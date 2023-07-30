from __future__ import annotations

from flask import current_app


def test_app(app):
    assert current_app is not None


def test_config(app):
    assert current_app.config["TESTING"]
