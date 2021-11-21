import os
from pathlib import Path

# Place the DB in the current working directory
basedir = str(Path(".").resolve())


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "hard to guess string"
    TYMENU_ADMIN = os.environ.get("TYMENU_ADMIN")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
