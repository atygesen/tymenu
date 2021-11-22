from flask import current_app
import pytest
from tymenu import create_app
from tymenu.resources import get_db


@pytest.fixture
def app_context():
    """Build the test app"""
    test_app = create_app("testing")
    with test_app.app_context():
        yield test_app


@pytest.fixture
def app(app_context):
    """Create the tables in the app database"""
    db = get_db()
    db.create_all()
    yield
    db.session.remove()
    db.drop_all()


@pytest.fixture
def db(app):
    return get_db()


@pytest.fixture
def commit_to_db(db):
    """Commit some item(s) to the database"""

    def _commit_to_db(*items):
        db.session.add_all(items)
        db.session.commit()

    return _commit_to_db
