from __future__ import annotations

from mail.chats import contact_key, conversation_messages, direct_message_for_people, group_messages, people_key
from mail.compose import reply_all_recipients, send_compose
from mail.conversations import (
    active_cc_addresses,
    attach_to_parent,
    discard_failed_spec,
    finalize_chat_send,
    plan_chat_send,
)
from mail.models import Folder
from mail.threading import topic_key
from mail.views import _reply_header_kwargs, _send_kwargs


def _result(outbound, conversation, dm_key: str = "") -> dict:
    return {
        "ok": True,
        "conversation_id": conversation.id if conversation is not None else None,
        "dm_key": dm_key,
        "outbound_id": str(outbound.id),
    }


def _deliver(mailbox, spec):
    try:
        outbound = send_compose(
            mailbox,
            from_address=mailbox.address,
            to=spec.to,
            subject=spec.subject,
            text=spec.text,
            **_send_kwargs(spec),
        )
    except Exception:
        discard_failed_spec(spec)
        raise
    finalize_chat_send(mailbox, outbound, spec)
    return outbound


def _primary_contact(conversation, mailbox) -> str:
    if conversation is None:
        return ""
    own = (mailbox.address or "").casefold()
    for part in conversation.participants.filter(active=True).order_by("id"):
        if part.address.casefold() != own:
            return part.address
    return ""


def send_chat(mailbox, *, mode, chats, contact_address, project, thread, body, subject="", add="", drop=""):
    if not (body or "").strip():
        raise ValueError("Write a message first.")
    spec = plan_chat_send(
        mailbox,
        mode=mode,
        chats=chats,
        contact_address=contact_address,
        project=project,
        thread=thread,
        subject=subject,
        body=body,
        add_raw=add or "",
        drop_raw=drop or "",
    )
    outbound = _deliver(mailbox, spec)
    dm_key = ""
    if spec.conversation is not None and (spec.conversation.topic_key or "").startswith("dm:"):
        dm_key = people_key(spec.conversation, mailbox)
    return _result(outbound, spec.conversation, dm_key)


def send_to_conversation(mailbox, conversation, body, *, subject="", add="", drop=""):
    if conversation.mailbox_id != mailbox.id:
        raise LookupError("not_found")
    saved = None
    thread = conversation.topic_key
    is_dm = (conversation.topic_key or "").startswith("dm:")
    if is_dm:
        saved = conversation.topic_key
        thread = topic_key(conversation.topic) or thread
        conversation.topic_key = thread
        conversation.save(update_fields=["topic_key"])
    try:
        if conversation.project_id and not is_dm:
            mode = "group"
            chats = group_messages(mailbox, conversation.project)
            project = conversation.project
            contact = ""
        else:
            mode = "contact"
            chats = conversation_messages(mailbox, conversation)
            project = conversation.project
            contact = _primary_contact(conversation, mailbox)
        result = send_chat(
            mailbox,
            mode=mode,
            chats=chats,
            contact_address=contact,
            project=project,
            thread=thread,
            body=body,
            subject=subject or conversation.topic,
            add=add,
            drop=drop,
        )
        if is_dm:
            result["dm_key"] = people_key(conversation, mailbox)
        return result
    finally:
        if saved is not None:
            conversation.topic_key = saved
            conversation.save(update_fields=["topic_key"])


def start_conversation(mailbox, recipients: list[str], subject: str, body: str, *, add: str = ""):
    cleaned = [part.strip() for part in recipients if part and part.strip()]
    if not (body or "").strip():
        raise ValueError("Write a message first.")
    if not cleaned:
        raise ValueError("Add at least one participant.")
    if subject.strip():
        return _queue_new(mailbox, cleaned, subject.strip(), body, as_dm=False, add=add)
    key = ",".join(sorted(contact_key(item) for item in cleaned))
    existing = direct_message_for_people(mailbox, key)
    if existing is not None:
        return send_to_conversation(mailbox, existing, body, add=add)
    label = ", ".join(contact_key(item).split("@")[0] for item in cleaned)
    return _queue_new(mailbox, cleaned, label, body, as_dm=True, add=add)


def _queue_new(mailbox, recipients, subject, body, *, as_dm: bool, add: str):
    spec = plan_chat_send(
        mailbox,
        mode="new",
        chats=[],
        contact_address=contact_key(recipients[0]),
        project=None,
        thread="",
        subject=subject,
        body=body,
        add_raw=add,
        extra_to=recipients,
    )
    outbound = _deliver(mailbox, spec)
    dm_key = ""
    if as_dm and spec.conversation is not None:
        dm_key = people_key(spec.conversation, mailbox)
        spec.conversation.topic_key = "dm:" + dm_key
        spec.conversation.save(update_fields=["topic_key"])
    return _result(outbound, spec.conversation, dm_key)


def reply_to_copy(mailbox, copy, body: str, *, reply_all: bool = False) -> dict:
    if copy.mailbox_id != mailbox.id:
        raise LookupError("not_found")
    if copy.folder == Folder.TRASH:
        raise ValueError("Cannot reply to a message in trash.")
    if not (body or "").strip():
        raise ValueError("Write a message first.")
    message = copy.message
    headers = _reply_header_kwargs(message)
    if reply_all:
        to_list, cc_list, bcc_list = reply_all_recipients(copy, mailbox)
        outbound = send_compose(
            mailbox,
            from_address=mailbox.address,
            to=to_list,
            cc=cc_list,
            bcc=bcc_list or None,
            subject=f"Re: {message.subject}",
            text=body,
            **headers,
        )
    else:
        to_addr = message.reply_to or message.from_address
        cc = active_cc_addresses(message, mailbox, [to_addr])
        outbound = send_compose(
            mailbox,
            from_address=mailbox.address,
            to=[to_addr],
            cc=cc or None,
            subject=f"Re: {message.subject}",
            text=body,
            **headers,
        )
    attach_to_parent(mailbox, outbound, message)
    return _result(outbound, message.conversation)
