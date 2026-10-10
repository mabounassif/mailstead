from __future__ import annotations

from typing import Any


def _num(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_usage(raw: dict) -> dict:
    emails = raw.get("emails") or {}
    daily = emails.get("daily") or {}
    monthly = emails.get("monthly") or {}
    rate = raw.get("rate_limit") or {}

    def period(block: dict) -> dict:
        used = _num(block.get("used"))
        limit = block.get("limit")
        limit_int = _num(limit) if limit is not None else None
        remaining = None
        if used is not None and limit_int is not None:
            remaining = max(0, limit_int - used)
        elif limit is None and limit_int is None and "limit" in block:
            limit_label = "uncapped (per Resend docs)"
        else:
            limit_label = "unknown" if limit is None else str(limit)
        if limit is None and "limit" in block:
            limit_display = "uncapped (per Resend docs)"
        elif limit_int is not None:
            limit_display = limit_int
        else:
            limit_display = "unknown"
        return {
            "used": used if used is not None else "unknown",
            "limit": limit_display,
            "sent": _num(block.get("sent")) if block.get("sent") is not None else "unknown",
            "received": _num(block.get("received")) if block.get("received") is not None else "unknown",
            "remaining": remaining if remaining is not None else "unknown",
            "resets_at": block.get("resets_at") or "unknown",
        }

    return {
        "daily": period(daily),
        "monthly": period(monthly),
        "rate_limit": {
            "limit": rate.get("limit", "unknown"),
            "duration": rate.get("duration", "unknown"),
        },
        "secondary": {
            "contacts": raw.get("contacts"),
            "segments": raw.get("segments"),
            "broadcasts": raw.get("broadcasts"),
            "domains": raw.get("domains"),
            "ai_credits": raw.get("ai_credits"),
            "automation_runs": raw.get("automation_runs"),
        },
    }
