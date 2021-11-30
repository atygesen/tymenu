from typing import Iterator
from datetime import datetime
import hashlib
from flask import request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import sqlalchemy as sql

from .search import query_substrings, get_operation
from .resources import get_db, get_login_manager

db = get_db()
login_manager = get_login_manager()


class Recipe(db.Model):
    __tablename__ = "recipe"
    id: int = db.Column(db.Integer, primary_key=True)
    author_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    title: str = db.Column(db.String(64), unique=True)
    ingredients: str = db.Column(db.Text)
    instructions: str = db.Column(db.Text)
    keywords: str = db.Column(db.Text)
    source: str = db.Column(db.String(64))

    def __repr__(self) -> str:
        return f"<Recipe {self.title!r} by {self.author!r}>"

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

    def iter_ingredients(self, nmax=None) -> Iterator[str]:
        """Helper function to iterate the ingredients list.

        Can optionally provide a maximum number of ingredients.
        A final "..." is returned if the ingredients list is truncated."""
        counter = 0
        # Split ingredients on newlines
        for ingredient in self.ingredients.split():
            s = ingredient.strip()
            if s:
                counter += 1  # Only iterate if it's a non-empty line
                yield s
            if nmax is not None and counter == (nmax - 1):
                # Maximum count reached
                # Yield one more "..." and break out
                yield "..."
                break


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship("User", backref="role", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Role {self.name!r}>"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    password_hash = db.Column(db.String(128))
    recipes = db.relationship("Recipe", backref="author", lazy="dynamic")
    avatar_hash = db.Column(db.String(32))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

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
        print("Generating gravatar")
        return hashlib.md5(self.email.lower().encode("utf-8")).hexdigest()

    def gravatar(self, size=100, default="identicon", rating="g"):
        if request.is_secure:
            url = "https://secure.gravatar.com/avatar"
        else:
            url = "http://www.gravatar.com/avatar"
        hash = self.avatar_hash or self.gravatar_hash()
        return f"{url}/{hash}?s={size}&d={default}&r={rating}"


@login_manager.user_loader
def load_user(user_id: int) -> User:
    return User.query.get(int(user_id))
