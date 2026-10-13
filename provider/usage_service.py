from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from provider.models import UsageAlert, UsageSnapshot
from provider.resend_client import ResendError, configure_rate_limit, get_usage
from provider.usage_parser import parse_usage


def refresh_usage() -> UsageSnapshot:
    try:
        raw = get_usage()
        parsed = parse_usage(raw)
        rate = parsed.get("rate_limit") or {}
        if isinstance(rate.get("limit"), int):
            duration = rate.get("duration", "1000ms")
            ms = int(str(duration).replace("ms", "")) if "ms" in str(duration) else 1000
            configure_rate_limit(int(rate["limit"]), ms)
        snap = UsageSnapshot.objects.create(raw_json=raw, parsed_json=parsed, ok=True)
        _maybe_alerts(parsed)
        return snap
    except ResendError as exc:
        last = UsageSnapshot.objects.filter(ok=True).order_by("-fetched_at").first()
        snap = UsageSnapshot.objects.create(
            raw_json={},
            parsed_json=last.parsed_json if last else {},
            ok=False,
            error_message=str(exc),
        )
        return snap


def _maybe_alerts(parsed: dict) -> None:
    thresholds = getattr(settings, "USAGE_ALERT_THRESHOLDS", [80, 90, 100])
    for period in ("daily", "monthly"):
        block = parsed.get(period) or {}
        resets = str(block.get("resets_at", "unknown"))
        used = block.get("used")
        limit = block.get("limit")
        if not isinstance(used, int) or not isinstance(limit, int):
            continue
        pct = (used / limit) * 100 if limit else 0
        for th in thresholds:
            if pct >= th:
                UsageAlert.objects.get_or_create(quota=period, period_key=resets, threshold=th)


def usage_period_rows(parsed: dict) -> list[dict]:
    rows: list[dict] = []
    for key, title in (("daily", "Daily"), ("monthly", "Monthly")):
        block = parsed.get(key) or {}
        rows.append(
            {
                "key": key,
                "title": title,
                "used": block.get("used"),
                "limit": block.get("limit"),
                "sent": block.get("sent"),
                "received": block.get("received"),
                "remaining": block.get("remaining"),
                "resets_at": block.get("resets_at"),
            }
        )
    return rows


def latest_usage_display() -> dict:
    snap = UsageSnapshot.objects.order_by("-fetched_at").first()
    if not snap:
        return {"status": "unknown", "periods": [], "rate_limit": None}
    age = timezone.now() - snap.fetched_at
    label = AdminSubscriptionLabel.objects.first()
    parsed = snap.parsed_json if snap.ok else {}
    rate = (parsed.get("rate_limit") or {}) if isinstance(parsed, dict) else {}
    return {
        "snapshot": snap,
        "age_seconds": int(age.total_seconds()),
        "stale": not snap.ok or age.total_seconds() > settings.USAGE_REFRESH_MINUTES * 60,
        "plan_label": label.label if label else None,
        "restricted_key": "restricted" in (snap.error_message or "").lower(),
        "periods": usage_period_rows(parsed) if isinstance(parsed, dict) else [],
        "rate_limit": rate,
    }


from provider.models import AdminSubscriptionLabel  # noqa: E402
