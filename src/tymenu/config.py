import os
from pathlib import Path
from dotenv import load_dotenv

# Place the DB in the current working directory
basedir = str(Path(".").resolve())

load_dotenv()  # take environment variables from .env.


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "unpiloted-flashcard-reuse-swoop"
    TYMENU_ADMIN = os.environ.get("TYMENU_ADMIN")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TYMENU_RECIPES_PER_PAGE = 10

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.googlemail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    TYMENU_MAIL_SUBJECT_PREFIX = "[TyMenu]"
    TYMENU_MAIL_SENDER = "TyMenu Admin <tymenuapp@gmail.com>"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URL") or "sqlite:///" + os.path.join(
        basedir, "data-dev.sqlite"
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL") or "sqlite://"


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///" + os.path.join(
        basedir, "data.sqlite"
    )


def get_config(config_name: str) -> Config:

    all_configs = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
        "default": DevelopmentConfig,
    }
    config_name = config_name.lower()
    if config_name not in all_configs:
        avail_configs = ", ".join(all_configs)
        raise ValueError(f"Unknown config {config_name}. Available configs: {avail_configs}")
    return all_configs[config_name]
