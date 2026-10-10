from __future__ import annotations

import os
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.utils import timezone

from core.paths import data_root
from jobs.models import WorkerHeartbeat


def liveness() -> dict[str, str]:
    return {"status": "ok"}


def readiness() -> tuple[bool, dict[str, str]]:
    checks: dict[str, str] = {}
    ok = True

    try:
        connection.ensure_connection()
        checks["database"] = "ok"
    except Exception as exc:
        ok = False
        checks["database"] = f"error: {type(exc).__name__}"

    data = data_root()
    probe = data / "tmp" / ".ready_probe"
    try:
        data.mkdir(parents=True, exist_ok=True)
        (data / "tmp").mkdir(parents=True, exist_ok=True)
        probe.write_text("1")
        probe.unlink(missing_ok=True)
        checks["volume"] = "ok"
    except OSError as exc:
        ok = False
        checks["volume"] = f"error: {exc}"

    try:
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            ok = False
            checks["migrations"] = f"pending: {len(plan)}"
        else:
            checks["migrations"] = "ok"
    except Exception as exc:
        ok = False
        checks["migrations"] = f"error: {type(exc).__name__}"

    max_age = settings.WORKER_HEARTBEAT_MAX_AGE_SECONDS
    hb = WorkerHeartbeat.objects.order_by("-updated_at").first()
    if hb is None:
        # Allow fresh deploy before worker first tick in dev/tests
        if os.environ.get("SKIP_WORKER_HEARTBEAT_CHECK", "").lower() in ("1", "true"):
            checks["worker"] = "skipped"
        else:
            ok = False
            checks["worker"] = "no heartbeat"
    else:
        age = timezone.now() - hb.updated_at
        if age > timedelta(seconds=max_age):
            ok = False
            checks["worker"] = f"stale ({int(age.total_seconds())}s)"
        else:
            checks["worker"] = "ok"

    checks["status"] = "ok" if ok else "degraded"
    return ok, checks
