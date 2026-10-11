from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from storage.capacity import email_budget_bytes
from storage.models import MailboxStorage

PHYSICAL_SOURCE_LABELS = {
    "measured": "Measured from disk",
    "configured": "Configured capacity override",
    "unknown": "Could not read disk stats",
}


def physical_source_label(code: str) -> str:
    return PHYSICAL_SOURCE_LABELS.get(code, code.replace("_", " ").title())


def mailbox_usage_rows(limit: int = 50) -> list[dict]:
    rows: list[dict] = []
    for ms in MailboxStorage.objects.select_related("mailbox").order_by("-charged_bytes")[:limit]:
        quota = ms.mailbox.quota_bytes
        charged = ms.charged_bytes
        if quota > 0:
            percent = min(100.0, 100.0 * charged / quota)
        else:
            percent = 0.0
        rows.append(
            {
                "address": ms.mailbox.address,
                "charged_bytes": charged,
                "quota_bytes": quota,
                "percent": round(percent, 1),
                "state": ms.get_state_display(),
                "state_code": ms.state,
            }
        )
    return rows


def worker_health(heartbeat) -> dict:
    if heartbeat is None:
        return {
            "status": "missing",
            "label": "No heartbeat",
            "detail": "Background worker has not reported in yet.",
        }
    max_age = int(getattr(settings, "WORKER_HEARTBEAT_MAX_AGE_SECONDS", 120))
    age_seconds = (timezone.now() - heartbeat.updated_at).total_seconds()
    if age_seconds <= max_age:
        return {
            "status": "ok",
            "label": "Healthy",
            "detail": f"Last seen {int(age_seconds)}s ago (PID {heartbeat.pid}).",
            "updated_at": heartbeat.updated_at,
        }
    return {
        "status": "stale",
        "label": "Stale",
        "detail": f"Last seen {int(age_seconds)}s ago; expected within {max_age}s.",
        "updated_at": heartbeat.updated_at,
    }


def webhook_summary(settings_row) -> dict:
    if settings_row is None:
        return {
            "label": "Not configured",
            "detail": "No provider settings row yet.",
        }
    if settings_row.webhook_disabled:
        return {
            "label": "Disabled",
            "detail": "Inbound webhooks are turned off in provider settings.",
        }
    if settings_row.webhook_id:
        return {
            "label": "Registered",
            "detail": f"Webhook ID {settings_row.webhook_id[:8]}…",
        }
    return {
        "label": "Not registered",
        "detail": "Run webhook registration from the admin or a scheduled job.",
    }
