from __future__ import annotations

import logging
from typing import Any

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_datepicker import datepicker
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_pagedown import PageDown
from flask_sqlalchemy import SQLAlchemy

__all__ = ["get_db", "get_login_manager", "get_plugins", "init_plugins"]

logger = logging.getLogger(__name__)

_RESOURCES = {
    "bootstrap": Bootstrap(),
    "moment": Moment(),
    "db": SQLAlchemy(),
    "login_manager": LoginManager(),
    "pagedown": PageDown(),
    "mail": Mail(),
    "datepicker": datepicker(),
}
_RESOURCES["login_manager"].login_view = "auth.login"


def get_db() -> SQLAlchemy:
    return _RESOURCES["db"]


def get_login_manager() -> LoginManager:
    return _RESOURCES["login_manager"]


def get_mail() -> Mail:
    return _RESOURCES["mail"]


def get_plugins() -> dict[str, Any]:
    return _RESOURCES.copy()


def init_plugins(app: Flask) -> None:
    for plugin_name, plugin in _RESOURCES.items():
        logger.info("Initializing plugin %s.", plugin_name)
        plugin.init_app(app)
