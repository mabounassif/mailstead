from __future__ import annotations

from datetime import datetime
from email.utils import parseaddr

from accounts.models import Mailbox
from mail.models import Folder, MessageCopy, Project, ReconcileCursor
from mail.threading import copy_is_outgoing, topic_key

ALL_THREADS = "*"
BLANK_THREAD = "__blank__"

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


def _person_label(part) -> str:
    if part.display_name:
        return part.display_name
    return (part.address or "").split("@")[0] or part.address


def people_key(conversation, mailbox: Mailbox) -> str:
    own = (mailbox.address or "").casefold()
    addresses = sorted(
        part.address
        for part in conversation.participants.all()
        if part.active and part.address.casefold() != own
    )
    return ",".join(addresses)


def person_rows(mailbox: Mailbox) -> list[dict]:
    from mail.models import Conversation

    own = (mailbox.address or "").casefold()
    people: dict[str, str] = {}
    conversations = Conversation.objects.filter(mailbox=mailbox).prefetch_related("participants")
    for conversation in conversations:
        for part in conversation.participants.all():
            if not part.active or part.address.casefold() == own or part.address in people:
                continue
            people[part.address] = _person_label(part)
    rows = [{"address": address, "label": label} for address, label in people.items()]
    rows.sort(key=lambda row: row["label"].casefold())
    return rows


def people_label(conversation, mailbox: Mailbox) -> str:
    own = (mailbox.address or "").casefold()
    people = [
        part
        for part in conversation.participants.all()
        if part.active and part.address.casefold() != own
    ]
    people.sort(key=lambda part: _person_label(part).casefold())
    return ", ".join(_person_label(part) for part in people)


def direct_message_for_people(mailbox: Mailbox, key: str):
    from mail.models import Conversation

    wanted = frozenset(part for part in key.split(",") if part)
    if not wanted:
        return None
    conversations = (
        Conversation.objects.filter(mailbox=mailbox, topic_key__startswith="dm:")
        .prefetch_related("participants")
        .order_by("-id")
    )
    for conversation in conversations:
        got = frozenset(part for part in people_key(conversation, mailbox).split(",") if part)
        if got == wanted:
            return conversation
    return None


def conversation_for_people(mailbox: Mailbox, key: str):
    from mail.models import Conversation

    wanted = frozenset(part for part in key.split(",") if part)
    if not wanted:
        return None
    for conversation in (
        Conversation.objects.filter(mailbox=mailbox).prefetch_related("participants").order_by("-id")
    ):
        if frozenset(people_key(conversation, mailbox).split(",")) == wanted:
            return conversation
    return None


def dm_rows(mailbox: Mailbox) -> list[dict]:
    from mail.models import Conversation

    rows: dict[str, dict] = {}
    conversations = Conversation.objects.filter(mailbox=mailbox).prefetch_related("participants")
    for conversation in conversations:
        key = people_key(conversation, mailbox)
        if not key:
            continue
        latest = conversation.messages.order_by("-created_at").first()
        sort_at = conversation.created_at
        preview = ""
        if latest is not None:
            preview = _preview(latest)
            sort_at = latest.sent_at or latest.created_at
        current = rows.get(key)
        if current is not None and current["sort_at"] >= sort_at:
            continue
        label = people_label(conversation, mailbox)
        rows[key] = {
            "key": key,
            "label": label,
            "names": [part.strip() for part in label.split(",") if part.strip()],
            "preview": preview,
            "sort_at": sort_at,
            "unread": False,
        }
    ordered = list(rows.values())
    ordered.sort(key=lambda row: row["sort_at"], reverse=True)
    return ordered


