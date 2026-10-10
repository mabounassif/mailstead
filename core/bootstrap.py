from __future__ import annotations

import hashlib
import logging
import os
import secrets
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction

from accounts.models import BootstrapState

logger = logging.getLogger(__name__)

TOKEN_FILE = "bootstrap-token"


def _token_path() -> Path:
    return settings.DATA_ROOT / TOKEN_FILE


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def resolve_bootstrap_token() -> str | None:
    if settings.BOOTSTRAP_TOKEN:
        return settings.BOOTSTRAP_TOKEN
    path = _token_path()
    if path.is_file():
        return path.read_text().strip()
    return None


def ensure_bootstrap_state() -> BootstrapState | None:
    """Create BootstrapState on first run if no superuser exists."""
    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return BootstrapState.objects.first()

    state = BootstrapState.objects.first()
    if state:
        return state

    token = resolve_bootstrap_token()
    if not token:
        token = secrets.token_urlsafe(32)
        path = _token_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(token + "\n")
        os.chmod(path, 0o600)

    with transaction.atomic():
        return BootstrapState.objects.create(token_hash=_hash_token(token))


def verify_setup_token(provided: str) -> bool:
    state = BootstrapState.objects.first()
    if not state or state.consumed_at:
        return False
    return state.token_hash == _hash_token(provided)


def consume_bootstrap(username: str, password: str) -> None:
    User = get_user_model()
    with transaction.atomic():
        state = BootstrapState.objects.select_for_update().get()
        if state.consumed_at:
            raise ValueError("Bootstrap already consumed")
        user = User.objects.create_superuser(username=username, password=password)
        recovery = settings.ADMIN_RECOVERY_EMAIL
        if recovery:
            user.recovery_email = recovery
            user.save(update_fields=["recovery_email"])
        from django.utils import timezone

        state.consumed_at = timezone.now()
        state.consumed_by = user
        state.save(update_fields=["consumed_at", "consumed_by"])
