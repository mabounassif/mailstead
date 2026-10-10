import os
from pathlib import Path


def data_root() -> Path:
    return Path(os.environ.get("DATA_ROOT", "/data"))


def ensure_data_dirs() -> None:
    root = data_root()
    for sub in ("db", "mail", "tmp"):
        (root / sub).mkdir(parents=True, exist_ok=True)
