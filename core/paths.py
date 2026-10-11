import os
import pwd
from pathlib import Path


def data_root() -> Path:
    return Path(os.environ.get("DATA_ROOT", "/data"))


def prepare_data_volume(run_as_user: str = "mailstead") -> None:
    """Ensure DATA_ROOT is writable (Railway/bind mounts are often root-owned).

    When PID 1 runs as root, chown the volume and drop to the app user before
    creating subdirectories or spawning workers.
    """
    if os.geteuid() != 0:
        return
    user = pwd.getpwnam(run_as_user)
    root = data_root()
    root.mkdir(parents=True, exist_ok=True)
    os.chown(root, user.pw_uid, user.pw_gid)
    for sub in ("db", "mail", "tmp"):
        path = root / sub
        path.mkdir(parents=True, exist_ok=True)
        os.chown(path, user.pw_uid, user.pw_gid)
    os.setgid(user.pw_gid)
    os.setuid(user.pw_uid)


def ensure_data_dirs() -> None:
    root = data_root()
    for sub in ("db", "mail", "tmp"):
        (root / sub).mkdir(parents=True, exist_ok=True)
