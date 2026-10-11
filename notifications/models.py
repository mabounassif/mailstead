from __future__ import annotations

import hashlib

from django.conf import settings
from django.db import models


class NotificationPreference(models.Model):
    class PreviewMode(models.TextChoices):
        PRIVATE = "private", "Private"
        SUBJECT = "subject", "Subject only"
        SENDER_SUBJECT = "sender_subject", "Sender and subject"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_prefs",
    )
    enabled = models.BooleanField(default=True)
    new_mail = models.BooleanField(default=True)
    preview_mode = models.CharField(
        max_length=16,
        choices=PreviewMode.choices,
        default=PreviewMode.PRIVATE,
    )
    updated_at = models.DateTimeField(auto_now=True)


class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(max_length=512)
    endpoint_hash = models.CharField(max_length=64, unique=True)
    keys_json = models.JSONField()
    user_agent = models.CharField(max_length=255, blank=True, default="")
    label = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=128, blank=True, default="")

    @staticmethod
    def hash_endpoint(endpoint: str) -> str:
        return hashlib.sha256(endpoint.encode("utf-8")).hexdigest()

    def subscription_info(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "keys": self.keys_json,
        }
