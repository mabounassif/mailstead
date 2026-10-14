from __future__ import annotations

import logging
import os
import threading
from concurrent.futures import Future, ThreadPoolExecutor

from django.db import close_old_connections
from django.utils import timezone

from jobs.models import Job, Schedule, WorkerHeartbeat
from jobs.queue import claim_next, complete_job, fail_job, enqueue, worker_owner

logger = logging.getLogger(__name__)

HANDLERS: dict[str, object] = {}

# One in-flight job. A second pool thread is unused RAM on an idle mailbox.
JOB_POOL_WORKERS = 1

_shutdown = threading.Event()


def request_worker_shutdown() -> None:
    _shutdown.set()


def register(kind: str):
    def decorator(handler):
        HANDLERS[kind] = handler
        return handler

    return decorator


def register_job_handlers() -> None:
    import mail.jobs  # noqa: F401
    import notifications.jobs  # noqa: F401
    import provider.jobs  # noqa: F401
    import storage.jobs  # noqa: F401


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
    close_old_connections()
    try:
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
    finally:
        close_old_connections()


def run_worker_loop(shutdown: threading.Event | None = None) -> None:
    """Poll the job queue until shutdown is set.

    Pass an event from `manage.py worker`. Gunicorn uses the module event so
    signal hooks can stop the loop without a second Django process.
    """
    stop = shutdown if shutdown is not None else _shutdown
    register_job_handlers()
    pid = os.getpid()
    owner = worker_owner()
    logger.info("Worker started pid=%s owner=%s", pid, owner)
    inflight: Future | None = None
    pool = ThreadPoolExecutor(max_workers=JOB_POOL_WORKERS)
    try:
        while not stop.is_set():
            close_old_connections()
            WorkerHeartbeat.objects.update_or_create(pk=1, defaults={"pid": pid})
            _tick_schedules()
            if inflight is not None and inflight.done():
                inflight = None
            if inflight is None and not stop.is_set():
                job = claim_next(owner)
                if job is not None:
                    inflight = pool.submit(_run_job, job)
            stop.wait(1)
        if inflight is not None and not inflight.done():
            try:
                inflight.result(timeout=20)
            except Exception:
                logger.exception("In-flight job did not finish during shutdown")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
        close_old_connections()
    logger.info("Worker shutting down")
