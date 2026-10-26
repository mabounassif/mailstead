from __future__ import annotations

import hashlib
import secrets

from django.http import HttpRequest
from django.utils import timezone

from api.models import ApiToken


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_token(user, label: str = "") -> str:
    raw = secrets.token_urlsafe(32)
    ApiToken.objects.create(user=user, token_hash=hash_token(raw), label=(label or "")[:64])
    return raw


def revoke_token(raw: str) -> bool:
    updated = ApiToken.objects.filter(token_hash=hash_token(raw), revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    return updated > 0


def revoke_api_tokens(user) -> int:
    return ApiToken.objects.filter(user=user, revoked_at__isnull=True).update(revoked_at=timezone.now())


def user_from_bearer(request: HttpRequest):
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Bearer "):
        return None
    raw = header[7:].strip()
    if not raw:
        return None
    token = (
        ApiToken.objects.select_related("user")
        .filter(token_hash=hash_token(raw), revoked_at__isnull=True)
        .first()
    )
    if token is None:
        return None
    token.last_used_at = timezone.now()
    token.save(update_fields=["last_used_at"])
    return token.user
