from __future__ import annotations

import re
import uuid

from django.db import models

from accounts.models import Alias
from mail.email_headers import reference_ids
from mail.models import Folder, Message, MessageCopy, OutboundMessage

_RE_PREFIX = re.compile(r"^(re|fwd|fw)\s*:\s*", re.IGNORECASE)
BLANK_TOPIC = "__blank__"
_GENERIC_TOPICS = {"(no subject)", "no subject", "untitled"}


def _strip_was_clauses(subject: str) -> str:
    s = (subject or "").strip()
    while s.endswith(")"):
        depth = 0
        start = None
        for index in range(len(s) - 1, -1, -1):
            char = s[index]
            if char == ")":
                depth += 1
            elif char == "(":
                depth -= 1
                if depth == 0:
                    start = index
                    break
        if start is None:
            break
        inner = s[start + 1 : -1].strip()
        if not inner.lower().startswith("was:"):
            break
        s = s[:start].strip()
    return s


def _strip_reply_prefixes(subject: str) -> str:
    s = (subject or "").strip()
    while True:
        match = _RE_PREFIX.match(s)
        if not match:
            break
        s = s[match.end() :].strip()
    return s


def display_topic(subject: str) -> str:
    return _strip_reply_prefixes(_strip_was_clauses(subject))


def normalized_subject(subject: str) -> str:
    return display_topic(subject).casefold()


def topic_key(subject: str) -> str:
    norm = normalized_subject(subject)
    return norm if norm else BLANK_TOPIC


def topic_is_generic(subject: str) -> bool:
    norm = normalized_subject(subject)
    return not norm or norm in _GENERIC_TOPICS


def effective_message_id(message: Message) -> str:
    if message.message_id:
        return message.message_id.strip()
    tag = (message.portal_tag or "").strip()
    if not tag:
        return ""
    try:
        outbound_uuid = uuid.UUID(tag)
    except ValueError:
        return ""
    outbound = OutboundMessage.objects.filter(pk=outbound_uuid).first()
    if not outbound:
        return ""
    headers = (outbound.payload_json or {}).get("headers") or {}
    return str(headers.get("Message-ID") or "").strip()


def _ids_for_message(message: Message) -> set[str]:
    ids = set(reference_ids(message.references_text, message.in_reply_to, effective_message_id(message)))
    return {x for x in ids if x}


def expand_thread_ids(mailbox, seed: set[str]) -> set[str]:
    ids = {x for x in seed if x}
    if not ids:
        return ids
    changed = True
    while changed:
        changed = False
        link_q = models.Q(message_id__in=ids) | models.Q(in_reply_to__in=ids)
        refs_q = models.Q()
        for mid in ids:
            refs_q |= models.Q(references_text__icontains=mid)
        msgs = Message.objects.filter(copies__mailbox=mailbox).filter(link_q | refs_q).distinct()
        for msg in msgs:
            for mid in _ids_for_message(msg):
                if mid not in ids:
                    ids.add(mid)
                    changed = True
    return ids


def _subject_fallback_copies(anchor: MessageCopy, mailbox) -> list[MessageCopy]:
    norm = normalized_subject(anchor.message.subject)
    if not norm:
        return [anchor]
    copies: list[MessageCopy] = []
    for copy in MessageCopy.objects.filter(mailbox=mailbox).select_related("message"):
        if normalized_subject(copy.message.subject) == norm:
            copies.append(copy)
    return copies or [anchor]


def _dedupe_copies(copies: list[MessageCopy]) -> list[MessageCopy]:
    seen: set[int] = set()
    out: list[MessageCopy] = []
    for copy in copies:
        if copy.message_id in seen:
            continue
        seen.add(copy.message_id)
        out.append(copy)
    return out


def reference_chain(message: Message) -> str:
    ordered: list[str] = []
    for token in reference_ids(message.references_text, message.in_reply_to, effective_message_id(message)):
        if token not in ordered:
            ordered.append(token)
    return " ".join(ordered[-25:])


def thread_copies(anchor: MessageCopy) -> list[MessageCopy]:
    mailbox = anchor.mailbox
    conversation = anchor.message.conversation
    if conversation is not None and conversation.mailbox_id == mailbox.id:
        copies = _dedupe_copies(
            list(
                MessageCopy.objects.filter(mailbox=mailbox, message__conversation=conversation).select_related(
                    "message"
                )
            )
        )
        copies.sort(key=lambda c: c.message.sent_at or c.created_at)
        return copies or [anchor]

    seed = _ids_for_message(anchor.message)
    ids = expand_thread_ids(mailbox, seed)

    if ids:
        link_q = models.Q(message__message_id__in=ids) | models.Q(message__in_reply_to__in=ids)
        refs_q = models.Q()
        for mid in ids:
            refs_q |= models.Q(message__references_text__icontains=mid)
        copies = list(
            MessageCopy.objects.filter(mailbox=mailbox)
            .filter(link_q | refs_q)
            .select_related("message")
            .distinct()
        )
    else:
        copies = []

    id_copies = _dedupe_copies(copies)
    subject_copies = _dedupe_copies(_subject_fallback_copies(anchor, mailbox))
    if len(subject_copies) > len(id_copies):
        copies = subject_copies
    elif id_copies:
        copies = id_copies
    else:
        copies = subject_copies or [anchor]

    copies.sort(key=lambda c: c.message.sent_at or c.created_at)
    return copies


def mailbox_from_addresses(mailbox) -> set[str]:
    addrs = {mailbox.address.lower()}
    for alias in Alias.objects.filter(mailbox=mailbox, is_active=True):
        addrs.add(alias.address.lower())
    return addrs


def copy_is_outgoing(copy: MessageCopy, mailbox) -> bool:
    if copy.folder == Folder.SENT:
        return True
    from_addr = (copy.message.from_address or "").strip().lower()
    return from_addr in mailbox_from_addresses(mailbox)
