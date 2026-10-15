from __future__ import annotations

import uuid

from django.db import models


class Folder(models.TextChoices):
    INBOX = "inbox", "Inbox"
    SENT = "sent", "Sent"
    DRAFTS = "drafts", "Drafts"
    ARCHIVE = "archive", "Archive"
    JUNK = "junk", "Junk"
    TRASH = "trash", "Trash"


class Blob(models.Model):
    sha256 = models.CharField(max_length=64, unique=True)
    size_bytes = models.BigIntegerField()
    path = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blob = models.ForeignKey(Blob, on_delete=models.PROTECT, null=True, blank=True)
    resend_email_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    message_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    in_reply_to = models.CharField(max_length=255, blank=True, default="", db_index=True)
    references_text = models.TextField(blank=True, default="")
    subject = models.CharField(max_length=998, blank=True, default="")
    from_address = models.CharField(max_length=320, blank=True, default="")
    to_index = models.TextField(blank=True, default="")
    cc_index = models.TextField(blank=True, default="")
    reply_to = models.CharField(max_length=320, blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    unretrievable = models.BooleanField(default=False)
    unretrievable_reason = models.CharField(max_length=255, blank=True, default="")
    auth_spf = models.CharField(max_length=32, blank=True, default="")
    auth_dkim = models.CharField(max_length=32, blank=True, default="")
    auth_dmarc = models.CharField(max_length=32, blank=True, default="")
    body_text_index = models.TextField(blank=True, default="")
    portal_tag = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["resend_email_id"],
                condition=models.Q(resend_email_id__gt=""),
                name="uniq_resend_email_id",
            ),
        ]


class Project(models.Model):
    mailbox = models.ForeignKey("accounts.Mailbox", on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["mailbox", "name"], name="uniq_mailbox_project_name"),
        ]

    def __str__(self) -> str:
        return self.name


class MessageCopy(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="copies")
    mailbox = models.ForeignKey("accounts.Mailbox", on_delete=models.CASCADE, related_name="message_copies")
    folder = models.CharField(max_length=16, choices=Folder.choices, default=Folder.INBOX)
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True, related_name="copies"
    )
    is_unread = models.BooleanField(default=True)
    bcc_snapshot = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["mailbox", "folder", "-created_at"]),
        ]
        unique_together = [("message", "mailbox", "folder")]


class MessageAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    provider_attachment_id = models.CharField(max_length=128, blank=True, default="")
    filename = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=127, blank=True, default="")
    size_bytes = models.BigIntegerField(default=0)
    blob = models.ForeignKey(Blob, on_delete=models.PROTECT, null=True, blank=True)


class OutboundMessage(models.Model):
    class State(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENDING = "sending", "Sending"
        ACCEPTED = "accepted", "Accepted"
        DELIVERED = "delivered", "Delivered"
        BOUNCED = "bounced", "Bounced"
        FAILED = "failed", "Failed"
        COMPLAINED = "complained", "Complained"
        SUPPRESSED = "suppressed", "Suppressed"
        UNCERTAIN = "uncertain", "Uncertain"
        HELD_PROVIDER_QUOTA = "held_provider_quota", "Held (provider quota)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mailbox = models.ForeignKey("accounts.Mailbox", on_delete=models.CASCADE, related_name="outbound")
    payload_json = models.JSONField()
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True)
    provider_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    state = models.CharField(max_length=32, choices=State.choices, default=State.QUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class WebhookEvent(models.Model):
    svix_id = models.CharField(max_length=128, unique=True)
    event_type = models.CharField(max_length=64)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)


class UnroutedMessage(models.Model):
    resend_email_id = models.CharField(max_length=128, unique=True)
    envelope = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)


class FilterRule(models.Model):
    class Action(models.TextChoices):
        ALLOW = "allow", "Allow"
        BLOCK = "block", "Block"

    class Scope(models.TextChoices):
        SENDER = "sender", "Sender address"
        DOMAIN = "domain", "Sender domain"

    mailbox = models.ForeignKey(
        "accounts.Mailbox", on_delete=models.CASCADE, null=True, blank=True, related_name="filter_rules"
    )
    scope = models.CharField(max_length=16, choices=Scope.choices)
    pattern = models.CharField(max_length=255)
    action = models.CharField(max_length=16, choices=Action.choices, default=Action.BLOCK)


class ReconcileCursor(models.Model):
    name = models.CharField(max_length=64, unique=True)
    cursor_value = models.CharField(max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)


class Card(models.Model):
    mailbox = models.ForeignKey("accounts.Mailbox", on_delete=models.CASCADE, related_name="cards")
    title = models.CharField(max_length=160)
    body = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]


class VaultEntry(models.Model):
    mailbox = models.ForeignKey("accounts.Mailbox", on_delete=models.CASCADE, related_name="vault_entries")
    label = models.CharField(max_length=160)
    username = models.CharField(max_length=320, blank=True, default="")
    secret = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["label", "id"]

