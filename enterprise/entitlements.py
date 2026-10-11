from __future__ import annotations

import json
from datetime import timedelta

import jwt
from django.conf import settings
from django.utils import timezone

from enterprise.models import EntitlementCache, InstallationIdentity


def installation_id() -> str:
    row = InstallationIdentity.objects.first()
    if not row:
        row = InstallationIdentity.objects.create()
    return str(row.id)


def verify_entitlement_token(token: str) -> dict:
    keys = getattr(settings, "ENTERPRISE_PUBLIC_KEYS", [])
    if not keys:
        raise ValueError("No enterprise public keys configured")
    last_error = None
    for key_pem in keys:
        try:
            return jwt.decode(
                token,
                key_pem,
                algorithms=["EdDSA", "Ed25519"],
                audience=installation_id(),
                options={"require": ["exp", "aud", "iss"]},
            )
        except Exception as exc:
            last_error = exc
    raise ValueError(str(last_error))


def cache_entitlement(token: str) -> EntitlementCache:
    claims = verify_entitlement_token(token)
    exp = claims.get("exp")
    from datetime import datetime, timezone as dt_tz

    valid_until = datetime.fromtimestamp(exp, tz=dt_tz.utc) if exp else None
    grace = timezone.now() + timedelta(hours=getattr(settings, "ENTERPRISE_GRACE_HOURS", 72))
    row = EntitlementCache.objects.first() or EntitlementCache.objects.create()
    row.token = token
    row.verified_claims = claims
    row.valid_until = valid_until
    row.grace_until = grace
    row.last_refresh = timezone.now()
    row.last_error = ""
    row.save()
    return row


def licensed_capability(name: str) -> bool:
    row = EntitlementCache.objects.first()
    if not row or not row.verified_claims:
        return False
    if row.valid_until and row.valid_until < timezone.now():
        if not row.grace_until or row.grace_until < timezone.now():
            return False
    caps = row.verified_claims.get("capabilities") or []
    return name in caps
