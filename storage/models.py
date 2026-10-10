from __future__ import annotations

import uuid

from django.db import models


class StorageLedger(models.Model):
    email_consumed_bytes = models.BigIntegerField(default=0)
    reserved_bytes = models.BigIntegerField(default=0)
    overflow_bytes = models.BigIntegerField(default=0)
    last_reconciled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Storage ledger"


class MailboxStorage(models.Model):
    class State(models.TextChoices):
        OK = "ok", "OK"
        WARN80 = "warn80", "Warn 80%"
        WARN90 = "warn90", "Warn 90%"
        FULL = "full", "Full"
        OVER_QUOTA = "over_quota", "Over quota"

    mailbox = models.OneToOneField("accounts.Mailbox", on_delete=models.CASCADE, related_name="storage")
    charged_bytes = models.BigIntegerField(default=0)
    state = models.CharField(max_length=16, choices=State.choices, default=State.OK)
    updated_at = models.DateTimeField(auto_now=True)


class Reservation(models.Model):
    class State(models.TextChoices):
        HELD = "held", "Held"
        COMMITTED = "committed", "Committed"
        RELEASED = "released", "Released"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mailbox = models.ForeignKey("accounts.Mailbox", on_delete=models.CASCADE, related_name="reservations")
    bytes = models.BigIntegerField()
    purpose = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    state = models.CharField(max_length=16, choices=State.choices, default=State.HELD)
    created_at = models.DateTimeField(auto_now_add=True)


class OverflowItem(models.Model):
    resend_email_id = models.CharField(max_length=128, unique=True)
    mailbox = models.ForeignKey("accounts.Mailbox", on_delete=models.CASCADE)
    bytes = models.BigIntegerField()
    blob_path = models.CharField(max_length=512, blank=True, default="")
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
