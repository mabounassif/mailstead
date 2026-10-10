from __future__ import annotations

import json
import logging

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from jobs.queue import enqueue
from mail.models import WebhookEvent
from provider.crypto import decrypt
from provider.models import ProviderSettings
from provider.resend_client import verify_webhook

logger = logging.getLogger(__name__)

MAX_WEBHOOK_BYTES = 256 * 1024


@csrf_exempt
@require_POST
def resend_webhook(request: HttpRequest) -> HttpResponse:
    if len(request.body) > MAX_WEBHOOK_BYTES:
        return HttpResponse(status=413)
    settings_row = ProviderSettings.objects.first()
    secret = settings.RESEND_WEBHOOK_SECRET
    if settings_row and settings_row.webhook_secret_encrypted:
        secret = decrypt(settings_row.webhook_secret_encrypted)
    if not secret:
        return HttpResponse("webhook not configured", status=400)

    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }
    try:
        verify_webhook(request.body, headers, secret)
    except Exception:
        return HttpResponse("invalid signature", status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("invalid json", status=400)

    svix_id = headers["svix-id"]
    event_type = payload.get("type", "")
    data = payload.get("data") or {}
    email_id = data.get("email_id") or data.get("id") or ""

    with transaction.atomic():
        if WebhookEvent.objects.filter(svix_id=svix_id).exists():
            return JsonResponse({"ok": True})
        WebhookEvent.objects.create(svix_id=svix_id, event_type=event_type, payload=payload)
        if event_type == "email.received" and email_id:
            enqueue("inbound", {"email_id": email_id, "webhook": data}, dedupe_key=f"inbound:{email_id}")
        elif email_id and event_type.startswith("email."):
            enqueue(
                "outbound_status",
                {"email_id": email_id, "type": event_type, "data": data},
                dedupe_key=f"outbound-status:{email_id}:{event_type}",
            )
    return JsonResponse({"ok": True})
