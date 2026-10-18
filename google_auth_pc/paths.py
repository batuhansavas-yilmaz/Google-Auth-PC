import os
from pathlib import Path


def data_dir() -> Path:
    directory = Path(os.environ["APPDATA"]) / "GoogleAuthPC"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def accounts_file() -> Path:
    return data_dir() / "accounts.enc"


def config_file() -> Path:
    return data_dir() / "config.json"
