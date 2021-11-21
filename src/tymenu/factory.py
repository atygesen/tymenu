"""The main app constructor"""

from flask import Flask

from .config import get_config
from .plugins import init_plugins


def create_app(config_name: str) -> Flask:
    app = Flask(__name__)

    config = get_config(config_name)

    app.config.from_object(config)
    config.init_app(app)

    init_plugins(app)

    # Blueprints
    from .main import main_blueprint
    from .auth import auth_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app