def channel_rows(mailbox: Mailbox) -> list[dict]:
    from mail.models import Conversation

    rows = []
    for conversation in Conversation.objects.filter(mailbox=mailbox).exclude(topic=""):
        if conversation.topic_key in ("", BLANK_THREAD) or conversation.topic_key.startswith("dm:"):
            continue
        latest = conversation.messages.order_by("-created_at").first()
        preview = ""
        sort_at = conversation.created_at
        if latest is not None:
            preview = _preview(latest)
            sort_at = latest.sent_at or latest.created_at
        rows.append(
            {
                "id": conversation.id,
                "title": conversation.topic,
                "preview": preview,
                "sort_at": sort_at,
                "key": conversation.topic_key,
            }
        )
    rows.sort(key=lambda row: row["sort_at"], reverse=True)
    return rows


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
        )
        .select_related("message", "message__conversation")
        .prefetch_related("message__conversation__participants")
    )


def _is_participant(message, key: str) -> bool:
    conversation = message.conversation
    if conversation is None:
        return False
    return any(part.address == key and part.active for part in conversation.participants.all())


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
    copies = _direct_copies(mailbox)
    for copy in copies:
        who = counterparty(copy.message, mailbox.address)
        key = contact_key(who)
        bucket = groups.setdefault(key, {"who": who, "copies": []})
        if _address_parts(who)[0]:
            bucket["who"] = who
        bucket["copies"].append(copy)
        conversation = copy.message.conversation
        if conversation is None:
            continue
        for part in conversation.participants.all():
            if not part.active:
                continue
            part_key = contact_key(part.address)
            part_bucket = groups.setdefault(part_key, {"who": part.display_name or part.address, "copies": []})
            if part.display_name and not _address_parts(part_bucket["who"])[0]:
                part_bucket["who"] = part.display_name
            if copy not in part_bucket["copies"]:
                part_bucket["copies"].append(copy)
    chats = [_as_chat(bucket["copies"], mailbox, who=bucket["who"]) for bucket in groups.values() if bucket["copies"]]
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
        if contact_key(who) != key and not _is_participant(copy.message, key):
            continue
        if contact_key(who) == key and _address_parts(who)[0]:
            label = who
        items.append(_conversation_item(copy, mailbox))
    items.sort(key=lambda item: item["sort_at"])
    return label, items


def conversation_messages(mailbox: Mailbox, conversation) -> list[dict]:
    copies = MessageCopy.objects.filter(
        mailbox=mailbox,
        message__conversation=conversation,
        folder__in=CHAT_FOLDERS,
    ).select_related("message")
    items = [_conversation_item(copy, mailbox) for copy in copies]
    items.sort(key=lambda item: item["sort_at"])
    return items


def group_messages(mailbox: Mailbox, project: Project) -> list[dict]:
    copies = MessageCopy.objects.filter(
        mailbox=mailbox,
        project=project,
        folder__in=CHAT_FOLDERS,
    ).select_related("message")
    items = [_conversation_item(copy, mailbox) for copy in copies]
    items.sort(key=lambda item: item["sort_at"])
    return items


def thread_value(subject: str) -> str:
    return topic_key(subject)


def subject_options(items: list[dict]) -> list[dict]:
    """Latest display label for each email subject in a conversation."""
    labels: dict[str, str] = {}
    for item in items:
        raw = (item["copy"].message.subject or "").strip()
        labels[thread_value(raw)] = raw or "(no subject)"
    return [{"value": value, "label": label} for value, label in labels.items()]


def filter_thread(items: list[dict], thread: str | None) -> list[dict]:
    if not thread or thread == ALL_THREADS:
        return items
    return [item for item in items if thread_value(item["copy"].message.subject or "") == thread]


def compose_subject(items: list[dict], thread: str | None) -> str:
    if not thread or thread == ALL_THREADS:
        return ""
    for item in reversed(items):
        raw = (item["copy"].message.subject or "").strip()
        if thread_value(raw) == thread:
            return raw
    return ""


def reply_target(items: list[dict], subject: str):
    wanted = thread_value(subject)
    for item in reversed(items):
        if thread_value(item["copy"].message.subject or "") == wanted:
            return item["copy"]
    return None
