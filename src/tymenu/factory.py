"""The main app constructor"""
from __future__ import annotations

import logging

from flask import Flask

from .config import get_config
from .resources import init_plugins

logger = logging.getLogger(__name__)


def create_app(config_name: str) -> Flask:
    logger.info("Creating app")
    app = Flask(__name__)

    config = get_config(config_name)

    app.config.from_object(config)
    config.init_app(app)

    init_plugins(app)

    # Blueprints
    from .auth import auth_blueprint
    from .main import main_blueprint
    from .menu import menu_blueprint
    from .plan import plan_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(menu_blueprint)
    app.register_blueprint(plan_blueprint)

    return app
