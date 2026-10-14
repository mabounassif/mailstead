from __future__ import annotations

from datetime import datetime
from email.utils import parseaddr

from accounts.models import Mailbox
from mail.models import Folder, MessageCopy, Project, ReconcileCursor
from mail.threading import copy_is_outgoing

GENERAL_PROJECT = "General"
CHAT_FOLDERS = (Folder.INBOX, Folder.SENT)


def detach_catchall(mailbox: Mailbox) -> None:
    """Move mail out of the old automatic General bucket so it can list as contacts."""
    key = f"detached-general-{mailbox.pk}"
    if ReconcileCursor.objects.filter(name=key).exists():
        return
    MessageCopy.objects.filter(mailbox=mailbox, project__name=GENERAL_PROJECT).update(project=None)
    Project.objects.filter(mailbox=mailbox, name=GENERAL_PROJECT).delete()
    ReconcileCursor.objects.create(name=key, cursor_value="1")


def nav_project_rows(mailbox: Mailbox) -> list[dict]:
    detach_catchall(mailbox)
    rows = []
    for project in Project.objects.filter(mailbox=mailbox):
        rows.append(
            {
                "project": project,
                "count": project.copies.filter(folder__in=CHAT_FOLDERS).count(),
            }
        )
    return rows


def _sort_at(copy: MessageCopy) -> datetime:
    return copy.message.sent_at or copy.created_at


def _address_parts(value: str) -> tuple[str, str]:
    name, addr = parseaddr(value or "")
    addr = (addr or (value or "")).strip()
    return name.strip(), addr


def counterparty(message, mailbox_address: str) -> str:
    own = (mailbox_address or "").casefold()
    _name, from_addr = _address_parts(message.from_address or "")
    if own and from_addr.casefold() == own:
        return (message.to_index or "").split(",")[0].strip() or "You"
    return message.from_address or "(unknown)"


def contact_key(value: str) -> str:
    _name, addr = _address_parts(value)
    return (addr or value or "(unknown)").casefold()


def _preview(message) -> str:
    body = (message.body_text_index or "").strip().replace("\n", " ")
    if body:
        return body[:140]
    return (message.subject or "").strip()[:140]


def _direct_copies(mailbox: Mailbox) -> list[MessageCopy]:
    return list(
        MessageCopy.objects.filter(
            mailbox=mailbox,
            folder__in=CHAT_FOLDERS,
            project__isnull=True,
        ).select_related("message")
    )


def _as_chat(group: list[MessageCopy], mailbox: Mailbox, *, who: str) -> dict:
    latest = max(group, key=_sort_at)
    return {
        "copy": latest,
        "who": who,
        "address": contact_key(who),
        "title": latest.message.subject or "(no subject)",
        "preview": _preview(latest.message),
        "sort_at": _sort_at(latest),
        "unread": any(copy.is_unread and copy.folder == Folder.INBOX for copy in group),
        "count": len(group),
    }


def contact_chats(mailbox: Mailbox) -> list[dict]:
    groups: dict[str, dict] = {}
    for copy in _direct_copies(mailbox):
        who = counterparty(copy.message, mailbox.address)
        key = contact_key(who)
        bucket = groups.setdefault(key, {"who": who, "copies": []})
        if _address_parts(who)[0]:
            bucket["who"] = who
        bucket["copies"].append(copy)
    chats = [_as_chat(bucket["copies"], mailbox, who=bucket["who"]) for bucket in groups.values()]
    chats.sort(key=lambda chat: chat["sort_at"], reverse=True)
    return chats


def _conversation_item(copy: MessageCopy, mailbox: Mailbox) -> dict:
    outgoing = copy_is_outgoing(copy, mailbox)
    who = "You" if outgoing else (copy.message.from_address or "(unknown)")
    return {
        "copy": copy,
        "who": who,
        "title": copy.message.subject or "(no subject)",
        "preview": _preview(copy.message),
        "sort_at": _sort_at(copy),
        "unread": copy.is_unread and copy.folder == Folder.INBOX,
        "outgoing": outgoing,
    }


def contact_messages(mailbox: Mailbox, address: str) -> tuple[str, list[dict]]:
    key = contact_key(address)
    label = address
    items = []
    for copy in _direct_copies(mailbox):
        who = counterparty(copy.message, mailbox.address)
        if contact_key(who) != key:
            continue
        if _address_parts(who)[0]:
            label = who
        items.append(_conversation_item(copy, mailbox))
    items.sort(key=lambda item: item["sort_at"])
    return label, items


def group_messages(mailbox: Mailbox, project: Project) -> list[dict]:
    copies = MessageCopy.objects.filter(
        mailbox=mailbox,
        project=project,
        folder__in=CHAT_FOLDERS,
    ).select_related("message")
    items = [_conversation_item(copy, mailbox) for copy in copies]
    items.sort(key=lambda item: item["sort_at"])
    return items
