from __future__ import annotations

import pytest
from tymenu.models import Role, User


@pytest.fixture
def john(commit_to_db):
    u = User(email="john@example.com", username="john", password="cat")
    commit_to_db(u)
    return u


@pytest.fixture
def alice(commit_to_db):
    u = User(email="alice@example.com", username="alice", password="dog")
    commit_to_db(u)
    assert u.role_id is None
    return u


@pytest.fixture
def admin_role(commit_to_db):
    r = Role(name="admin")
    commit_to_db(r)
    return r


@pytest.fixture
def user_role(commit_to_db):
    r = Role(name="user")
    commit_to_db(r)
    return r
