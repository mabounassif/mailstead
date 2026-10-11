"""Supervisor: migrations, bootstrap, gunicorn + worker."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def _prepare_data_volume() -> None:
    from core.paths import prepare_data_volume

    prepare_data_volume()


def _ensure_data_dirs() -> None:
    from core.paths import ensure_data_dirs

    ensure_data_dirs()


def _django_setup() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")


def _run_migrations() -> None:
    subprocess.check_call([sys.executable, "manage.py", "migrate", "--noinput"])
    subprocess.check_call([sys.executable, "manage.py", "createcachetable"])


def _bootstrap() -> None:
    _django_setup()
    import django

    django.setup()
    from core.bootstrap import ensure_bootstrap_state
    from core.schedules import ensure_default_schedules

    ensure_bootstrap_state()
    ensure_default_schedules()


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    _prepare_data_volume()
    _ensure_data_dirs()
    _django_setup()
    _run_migrations()
    _bootstrap()

    bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
    gunicorn_cmd = [
        sys.executable,
        "-m",
        "gunicorn",
        "mailstead.wsgi:application",
        "--bind",
        bind,
        "--workers",
        "1",
        "--worker-class",
        "gthread",
        "--threads",
        "4",
        "--timeout",
        "60",
        "--graceful-timeout",
        "25",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
    ]
    worker_cmd = [sys.executable, "manage.py", "worker"]

    children: dict[str, subprocess.Popen] = {}
    children["gunicorn"] = subprocess.Popen(gunicorn_cmd)
    children["worker"] = subprocess.Popen(worker_cmd)

    shutting_down = False

    def forward_signal(signum, _frame):
        nonlocal shutting_down
        shutting_down = True
        for proc in children.values():
            if proc.poll() is None:
                proc.send_signal(signum)

    signal.signal(signal.SIGTERM, forward_signal)
    signal.signal(signal.SIGINT, forward_signal)

    deadline = None
    while True:
        for name, proc in children.items():
            rc = proc.poll()
            if rc is not None and not shutting_down:
                sys.exit(rc if rc is not None else 1)
        if shutting_down:
            if deadline is None:
                deadline = time.monotonic() + 25
            if all(p.poll() is not None for p in children.values()):
                sys.exit(0)
            if time.monotonic() > deadline:
                for proc in children.values():
                    if proc.poll() is None:
                        proc.kill()
                sys.exit(1)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
