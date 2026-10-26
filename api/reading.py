from __future__ import annotations

import email
import os
from email import policy

from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from django.utils import timezone

from mail.chats import (
    channel_rows,
    contact_chats,
    contact_key,
    contact_messages,
    conversation_for_people,
    conversation_messages,
    detach_catchall,
    dm_rows,
    group_messages,
    nav_project_rows,
    people_key,
    people_label,
    person_rows,
)
from mail.conversations import ensure_mailbox_conversations, known_addresses, with_events
from mail.html_safety import sanitize_html, wrap_html_for_iframe
from mail.models import Conversation, ConversationEvent, Folder, MessageCopy, Project
from mail.templatetags.mail_extras import message_snippet
from mail.threading import copy_is_outgoing, thread_copies
from notifications.services import unread_inbox_count
from storage.capacity import physical_capacity


def iso(value) -> str | None:
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return value.isoformat()


def _message_html(message, *, load_images: bool) -> str:
    if not message.blob_id or message.unretrievable:
        return ""
    with open(message.blob.path, "rb") as handle:
        raw = handle.read()
    mime = email.message_from_bytes(raw, policy=policy.default)
    part = mime.get_body(preferencelist=("html",))
    if not part:
        return ""
    return wrap_html_for_iframe(sanitize_html(part.get_content() or "", allow_remote_images=load_images))


def chats_payload(mailbox) -> dict:
    detach_catchall(mailbox)
    ensure_mailbox_conversations(mailbox)
    return {
        "unread_count": unread_inbox_count(mailbox),
        "dms": [
            {
                "key": row["key"],
                "label": row["label"],
                "names": row["names"],
                "preview": row["preview"],
                "unread": row["unread"],
                "sort_at": iso(row["sort_at"]),
            }
            for row in dm_rows(mailbox)
        ],
        "channels": [
            {
                "id": row["id"],
                "key": row["key"],
                "title": row["title"],
                "preview": row["preview"],
                "sort_at": iso(row["sort_at"]),
            }
            for row in channel_rows(mailbox)
        ],
        "projects": [
            {"id": row["project"].id, "name": row["project"].name, "count": row["count"]}
            for row in nav_project_rows(mailbox)
        ],
        "people": person_rows(mailbox),
    }


def contacts_payload(mailbox) -> dict:
    rows = []
    for chat in contact_chats(mailbox):
        rows.append(
            {
                "address": chat["address"],
                "label": chat["who"],
                "title": chat["title"],
                "preview": chat["preview"],
                "unread": chat["unread"],
                "count": chat["count"],
                "sort_at": iso(chat["sort_at"]),
            }
        )
    return {"contacts": rows}


def _chat_item(item: dict) -> dict:
    if item.get("kind") == "event":
        return {"kind": "event", "body": item.get("body") or "", "sort_at": iso(item.get("sort_at"))}
    return {
        "kind": "message",
        "copy_id": item["copy"].id,
        "who": item.get("who") or "",
        "title": item.get("title") or "",
        "preview": item.get("preview") or "",
        "outgoing": bool(item.get("outgoing")),
        "unread": bool(item.get("unread")),
        "sort_at": iso(item.get("sort_at")),
    }


def _participants(conversation) -> list[dict]:
    if conversation is None:
        return []
    return [
        {"address": part.address, "display_name": part.display_name, "kind": part.kind}
        for part in conversation.participants.filter(active=True).order_by("id")
    ]


class OpenedChat:
    def __init__(self, *, mode, conversation, project, contact_address, thread, chats, label, dm_key):
        self.mode = mode
        self.conversation = conversation
        self.project = project
        self.contact_address = contact_address
        self.thread = thread
        self.chats = chats
        self.label = label
        self.dm_key = dm_key


