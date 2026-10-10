from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone


class WorkerHeartbeat(models.Model):
    pid = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = "updated_at"


class Job(models.Model):
    class State(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        DEAD = "dead", "Dead"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=64, db_index=True)
    dedupe_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    payload = models.JSONField(default=dict)
    state = models.CharField(max_length=16, choices=State.choices, default=State.QUEUED, db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=8)
    run_after = models.DateTimeField(default=timezone.now, db_index=True)
    lease_owner = models.CharField(max_length=64, blank=True, default="")
    lease_until = models.DateTimeField(null=True, blank=True, db_index=True)
    last_error_redacted = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["state", "run_after"]),
        ]


class Schedule(models.Model):
    name = models.CharField(max_length=64, unique=True)
    kind = models.CharField(max_length=64)
    interval_seconds = models.PositiveIntegerField()
    payload = models.JSONField(default=dict)
    enabled = models.BooleanField(default=True)
    last_enqueued_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name
