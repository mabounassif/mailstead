from __future__ import annotations

import logging
import random
import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from jobs.models import Job

logger = logging.getLogger(__name__)

LEASE_SECONDS = 120


def enqueue(kind: str, payload: dict, dedupe_key: str | None = None, run_after=None) -> Job | None:
    run_after = run_after or timezone.now()
    try:
        with transaction.atomic():
            if dedupe_key:
                existing = Job.objects.filter(dedupe_key=dedupe_key).exclude(state=Job.State.DONE).first()
                if existing:
                    return None
            return Job.objects.create(
                kind=kind,
                payload=payload,
                dedupe_key=dedupe_key,
                run_after=run_after,
            )
    except Exception:
        if dedupe_key:
            return None
        raise


def reclaim_expired_leases() -> int:
    now = timezone.now()
    updated = Job.objects.filter(state=Job.State.RUNNING, lease_until__lt=now).update(
        state=Job.State.QUEUED,
        lease_owner="",
        lease_until=None,
    )
    return updated


def claim_next(owner: str) -> Job | None:
    reclaim_expired_leases()
    now = timezone.now()
    with transaction.atomic():
        job = (
            Job.objects.select_for_update(skip_locked=True)
            .filter(state=Job.State.QUEUED, run_after__lte=now)
            .order_by("run_after", "created_at")
            .first()
        )
        if not job:
            return None
        job.state = Job.State.RUNNING
        job.lease_owner = owner
        job.lease_until = now + timedelta(seconds=LEASE_SECONDS)
        job.attempts += 1
        job.save(update_fields=["state", "lease_owner", "lease_until", "attempts", "updated_at"])
        return job


def complete_job(job: Job) -> None:
    job.state = Job.State.DONE
    job.lease_owner = ""
    job.lease_until = None
    job.save(update_fields=["state", "lease_owner", "lease_until", "updated_at"])


def fail_job(job: Job, error: str, retry: bool = True) -> None:
    job.last_error_redacted = error[:2000]
    if not retry or job.attempts >= job.max_attempts:
        job.state = Job.State.DEAD
        job.lease_owner = ""
        job.lease_until = None
        job.save(update_fields=["state", "lease_owner", "lease_until", "last_error_redacted", "updated_at"])
        return
    delay = min(3600, (2 ** min(job.attempts, 10)) + random.uniform(0, 3))
    job.state = Job.State.QUEUED
    job.lease_owner = ""
    job.lease_until = None
    job.run_after = timezone.now() + timedelta(seconds=delay)
    job.save(
        update_fields=[
            "state",
            "lease_owner",
            "lease_until",
            "run_after",
            "last_error_redacted",
            "updated_at",
        ]
    )


def worker_owner() -> str:
    return f"worker-{uuid.uuid4().hex[:8]}"
