import uuid

from django.db import models


class InstallationIdentity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


class License(models.Model):
    license_key_encrypted = models.TextField(blank=True, default="")
    service_credential_encrypted = models.TextField(blank=True, default="")
    active = models.BooleanField(default=False)
    configured = models.BooleanField(default=False)
    data_flow_accepted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class EntitlementCache(models.Model):
    token = models.TextField(blank=True, default="")
    verified_claims = models.JSONField(default=dict)
    valid_until = models.DateTimeField(null=True, blank=True)
    grace_until = models.DateTimeField(null=True, blank=True)
    last_refresh = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")


class ScanResult(models.Model):
    message = models.ForeignKey("mail.Message", on_delete=models.CASCADE, related_name="scan_results")
    verdict = models.CharField(max_length=16)
    score = models.FloatField(default=0)
    reasons = models.JSONField(default=list)
    service = models.CharField(max_length=128)
    engine_version = models.CharField(max_length=64, blank=True, default="")
    model_version = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
