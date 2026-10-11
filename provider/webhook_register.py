from __future__ import annotations

import logging

from django.conf import settings

from provider.crypto import encrypt
from provider.models import ProviderSettings
from provider.resend_client import ResendError, create_webhook, list_webhooks, resend_api_configured

logger = logging.getLogger(__name__)

EVENTS = [
    "email.received",
    "email.sent",
    "email.delivered",
    "email.delivery_delayed",
    "email.bounced",
    "email.complained",
    "email.failed",
    "email.suppressed",
]


def webhook_endpoint() -> str:
    return settings.PUBLIC_URL.rstrip("/") + "/hooks/resend"


def ensure_webhook_registered() -> ProviderSettings:
    row = ProviderSettings.objects.first() or ProviderSettings.objects.create()
    if not resend_api_configured():
        logger.warning("Skipping webhook registration: set a valid RESEND_API_KEY")
        return row
    endpoint = webhook_endpoint()
    try:
        hooks = list_webhooks()
    except ResendError as exc:
        logger.warning("Webhook registration failed: %s", exc)
        row.webhook_disabled = True
        row.save(update_fields=["webhook_disabled", "updated_at"])
        return row
    items = hooks.get("data") or hooks.get("webhooks") or []
    for hook in items:
        if hook.get("endpoint") == endpoint:
            row.webhook_id = hook.get("id") or ""
            secret = hook.get("signing_secret") or ""
            if secret:
                row.webhook_secret_encrypted = encrypt(secret)
            row.webhook_disabled = hook.get("disabled", False)
            row.save()
            return row
    created = create_webhook(endpoint, EVENTS)
    row.webhook_id = created.get("id") or ""
    secret = created.get("signing_secret") or ""
    if secret:
        row.webhook_secret_encrypted = encrypt(secret)
    row.webhook_disabled = False
    row.save()
    return row
