from jobs.models import Schedule


def ensure_default_schedules() -> None:
    defaults = [
        ("reconcile_received", "reconcile_received", 15 * 60, {}),
        ("register_webhook", "register_webhook", 6 * 60 * 60, {}),
        ("storage_sweep", "storage_sweep", 60 * 60, {}),
        ("usage_refresh", "usage_refresh", 30 * 60, {}),
    ]
    for name, kind, interval, payload in defaults:
        Schedule.objects.get_or_create(
            name=name,
            defaults={"kind": kind, "interval_seconds": interval, "payload": payload, "enabled": True},
        )
