from __future__ import annotations

from django.http import HttpRequest

from accounts.models import Mailbox
from mail.models import Folder, MessageCopy


def mail_nav_counts(request: HttpRequest) -> dict:
    if not request.user.is_authenticated:
        return {"inbox_unread_count": 0}
    try:
        mailbox = request.user.mailbox
    except Mailbox.DoesNotExist:
        return {"inbox_unread_count": 0}
    count = MessageCopy.objects.filter(
        mailbox=mailbox,
        folder=Folder.INBOX,
        is_unread=True,
    ).count()
    return {"inbox_unread_count": count}
