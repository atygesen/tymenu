from pathlib import Path

with Path(__file__).with_name("_version.txt").open("r") as file:
    __version__ = file.readline().strip()
