from pathlib import Path
from flask_mail import Mail

from .factory import create_app

with Path(__file__).with_name("_version.txt").open("r") as file:
    __version__ = file.readline().strip()


__all__ = ["__version__", "create_app"]