def resolve_chat(mailbox, *, dm: str = "", project_id: int | None = None, contact: str = "", channel_id: int | None = None) -> OpenedChat:
    detach_catchall(mailbox)
    ensure_mailbox_conversations(mailbox)
    contact_address = (contact or "").strip()
    selected = None
    if project_id:
        selected = Project.objects.filter(mailbox=mailbox, pk=project_id).first()
        if selected is None:
            raise LookupError("not_found")
    open_conv = None
    if channel_id:
        open_conv = Conversation.objects.filter(mailbox=mailbox, pk=channel_id).first()
        if open_conv is None:
            raise LookupError("not_found")
    thread = ""
    if open_conv is not None and not contact_address and selected is None:
        mode = "channel"
        chats = conversation_messages(mailbox, open_conv)
        label = open_conv.topic
        thread = open_conv.topic_key
        dm_key = ""
    elif dm and selected is None:
        mode = "dm"
        open_conv = conversation_for_people(mailbox, dm)
        chats = conversation_messages(mailbox, open_conv) if open_conv is not None else []
        label = people_label(open_conv, mailbox) if open_conv is not None else dm
        if open_conv is not None:
            thread = open_conv.topic_key
        dm_key = people_key(open_conv, mailbox) if open_conv is not None else dm
    elif selected is not None:
        mode = "group"
        chats = group_messages(mailbox, selected)
        label = selected.name
        dm_key = ""
    elif contact_address:
        mode = "dm"
        label, _all = contact_messages(mailbox, contact_address)
        if not label:
            label = contact_address
        open_conv = (
            Conversation.objects.filter(
                mailbox=mailbox,
                participants__address=contact_key(contact_address),
                participants__active=True,
            )
            .distinct()
            .order_by("-id")
            .first()
        )
        chats = conversation_messages(mailbox, open_conv) if open_conv is not None else []
        if open_conv is not None:
            thread = open_conv.topic_key
            label = people_label(open_conv, mailbox) or label
        dm_key = people_key(open_conv, mailbox) if open_conv is not None else contact_key(contact_address)
        contact_address = contact_key(contact_address)
    else:
        raise ValueError("Choose a conversation.")
    return OpenedChat(
        mode=mode,
        conversation=open_conv,
        project=selected,
        contact_address=contact_key(contact_address) if contact_address else "",
        thread=thread,
        chats=chats,
        label=label,
        dm_key=dm_key,
    )


def serialize_chat(mailbox, opened: OpenedChat) -> dict:
    visible = with_events(opened.chats) if opened.mode in ("dm", "channel", "group") else opened.chats
    conversation = opened.conversation
    can_compose = conversation is not None or (opened.mode == "group" and bool(opened.chats))
    return {
        "mode": opened.mode,
        "conversation_id": conversation.id if conversation is not None else None,
        "label": opened.label,
        "project_id": opened.project.id if opened.project is not None else None,
        "dm_key": opened.dm_key,
        "contact": opened.contact_address,
        "subject": conversation.topic if conversation is not None else "",
        "can_compose": can_compose,
        "participants": _participants(conversation),
        "known_addresses": known_addresses(mailbox) if opened.mode in ("dm", "channel", "group") else [],
        "messages": [_chat_item(item) for item in visible],
    }


def copy_summary(copy: MessageCopy) -> dict:
    message = copy.message
    return {
        "copy_id": copy.id,
        "folder": copy.folder,
        "subject": message.subject,
        "from": message.from_address,
        "to": message.to_index,
        "snippet": message_snippet(message),
        "unread": copy.is_unread,
        "sort_at": iso(message.sent_at or copy.created_at),
    }


def page_payload(qs, page_number: str, per_page: int = 25) -> dict:
    paginator = Paginator(qs, per_page)
    page = paginator.get_page(page_number)
    return {
        "page": page.number,
        "pages": paginator.num_pages,
        "count": paginator.count,
        "results": [copy_summary(copy) for copy in page.object_list],
    }


def folder_queryset(mailbox, folder: str):
    if folder not in (Folder.JUNK, Folder.TRASH):
        raise LookupError("not_found")
    return (
        MessageCopy.objects.filter(mailbox=mailbox, folder=folder)
        .select_related("message")
        .annotate(sort_at=Coalesce("message__sent_at", "created_at"))
        .order_by("-sort_at")
    )


