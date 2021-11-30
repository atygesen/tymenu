from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from .resources import get_db
from .models import User, Recipe


def users(count=100):
    db = get_db()
    fake = Faker()
    i = 0
    while i < count:
        u = User(
            email=fake.email(),
            username=fake.user_name(),
            password="password",
            member_since=fake.past_date(),
        )
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        else:
            i += 1


def recipes(count=100):
    db = get_db()
    fake = Faker()
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Recipe(
            title=fake.text(),
            ingredients=fake.text(),
            instructions=fake.text(),
            keywords=fake.text(),
            source=fake.text(),
            author=u,
        )
        db.session.add(p)
    db.session.commit()
