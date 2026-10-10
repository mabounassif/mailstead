from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.utils import timezone

from jobs.models import Job, Schedule, WorkerHeartbeat
from jobs.queue import claim_next, complete_job, fail_job, enqueue, worker_owner

logger = logging.getLogger(__name__)

HANDLERS: dict[str, object] = {}


def register(kind: str):
    def decorator(handler):
        HANDLERS[kind] = handler
        return handler

    return decorator


def _tick_schedules() -> None:
    now = timezone.now()
    for sched in Schedule.objects.filter(enabled=True):
        if sched.last_enqueued_at and (now - sched.last_enqueued_at).total_seconds() < sched.interval_seconds:
            continue
        bucket = int(now.timestamp() // sched.interval_seconds)
        dedupe = f"schedule:{sched.name}:{bucket}"
        if enqueue(sched.kind, sched.payload, dedupe_key=dedupe):
            sched.last_enqueued_at = now
            sched.save(update_fields=["last_enqueued_at"])


def _run_job(job: Job) -> None:
    handler = HANDLERS.get(job.kind)
    if not handler:
        fail_job(job, f"unknown kind {job.kind}", retry=False)
        return
    try:
        handler(job)
        complete_job(job)
    except Exception as exc:
        logger.exception("Job %s failed", job.id)
        fail_job(job, str(exc))


