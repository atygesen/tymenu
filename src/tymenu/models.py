from __future__ import annotations

import datetime
import enum
import hashlib

from flask import current_app, request
from flask_login import AnonymousUserMixin, UserMixin, current_user
from flask_sqlalchemy.model import DefaultMeta
import jwt
import sqlalchemy as sql
from sqlalchemy.orm import Mapped, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from tymenu.timestamp import get_now_utc
from tymenu.utils import clean_markdown_to_html

from .resources import get_db, get_login_manager
from .search import get_operation, query_substrings


@enum.unique
class KcalType(enum.IntEnum):
    PER_PERSON = 1
    TOTAL = 2


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


db = get_db()
login_manager = get_login_manager()


def _get_secret_key() -> str:
    return current_app.config["SECRET_KEY"]


def encode(data: dict, expiration=3600):
    # expiration is a special name
    # https://pyjwt.readthedocs.io/en/latest/usage.html#registered-claim-names
    data["exp"] = get_now_utc() + datetime.timedelta(seconds=expiration)
    return jwt.encode(data, _get_secret_key(), algorithm="HS256")


def decode(token, leeway: int = 10):
    return jwt.decode(
        token,
        _get_secret_key(),
        leeway=datetime.timedelta(seconds=leeway),
        algorithms=["HS256"],
    )


# Energy conversion (kcal/g)
energy_conversion = {
    "fat": 8.80,
    "protein": 4.06,
    "carb": 4.06,
}

BaseModel: DefaultMeta = db.Model


