from django.db import models


class ProviderSettings(models.Model):
    webhook_id = models.CharField(max_length=128, blank=True, default="")
    webhook_secret_encrypted = models.TextField(blank=True, default="")
    webhook_disabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Provider settings"