def search_queryset(mailbox, query: str):
    from django.db import models

    qs = MessageCopy.objects.filter(mailbox=mailbox).select_related("message")
    if not query:
        return qs.none()
    return (
        qs.filter(
            models.Q(message__subject__icontains=query)
            | models.Q(message__from_address__icontains=query)
            | models.Q(message__body_text_index__icontains=query)
            | models.Q(message__to_index__icontains=query)
        )
        .annotate(sort_at=Coalesce("message__sent_at", "created_at"))
        .order_by("-sort_at")
    )


def _attachment_payload(attachment) -> dict:
    return {
        "id": attachment.id,
        "filename": attachment.filename,
        "content_type": attachment.content_type,
        "size_bytes": attachment.size_bytes,
        "downloadable": bool(attachment.blob_id),
    }


def message_detail_payload(copy: MessageCopy, mailbox, *, load_images: bool) -> dict:
    if copy.is_unread:
        copy.is_unread = False
        copy.save(update_fields=["is_unread"])
    items = []
    for thread_copy in thread_copies(copy):
        if thread_copy.mailbox_id != mailbox.id:
            continue
        message = thread_copy.message
        items.append(
            {
                "kind": "message",
                "copy": thread_copy,
                "sort_at": message.sent_at or thread_copy.created_at,
                "payload": {
                    "kind": "message",
                    "copy_id": thread_copy.id,
                    "subject": message.subject,
                    "from": message.from_address,
                    "outgoing": copy_is_outgoing(thread_copy, mailbox),
                    "sort_at": iso(message.sent_at or thread_copy.created_at),
                    "text": message.body_text_index,
                    "html": _message_html(message, load_images=load_images),
                    "is_anchor": thread_copy.id == copy.id,
                    "bcc": thread_copy.bcc_snapshot if thread_copy.mailbox_id == mailbox.id else "",
                    "attachments": [_attachment_payload(att) for att in message.attachments.all()],
                },
            }
        )
    conv_ids = [item["copy"].message.conversation_id for item in items if item["copy"].message.conversation_id]
    for event in ConversationEvent.objects.filter(conversation_id__in=conv_ids):
        items.append(
            {
                "sort_at": event.created_at,
                "payload": {"kind": "event", "body": event.body, "sort_at": iso(event.created_at)},
            }
        )
    items.sort(key=lambda item: item["sort_at"])
    from mail.views import _reply_recipient_context

    recipients = _reply_recipient_context(copy, mailbox)
    return {
        "copy_id": copy.id,
        "folder": copy.folder,
        "can_reply": copy.folder != Folder.TRASH,
        "reply_to": recipients["reply_to_address"],
        "reply_all_to": recipients["reply_all_to"],
        "reply_all_cc": recipients["reply_all_cc"],
        "reply_subject": recipients["reply_subject"],
        "thread": [item["payload"] for item in items],
    }


def drive_payload(mailbox) -> dict:
    from mail.models import MessageAttachment
    from mail.workspace_views import _format_bytes

    capacity = physical_capacity()
    files = []
    attachments = (
        MessageAttachment.objects.filter(message__copies__mailbox=mailbox)
        .select_related("blob", "message")
        .order_by("-id")
        .distinct()
    )
    for attachment in attachments:
        copy = MessageCopy.objects.filter(message=attachment.message, mailbox=mailbox).order_by("id").first()
        if copy is None:
            continue
        path = attachment.blob.path if attachment.blob_id else ""
        size = attachment.size_bytes or (attachment.blob.size_bytes if attachment.blob_id else 0)
        files.append(
            {
                "name": attachment.filename or "(unnamed file)",
                "size": _format_bytes(size),
                "size_bytes": size,
                "subject": attachment.message.subject or "(no subject)",
                "local": bool(path and os.path.isfile(path)),
                "copy_id": copy.id,
                "attachment_id": attachment.id,
            }
        )
    return {
        "files": files,
        "disk_used": _format_bytes(capacity.used_bytes),
        "disk_total": _format_bytes(capacity.total_bytes),
        "disk_free": _format_bytes(capacity.free_bytes),
    }
