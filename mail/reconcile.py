from __future__ import annotations

import logging

from mail.models import Message, ReconcileCursor
from jobs.queue import enqueue
from provider.resend_client import ResendError, list_receiving, resend_api_configured

logger = logging.getLogger(__name__)

CURSOR_NAME = "received_import"


def reconcile_received(batch: int = 100) -> int:
    """Page newest received mail; enqueue ingest for unknown ids."""
    if not resend_api_configured():
        logger.debug("Skipping received reconcile: RESEND_API_KEY not configured")
        return 0
    known = set(Message.objects.exclude(resend_email_id="").values_list("resend_email_id", flat=True))
    enqueued = 0
    after = None
    while True:
        try:
            page = list_receiving(limit=batch, after=after)
        except ResendError as exc:
            logger.warning("Received reconcile failed: %s", exc)
            return enqueued
        items = page.get("data") or page.get("emails") or []
        if not items:
            break
        for item in items:
            eid = item.get("id") or item.get("email_id")
            if not eid:
                continue
            if eid in known:
                return enqueued
            if enqueue(
                "inbound",
                {"email_id": eid, "notify": False},
                dedupe_key=f"inbound:{eid}",
            ):
                enqueued += 1
                known.add(eid)
        if not page.get("has_more"):
            break
        after = items[-1].get("id")
    return enqueued


def import_all_received(cursor_name: str = CURSOR_NAME) -> int:
    cursor, _ = ReconcileCursor.objects.get_or_create(name=cursor_name)
    after = cursor.cursor_value or None
    total = 0
    while True:
        page = list_receiving(limit=100, after=after or None)
        items = page.get("data") or page.get("emails") or []
        if not items:
            break
        for item in items:
            eid = item.get("id") or item.get("email_id")
            if not eid:
                continue
            if Message.objects.filter(resend_email_id=eid).exists():
                continue
            if enqueue(
                "inbound",
                {"email_id": eid, "notify": False},
                dedupe_key=f"inbound:{eid}",
            ):
                total += 1
            after = eid
        cursor.cursor_value = after or ""
        cursor.save(update_fields=["cursor_value", "updated_at"])
        if not page.get("has_more"):
            break
    return total
