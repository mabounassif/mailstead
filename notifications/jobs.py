from __future__ import annotations

import logging

from accounts.models import Mailbox
from jobs.worker_runtime import register
from notifications.scheduling import pop_pending_copy_ids
from notifications.services import build_new_mail_payload, deliver_to_user

logger = logging.getLogger(__name__)


@register("push_notify_mailbox")
def handle_push_notify_mailbox(job):
    mailbox_id = job.payload.get("mailbox_id")
    if not mailbox_id:
        return
    try:
        mailbox = Mailbox.objects.select_related("user").get(pk=mailbox_id)
    except Mailbox.DoesNotExist:
        return
    copy_ids = pop_pending_copy_ids(mailbox_id)
    if not copy_ids:
        return
    payload = build_new_mail_payload(mailbox.user, mailbox, copy_ids)
    if not payload:
        return
    deliver_to_user(mailbox.user, payload)


@register("push_send")
def handle_push_send(job):
    from notifications.models import PushSubscription
    from notifications.push import build_declarative_payload, send_push_safe

    sub_id = job.payload.get("subscription_id")
    if not sub_id:
        return
    try:
        sub = PushSubscription.objects.select_related("user").get(pk=sub_id, revoked_at__isnull=True)
    except PushSubscription.DoesNotExist:
        return
    payload = job.payload.get("payload")
    if not payload:
        payload = build_declarative_payload(
            title="Mailstead",
            body="Notification",
            navigate=job.payload.get("navigate", "/mail/"),
        )
    ok, err, _ = send_push_safe(sub.subscription_info(), payload)
    if ok:
        from django.utils import timezone

        sub.last_success_at = timezone.now()
        sub.last_error = ""
        sub.save(update_fields=["last_success_at", "last_error"])
    elif err == "revoked":
        from django.utils import timezone

        sub.revoked_at = timezone.now()
        sub.last_error = "revoked"
        sub.save(update_fields=["revoked_at", "last_error"])
    else:
        raise RuntimeError(err or "push failed")