class Recipe(BaseModel):
    __tablename__ = "recipe"
    id: int = db.Column(db.Integer, primary_key=True)
    author_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    timestamp: datetime.datetime = db.Column(db.DateTime, index=True, default=get_now_utc)
    last_updated = db.Column(db.DateTime)
    title: str = db.Column(db.String(64), unique=True)
    ingredients: str = db.Column(db.Text)
    instructions: str = db.Column(db.Text)
    background: str = db.Column(db.Text, nullable=True)
    keywords: str = db.Column(db.Text)
    source: str = db.Column(db.Text)
    servings: int = db.Column(db.Integer)
    kcal: float | None = db.Column(db.Float, nullable=True)
    kcal_type: int = db.Column(db.Integer)  # are kcal measured in per person or in total
    # Breakdown of the kcals
    protein_gram: float | None = db.Column(db.Float, nullable=True)
    carb_gram: float | None = db.Column(db.Float, nullable=True)
    fat_gram: float | None = db.Column(db.Float, nullable=True)
    cooking_time_min: float | None = db.Column(db.Float, nullable=True)

    # Special columns with sanitized HTML from Markdown
    ingredients_html: str = db.Column(db.Text)
    instructions_html: str = db.Column(db.Text)
    background_html: str = db.Column(db.Text)

    # img_url to BBimg
    img_display_url: str = db.Column(db.Text, nullable=True)
    img_delete_url: str = db.Column(db.Text, nullable=True)
    img_thumbnail_url: str = db.Column(db.Text, nullable=True)
    img_url_viewer: str = db.Column(db.Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Recipe {self.title!r} by {self.author!r}>"

    @property
    def kcal_pers(self) -> float | None:
        if self.kcal is None:
            return None
        if self.kcal_type == KcalType.PER_PERSON:
            return self.kcal
        # kcal are measured in totals
        if self.servings is None:
            return None
        return self.kcal / self.servings

    def _energy_string(self, val_g, energy_name, prefix: str):
        if val_g is None:
            return ""
        energy_kcal = energy_conversion[energy_name] * val_g
        val_g = round(val_g, 1)
        r = round(val_g)
        if abs(val_g - r) < 0.01:
            # If number is rounded off to integer, display it as an integer
            val_s = f"{r:d}"
        else:
            # Otherwise display with a decimal.
            val_s = f"{val_g:.1f}"

        return f"{prefix}: {val_s} g ({energy_kcal:.2f} kcal)"

    def protein_string(self):
        return self._energy_string(self.protein_gram, "protein", "Protein")

    def carb_string(self):
        return self._energy_string(self.carb_gram, "carb", "Carbs")

    def fat_string(self):
        return self._energy_string(self.fat_gram, "fat", "Fat")

    def cooking_time_hh_mm_ss(self):
        delta = datetime.timedelta(minutes=self.cooking_time_min)
        return _timedelta_to_hh_mm(delta)

    @property
    def kcal_total(self) -> float | None:
        if self.kcal is None:
            return None
        if self.kcal_type == KcalType.TOTAL:
            return self.kcal
        if self.servings is None:
            return None
        return self.kcal * self.servings

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


class Role(BaseModel):
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
    def all_role_permissions() -> dict[str, list[Permission]]:
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


class User(UserMixin, BaseModel):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    password_hash = db.Column(db.String(128))
    recipes = db.relationship("Recipe", backref="author", lazy="dynamic")
    avatar_hash = db.Column(db.String(32))
    member_since = db.Column(db.DateTime(), default=get_now_utc)
    # menu_plans = db.relationship("MenuPlanItem", backref="author", lazy="dynamic")

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

    @property
    def is_current_user(self) -> bool:
        """Is this user is the current logged in user?"""
        return self.id == current_user.id


@login_manager.user_loader
def load_user(user_id: int) -> User:
    return User.query.get(int(user_id))


def _timedelta_to_hh_mm(delta: datetime.timedelta):
    sec = delta.seconds
    hours = sec // 3600
    min_ = (sec // 60) - (hours * 60)
    # Construct the "minute" string.
    min_s = f"{min_:d} minute"
    if min_ != 1:
        # plural
        min_s += "s"
    # Hours?
    if hours == 0:
        # No hours, only minutes
        return min_s
    if hours == 1:
        # Singular hour
        return f"1 hour, {min_s}"
    # Multuple hours
    return f"{hours} hours, {min_s}"


class MenuPlanInstance(BaseModel):
    __tablename__ = "menu_plan_instance"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, index=True)
    menu_plan_id = db.Column(db.Integer, db.ForeignKey("menu_plan.id"), index=True)
    # menu_plan: Mapped[MenuPlan] = relationship(foreign_keys=[menu_plan_id])

    @property
    def recipe_plans(self) -> list[MenuPlanItem]:
        return self.menu_plan.get_sorted_plans()

    @property
    def title(self) -> str:
        return self.menu_plan.title


class MenuPlan(BaseModel):
    __tablename__ = "menu_plan"
    id = db.Column(db.Integer, primary_key=True)
    title: str = db.Column(db.String(255), nullable=False, index=False)
    description: str = db.Column(db.Text, nullable=True, index=False)
    added_by_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    added_by: Mapped[User] = relationship("User")
    timestamp: datetime.datetime = db.Column(db.DateTime, index=False, default=get_now_utc)
    recipe_plans: Mapped[list[MenuPlanItem]] = relationship(
        "MenuPlanItem",
        cascade="all,delete",
        backref="menu_plan",
    )
    instances: Mapped[list[MenuPlanInstance]] = relationship(
        "MenuPlanInstance",
        cascade="all,delete",
        backref="menu_plan",
    )

    description_html: str = db.Column(db.Text)

    @classmethod
    def get_date(cls, date: datetime.date):
        return cls.query.filter(cls.date == date).all()

    def get_sorted_plans(self) -> list[MenuPlanItem]:
        plans = self.recipe_plans.copy()
        plans.sort(key=lambda p: p.day)
        return plans

    @staticmethod
    def on_changed_description(target, value, oldvalue, initiator):
        if value is None:
            target.description_html = ""
        target.description_html = clean_markdown_to_html(value)


db.event.listen(MenuPlan.description, "set", MenuPlan.on_changed_description)


class MenuPlanItem(BaseModel):
    """Join table for MenuPlan and Recipe"""

    __tablename__ = "menu_plan_recipe"
    id: int = db.Column(db.Integer, primary_key=True)
    menu_plan_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("menu_plan.id"), index=True)
    recipe_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("recipe.id"), index=True)
    day: int = db.Column(db.Integer, nullable=False)  # Number of days offset from day 0
    days_leftover = db.Column(db.Integer, nullable=False)
    recipe: Mapped[Recipe] = relationship(foreign_keys=[recipe_id])
