"""The main app constructor"""

from flask import Flask, url_for
import logging


from .config import get_config
from .resources import init_plugins


logger = logging.getLogger(__name__)


def create_app(config_name: str) -> Flask:
    app = Flask(__name__)

    config = get_config(config_name)

    app.config.from_object(config)
    config.init_app(app)

    init_plugins(app)

    # Blueprints
    from .main import main_blueprint
    from .auth import auth_blueprint
    from .menu import menu_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(menu_blueprint)

    # static path
    static = url_for("static", filename="styles.css")
    logger.info("Serving from static path: %s", static)

    return app
