"""Prepare the data volume and database, then exec gunicorn.

PID 1 must not import Django. migrate, createcachetable, and prepare run in
short-lived processes that exit. os.execvpe replaces this interpreter so the
gunicorn master is the only process left, with one worker that also runs jobs.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _prepare_data_volume() -> None:
    from core.paths import prepare_data_volume

    prepare_data_volume()


def _ensure_data_dirs() -> None:
    from core.paths import ensure_data_dirs

    ensure_data_dirs()


def _manage(*args: str) -> None:
    subprocess.check_call([sys.executable, "manage.py", *args])


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    _prepare_data_volume()
    _ensure_data_dirs()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    _manage("migrate", "--noinput")
    _manage("createcachetable")
    _manage("prepare")

    if not os.environ.get("HOME") or os.environ.get("HOME") == "/root":
        os.environ["HOME"] = "/tmp"

    os.execvpe(
        sys.executable,
        [
            sys.executable,
            "-m",
            "gunicorn",
            "mailstead.wsgi:application",
            "--config",
            "mailstead/gunicorn.conf.py",
        ],
        os.environ.copy(),
    )


if __name__ == "__main__":
    main()
