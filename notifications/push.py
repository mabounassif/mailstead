from __future__ import annotations

import json
import logging
from urllib.parse import urlparse

from django.conf import settings

logger = logging.getLogger(__name__)

ALLOWED_PUSH_HOST_SUFFIXES = (
    "push.apple.com",
    "push.services.mozilla.com",
    "updates.push.services.mozilla.com",
    "fcm.googleapis.com",
    "update.googleapis.com",
    "notify.windows.com",
    "wns.windows.com",
    "web.push.apple.com",
)


def load_vapid_private_key():
    """Parse VAPID private key from settings (PEM, DER base64url, or 32-byte raw)."""
    from py_vapid import Vapid, Vapid01

    raw = (getattr(settings, "VAPID_PRIVATE_KEY", "") or "").strip()
    if not raw:
        return None
    if "BEGIN" in raw:
        pem = raw.replace("\\n", "\n")
        try:
            return Vapid01.from_pem(pem.encode("utf-8"))
        except Exception as exc:
            logger.warning("Invalid VAPID_PRIVATE_KEY (PEM): %s", exc)
            return None
    try:
        return Vapid.from_string(raw)
    except Exception as exc:
        logger.warning("Invalid VAPID_PRIVATE_KEY: %s", exc)
        return None


def push_keys_present() -> bool:
    return bool(getattr(settings, "VAPID_PRIVATE_KEY", "") and getattr(settings, "VAPID_PUBLIC_KEY", ""))


def push_configured() -> bool:
    return push_keys_present() and load_vapid_private_key() is not None


def endpoint_allowed(endpoint: str) -> bool:
    try:
        parsed = urlparse(endpoint)
    except Exception:
        return False
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    if host in ("localhost", "127.0.0.1"):
        return False
    return any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_PUSH_HOST_SUFFIXES)


def vapid_claims() -> dict:
    sub = getattr(settings, "ADMIN_RECOVERY_EMAIL", "") or settings.DEFAULT_FROM_EMAIL
    if sub and not sub.startswith("mailto:"):
        sub = f"mailto:{sub}"
    return {"sub": sub}


def build_declarative_payload(*, title: str, body: str, navigate: str, badge: int | None = None) -> dict:
    notification: dict = {
        "title": title[:120],
        "body": body[:240],
        "navigate": navigate,
        "lang": "en-US",
        "dir": "ltr",
        "silent": False,
    }
    if badge is not None and badge > 0:
        notification["app_badge"] = str(min(badge, 99))
    return {"web_push": 8030, "notification": notification}


def send_push(subscription_info: dict, payload: dict) -> None:
    from pywebpush import WebPushException, webpush

    if not push_configured():
        raise RuntimeError("VAPID keys not configured")

    vapid_key = load_vapid_private_key()
    if vapid_key is None:
        raise RuntimeError("VAPID keys not configured")

    webpush(
        subscription_info,
        json.dumps(payload),
        vapid_private_key=vapid_key,
        vapid_claims=vapid_claims(),
        timeout=10,
    )


def send_push_safe(subscription_info: dict, payload: dict) -> tuple[bool, str | None, int | None]:
    """Returns (ok, error_code, http_status). error_code: revoked | error."""
    from pywebpush import WebPushException, webpush

    if not push_configured():
        return False, "not_configured", None
    vapid_key = load_vapid_private_key()
    if vapid_key is None:
        return False, "not_configured", None
    try:
        webpush(
            subscription_info,
            json.dumps(payload),
            vapid_private_key=vapid_key,
            vapid_claims=vapid_claims(),
            timeout=10,
        )
        return True, None, None
    except WebPushException as exc:
        status = getattr(exc, "response", None)
        code = status.status_code if status is not None else None
        if code in (404, 410):
            return False, "revoked", code
        logger.warning("Web push failed status=%s: %s", code, exc)
        return False, "error", code
    except Exception as exc:
        logger.warning("Web push failed: %s", exc)
        return False, "error", None
