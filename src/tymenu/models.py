from __future__ import annotations
from typing import List, Dict, Optional
import datetime
import hashlib
import jwt
from flask import request, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
import sqlalchemy as sql
from markdown import markdown
import bleach
import emoji

from .search import query_substrings, get_operation
from .resources import get_db, get_login_manager


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


db = get_db()
login_manager = get_login_manager()


def get_secret_key() -> str:
    return current_app.config["SECRET_KEY"]


def encode(data: dict, expiration=3600):
    # expiration is a special name
    # https://pyjwt.readthedocs.io/en/latest/usage.html#registered-claim-names
    data["exp"] = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        seconds=expiration
    )
    return jwt.encode(data, get_secret_key(), algorithm="HS256")


def decode(token, leeway: int = 10):
    return jwt.decode(
        token,
        get_secret_key(),
        leeway=datetime.timedelta(seconds=leeway),
        algorithms=["HS256"],
    )


def emojify_str(s: str) -> str:
    return emoji.emojize(s, language="alias", variant="emoji_type")


def clean_markdown_to_html(value: str, emojify=True) -> str:
    allowed_tags = [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "code",
        "em",
        "i",
        "li",
        "ol",
        "pre",
        "strong",
        "ul",
        "h1",
        "h2",
        "h3",
        "p",
    ]
    cleaned = bleach.linkify(
        bleach.clean(
            markdown(value, output_format="html"),
            tags=allowed_tags,
            strip=True,
        )
    )
    if emojify:
        cleaned = emojify_str(cleaned)
    return cleaned


class Recipe(db.Model):
    __tablename__ = "recipe"
    id: int = db.Column(db.Integer, primary_key=True)
    author_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow)
    last_updated = db.Column(db.DateTime)
    title: str = db.Column(db.String(64), unique=True)
    ingredients: str = db.Column(db.Text)
    instructions: str = db.Column(db.Text)
    background: str = db.Column(db.Text, nullable=True)
    keywords: str = db.Column(db.Text)
    source: str = db.Column(db.String(64))
    servings: int = db.Column(db.Integer)
    kcal: float = db.Column(db.Float, nullable=True)
    # Special columns with sanitized HTML from Markdown
    ingredients_html: str = db.Column(db.Text)
    instructions_html: str = db.Column(db.Text)
    background_html: str = db.Column(db.Text)

    # img_url to BBimg
    img_display_url: str = db.Column(db.Text, nullable=True)
    img_delete_url: str = db.Column(db.Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Recipe {self.title!r} by {self.author!r}>"

    @property
    def kcal_pers(self) -> Optional[float]:
        if self.kcal is None or self.servings is None:
            return None
        return self.kcal / self.servings

    @classmethod
    def search_string(cls, string: str):
        """Search in relevant fields for a string"""

        contains = (
            getattr(cls, name).contains(string)
            for name in ("title", "ingredients", "keywords", "instructions")
        )

        return cls.query.filter(sql.or_(*contains))

    @classmethod
    def search_ingredients(cls, *ingredients, operation="and", exclude: bool = False):
        """Query for one or more ingredients from the ingredients column.
        Default behaviour is to require all ingreduents."""
        queries = query_substrings(cls.ingredients, *ingredients, exclude=exclude)
        op = get_operation(operation)
        return cls.query.filter(op(*queries))

    @classmethod
    def search_keywords(cls, *keywords: str, operation="and", exclude: bool = False):
        queries = query_substrings(cls.keywords, *keywords, exclude=exclude)
        op = get_operation(operation)
        return cls.query.filter(op(*queries))

    @classmethod
    def build_query(cls, title=None, ingredients=None, keywords=None, order_by_time=True):
        query = cls.query
        if title:
            query = query.filter(sql.and_(*query_substrings(cls.title, title)))
        if ingredients:
            query = query.filter(sql.and_(*query_substrings(cls.ingredients, *ingredients)))
        if keywords:
            query = query.filter(sql.and_(*query_substrings(cls.keywords, *keywords)))
        if order_by_time:
            query = query.order_by(cls.timestamp.desc())
        return query

    def short_ingredients_list(self, nmax=5):
        ingr = []
        for ii, line in enumerate(self.ingredients.split("\n")):
            if ii == nmax:
                ingr.append("\n...")
                break
            ingr.append(line)
        return clean_markdown_to_html("\n".join(ingr))

    @staticmethod
    def on_changed_instructions(target, value, oldvalue, initiator):
        target.instructions_html = clean_markdown_to_html(value)

    @staticmethod
    def on_changed_ingredients(target, value, oldvalue, initiator):
        target.ingredients_html = clean_markdown_to_html(value)

    @staticmethod
    def on_changed_background(target, value, oldvalue, initiator):
        if value is None:
            target.background_html = ""
        target.background_html = clean_markdown_to_html(value)


# Listen to set the markdown -> HTML conversion
db.event.listen(Recipe.ingredients, "set", Recipe.on_changed_ingredients)
db.event.listen(Recipe.instructions, "set", Recipe.on_changed_instructions)
db.event.listen(Recipe.background, "set", Recipe.on_changed_background)


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship("User", backref="role", lazy="dynamic")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def all_role_permissions() -> Dict[str, List[Permission]]:
        return {
            "User": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            "Moderator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
            ],
            "Administrator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE,
                Permission.MODERATE,
                Permission.ADMIN,
            ],
        }

    @classmethod
    def all_roles(cls):
        return cls.query.all()

    @staticmethod
    def insert_roles():
        default_role = "User"
        roles = Role.all_role_permissions()
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = role.name == default_role
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self) -> str:
        return f"<Role {self.name!r}>"

    def __str__(self) -> str:
        return self.name


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def is_mod(self):
        return False


