from __future__ import annotations

from django.http import HttpRequest

from accounts.models import Mailbox
from mail.chats import contact_chats, nav_project_rows
from mail.models import Folder, MessageCopy


def mail_nav_counts(request: HttpRequest) -> dict:
    if not request.user.is_authenticated:
        return {"inbox_unread_count": 0, "nav_projects": [], "nav_contacts": []}
    try:
        mailbox = request.user.mailbox
    except Mailbox.DoesNotExist:
        return {"inbox_unread_count": 0, "nav_projects": [], "nav_contacts": []}
    count = MessageCopy.objects.filter(
        mailbox=mailbox,
        folder=Folder.INBOX,
        is_unread=True,
    ).count()
    projects = nav_project_rows(mailbox)
    return {
        "inbox_unread_count": count,
        "nav_projects": projects,
        "nav_contacts": contact_chats(mailbox),
    }
