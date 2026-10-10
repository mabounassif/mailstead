from __future__ import annotations

import hashlib
import os
from pathlib import Path

from core.paths import data_root
from mail.models import Blob


def blob_path(sha256: str) -> Path:
    return data_root() / "mail" / "blobs" / sha256[:2] / sha256[2:4] / sha256


def write_blob(data: bytes) -> Blob:
    sha = hashlib.sha256(data).hexdigest()
    dest = blob_path(sha)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = data_root() / "tmp" / f"blob-{sha}.part"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, dest)
    blob, _ = Blob.objects.get_or_create(
        sha256=sha,
        defaults={"size_bytes": len(data), "path": str(dest)},
    )
    return blob
