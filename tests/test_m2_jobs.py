import pytest
from django.utils import timezone

from jobs.models import Job
from jobs.queue import claim_next, complete_job, enqueue, fail_job, worker_owner


@pytest.mark.django_db
def test_job_dedupe():
    enqueue("noop", {}, dedupe_key="x:1")
    assert enqueue("noop", {}, dedupe_key="x:1") is None
    assert Job.objects.count() == 1


@pytest.mark.django_db
def test_job_claim_and_complete():
    job = enqueue("noop", {"a": 1})
    claimed = claim_next(worker_owner())
    assert claimed and claimed.id == job.id
    complete_job(claimed)
    assert Job.objects.get(pk=job.id).state == Job.State.DONE


@pytest.mark.django_db
def test_job_backoff_on_failure():
    job = enqueue("noop", {})
    claimed = claim_next(worker_owner())
    fail_job(claimed, "boom", retry=True)
    refreshed = Job.objects.get(pk=job.id)
    assert refreshed.state == Job.State.QUEUED
    assert refreshed.run_after > timezone.now()
