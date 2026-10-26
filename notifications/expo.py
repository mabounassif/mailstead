from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request

from django.conf import settings
from django.utils import timezone

from notifications.models import NativePushDevice

_EXPO_TOKEN = re.compile(r"^(ExponentPushToken|ExpoPushToken)\[[A-Za-z0-9_\-]+\]$")
_EXPO_URL = "https://exp.host/--/api/v2/push/send"


def expo_push_configured() -> bool:
    return bool((getattr(settings, "EXPO_ACCESS_TOKEN", "") or "").strip())


def register_expo_token(user, token: str, label: str = "") -> NativePushDevice:
    if not _EXPO_TOKEN.match(token or ""):
        raise ValueError("Enter the Expo push token from this device.")
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    device, _created = NativePushDevice.objects.update_or_create(
        token_hash=digest,
        defaults={
            "user": user,
            "token": token,
            "label": (label or "Mailstead app")[:64],
            "revoked_at": None,
            "last_error": "",
        },
    )
    return device


def send_expo_message(token: str, *, title: str, body: str, data: dict) -> tuple[bool, str | None]:
    """Returns (ok, error_code). error_code is revoked or error. Does not log the token."""
    if not expo_push_configured():
        return False, "not_configured"
    payload = json.dumps(
        {
            "to": token,
            "title": title[:120],
            "body": body[:240],
            "data": data,
            "sound": "default",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        _EXPO_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.EXPO_ACCESS_TOKEN}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        exc.read()
        return False, "error"
    except Exception:
        return False, "error"
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, "error"
    ticket = parsed.get("data")
    item = ticket[0] if isinstance(ticket, list) and ticket else parsed
    if not isinstance(item, dict):
        return False, "error"
    if item.get("status") == "ok":
        return True, None
    details = item.get("details")
    if isinstance(details, dict) and details.get("error") == "DeviceNotRegistered":
        return False, "revoked"
    return False, "error"


def deliver_expo(user, payload: dict) -> int:
    if not expo_push_configured():
        return 0
    note = payload.get("notification") or {}
    title = note.get("title") or "Mailstead"
    body = note.get("body") or ""
    data = {"navigate": note.get("navigate") or ""}
    sent = 0
    for device in NativePushDevice.objects.filter(user=user, revoked_at__isnull=True):
        ok, err = send_expo_message(device.token, title=title, body=body, data=data)
        if ok:
            device.last_success_at = timezone.now()
            device.last_error = ""
            device.save(update_fields=["last_success_at", "last_error"])
            sent += 1
        elif err == "revoked":
            device.revoked_at = timezone.now()
            device.last_error = "revoked"
            device.save(update_fields=["revoked_at", "last_error"])
        else:
            device.last_error = err or "error"
            device.save(update_fields=["last_error"])
    return sent
