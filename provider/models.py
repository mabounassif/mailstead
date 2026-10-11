from django.db import models


class UsageSnapshot(models.Model):
    fetched_at = models.DateTimeField(auto_now_add=True)
    raw_json = models.JSONField(default=dict)
    parsed_json = models.JSONField(default=dict)
    ok = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, default="")


class UsageAlert(models.Model):
    quota = models.CharField(max_length=32)
    period_key = models.CharField(max_length=64)
    threshold = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("quota", "period_key", "threshold")]


class AdminSubscriptionLabel(models.Model):
    label = models.CharField(max_length=128)
    updated_at = models.DateTimeField(auto_now=True)


class ProviderSettings(models.Model):
    webhook_id = models.CharField(max_length=128, blank=True, default="")
    webhook_secret_encrypted = models.TextField(blank=True, default="")
    webhook_disabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Provider settings"
