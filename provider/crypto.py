from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet() -> Fernet:
    key = settings.APP_ENCRYPTION_KEY.encode("utf-8")
    digest = hashlib.sha256(key).digest()
    fkey = base64.urlsafe_b64encode(digest)
    return Fernet(fkey)


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
