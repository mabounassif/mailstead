from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from jobs.queue import enqueue
from mail.models import Folder, Message, MessageCopy, OutboundMessage
from provider.resend_client import ResendError, send_email

logger = logging.getLogger(__name__)


def queue_send(outbound: OutboundMessage) -> None:
    enqueue("outbound_send", {"outbound_id": str(outbound.id)}, dedupe_key=f"outbound-send:{outbound.id}")


def send_outbound(outbound_id: str) -> None:
    outbound = OutboundMessage.objects.select_related("mailbox").get(pk=outbound_id)
    if outbound.state not in (OutboundMessage.State.QUEUED, OutboundMessage.State.HELD_PROVIDER_QUOTA):
        return
    outbound.state = OutboundMessage.State.SENDING
    outbound.save(update_fields=["state", "updated_at"])
    try:
        result = send_email(outbound.payload_json, str(outbound.idempotency_key))
        outbound.provider_id = result.get("id") or (result.get("data") or {}).get("id") or ""
        outbound.state = OutboundMessage.State.ACCEPTED
        outbound.save(update_fields=["provider_id", "state", "updated_at"])
    except ResendError as exc:
        if exc.status == 409 and exc.error_type == "concurrent_idempotent_requests":
            raise
        if exc.status == 409 and exc.error_type == "invalid_idempotent_request":
            fail_outbound(outbound, dead=True)
            return
        if exc.status == 429 and exc.error_type and "quota" in exc.error_type:
            outbound.state = OutboundMessage.State.HELD_PROVIDER_QUOTA
            outbound.save(update_fields=["state", "updated_at"])
            return
        if outbound.created_at < timezone.now() - timedelta(hours=23):
            outbound.state = OutboundMessage.State.UNCERTAIN
            outbound.save(update_fields=["state", "updated_at"])
            return
        raise


def fail_outbound(outbound: OutboundMessage, dead: bool = False) -> None:
    outbound.state = OutboundMessage.State.FAILED if dead else OutboundMessage.State.QUEUED
    outbound.save(update_fields=["state", "updated_at"])


def apply_outbound_status(payload: dict) -> None:
    email_id = payload.get("email_id")
    event_type = payload.get("type", "")
    mapping = {
        "email.delivered": OutboundMessage.State.DELIVERED,
        "email.bounced": OutboundMessage.State.BOUNCED,
        "email.failed": OutboundMessage.State.FAILED,
        "email.complained": OutboundMessage.State.COMPLAINED,
        "email.suppressed": OutboundMessage.State.SUPPRESSED,
    }
    new_state = mapping.get(event_type)
    if not new_state:
        return
    OutboundMessage.objects.filter(provider_id=email_id).update(state=new_state)


def create_outbound(mailbox, payload: dict, outbound_uuid=None) -> OutboundMessage:
    import uuid as uuid_mod

    key = outbound_uuid or uuid_mod.uuid4()
    with transaction.atomic():
        outbound = OutboundMessage.objects.create(
            mailbox=mailbox,
            payload_json=payload,
            idempotency_key=key,
        )
        msg = Message.objects.create(
            subject=payload.get("subject", ""),
            from_address=payload.get("from", mailbox.address),
            to_index=",".join(payload.get("to") or []),
            cc_index=",".join(payload.get("cc") or []),
            archived=True,
            portal_tag=str(key),
        )
        MessageCopy.objects.create(message=msg, mailbox=mailbox, folder=Folder.SENT, is_unread=False)
        queue_send(outbound)
    return outbound