login_manager.anonymous_user = AnonymousUser


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    password_hash = db.Column(db.String(128))
    recipes = db.relationship("Recipe", backref="author", lazy="dynamic")
    avatar_hash = db.Column(db.String(32))
    member_since = db.Column(db.DateTime(), default=datetime.datetime.utcnow)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

        if self.role is None:
            if self.email == current_app.config["TYMENU_ADMIN"]:
                self.role = Role.query.filter_by(name="Administrator").first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode("utf-8")).hexdigest()

    def gravatar(self, size=100, default="identicon", rating="g"):
        if request.is_secure:
            url = "https://secure.gravatar.com/avatar"
        else:
            url = "http://www.gravatar.com/avatar"
        hash = self.avatar_hash or self.gravatar_hash()
        return f"{url}/{hash}?s={size}&d={default}&r={rating}"

    def generate_confirmation_token(self, expiration=3600):
        return encode({"confirm": self.id}, expiration=expiration)

    def generate_reset_token(self, expiration=3600):
        return encode({"reset": self.id}, expiration=expiration)

    def confirm(self, token):
        try:
            data = decode(token)
        except Exception:
            return False
        if data.get("confirm") != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    @staticmethod
    def reset_password(token, new_password) -> bool:
        """Reset the password. Returns a boolean indicating if
        the password has been changed."""
        try:
            data = decode(token)
        except Exception:
            return False
        user = User.query.get(data.get("reset"))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def can(self, perm) -> bool:
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self) -> bool:
        return self.can(Permission.ADMIN)

    def is_mod(self):
        return self.can(Permission.MODERATE)

    def set_role(self, role_name: str) -> None:
        """Change the role of a user using a string.
        Example:

        >>> usr = User.query.filter_by(id=1).first()  # Select a user
        >>> usr.set_role("administrator")
        >>> usr.set_role("user")

        """
        all_roles = Role.all_roles()
        # Always compare lower, for convenience.
        role_name = role_name.lower()
        for role in all_roles:
            # Find a role corresponding to the requested role name.
            if role.name.lower() == role_name:
                self.role = role
                db.session.commit()
                return
        raise RuntimeError(f"Unknown role: {role_name}. Available roles: {all_roles!r}")


@login_manager.user_loader
def load_user(user_id: int) -> User:
    return User.query.get(int(user_id))
