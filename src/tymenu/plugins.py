from typing import Dict, Any
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

__all__ = ["get_db", "get_login_manager", "get_plugins", "init_plugins"]

_PLUGINS = {
    "bootstrap": Bootstrap(),
    "moment": Moment(),
    "db": SQLAlchemy(),
    "login_manager": LoginManager(),
}
_PLUGINS["login_manager"].login_view = "auth.login"


def get_db() -> SQLAlchemy:
    return _PLUGINS["db"]


def get_login_manager() -> LoginManager:
    return _PLUGINS["login_manager"]


def get_plugins() -> Dict[str, Any]:
    return _PLUGINS.copy()


def init_plugins(app: Flask) -> None:
    for plugin in _PLUGINS.values():
        plugin.init_app(app)
