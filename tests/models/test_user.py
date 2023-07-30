from __future__ import annotations

import pytest
from tymenu.models import User


def test_user(john, alice):
    assert john.id is not None
    assert isinstance(john.id, int)
    assert isinstance(alice.id, int)
    assert john.id == 1
    assert alice.id == 2
    result = User.query.filter_by(email=john.email).all()
    assert len(result) == 1
    result = User.query.filter_by(email=john.email).first()
    assert result == john
    assert result is john
    assert john != alice

    result = User.query.filter_by(username="alice").first()
    assert result == alice


def test_password_access(john):
    with pytest.raises(AttributeError):
        john.password


def test_password_cmp(john, alice):
    assert john.verify_password("cat")
    assert not john.verify_password("dog")
    assert alice.verify_password("dog")
    assert not alice.verify_password("Dog")


def test_add_role(john, alice, admin_role, user_role):
    assert len(admin_role.users.all()) == 0
    john.role = admin_role
    alice.role = user_role
    result = admin_role.users.all()
    assert len(result) == 1
    assert john in result
    assert alice not in result
    assert alice in user_role.users.all()
