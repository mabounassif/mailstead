from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from accounts.models import Mailbox
from mail.models import Folder, MessageCopy
from notifications.models import NotificationPreference, PushSubscription
from notifications.push import build_declarative_payload, push_configured, send_push_safe


def prefs_for_user(user) -> NotificationPreference:
    pref, _ = NotificationPreference.objects.get_or_create(user=user)
    return pref


def unread_inbox_count(mailbox: Mailbox) -> int:
    return MessageCopy.objects.filter(
        mailbox=mailbox,
        folder=Folder.INBOX,
        is_unread=True,
    ).count()


def _public_url(path: str) -> str:
    base = settings.PUBLIC_URL.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def build_new_mail_payload(user, mailbox: Mailbox, copy_ids: list[int]) -> dict | None:
    pref = prefs_for_user(user)
    if not pref.enabled or not pref.new_mail:
        return None

    copies = list(
        MessageCopy.objects.filter(
            pk__in=copy_ids,
            mailbox=mailbox,
            folder=Folder.INBOX,
            is_unread=True,
        ).select_related("message")
    )
    if not copies:
        return None

    badge = unread_inbox_count(mailbox)
    if len(copies) == 1:
        copy = copies[0]
        msg = copy.message
        navigate = _public_url(f"/mail/m/{copy.pk}/")
        if pref.preview_mode == NotificationPreference.PreviewMode.SENDER_SUBJECT:
            body = f"{msg.from_address}: {msg.subject}"[:240] or "New message"
        elif pref.preview_mode == NotificationPreference.PreviewMode.SUBJECT:
            body = (msg.subject or "New message")[:240]
        else:
            body = "You have a new message in Mailstead."
        title = "New mail"
    else:
        navigate = _public_url("/mail/")
        title = "New mail"
        body = f"You have {len(copies)} new messages in Mailstead."

    return build_declarative_payload(title=title, body=body, navigate=navigate, badge=badge)


def deliver_to_user(user, payload: dict) -> int:
    sent = 0
    if push_configured():
        sent += _deliver_web(user, payload)
    from notifications.expo import deliver_expo

    sent += deliver_expo(user, payload)
    return sent


def _deliver_web(user, payload: dict) -> int:
    sent = 0
    for sub in PushSubscription.objects.filter(user=user, revoked_at__isnull=True):
        ok, err, _status = send_push_safe(sub.subscription_info(), payload)
        if ok:
            sub.last_success_at = timezone.now()
            sub.last_error = ""
            sub.save(update_fields=["last_success_at", "last_error"])
            sent += 1
        elif err == "revoked":
            sub.revoked_at = timezone.now()
            sub.last_error = "revoked"
            sub.save(update_fields=["revoked_at", "last_error"])
        else:
            sub.last_error = err or "error"
            sub.save(update_fields=["last_error"])
    return sent


def send_test_notification(user) -> int:
    payload = build_declarative_payload(
        title="Mailstead test",
        body="Notifications are working on this device.",
        navigate=_public_url("/notifications/"),
    )
    return deliver_to_user(user, payload)
