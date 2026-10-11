from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Login identity; mailbox address is separate."""

    email = models.EmailField(blank=True, default="")
    recovery_email = models.EmailField(blank=True, default="")

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"


class Mailbox(models.Model):
    class State(models.TextChoices):
        ACTIVE = "active", "Active"
        DISABLED = "disabled", "Disabled"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mailbox")
    address = models.EmailField(unique=True)
    quota_bytes = models.BigIntegerField(default=settings.DEFAULT_MAILBOX_QUOTA_BYTES)
    over_quota = models.BooleanField(default=False)
    state = models.CharField(max_length=16, choices=State.choices, default=State.ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.address


class Alias(models.Model):
    mailbox = models.ForeignKey(Mailbox, on_delete=models.CASCADE, related_name="aliases")
    address = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.address


class BootstrapState(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    consumed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
