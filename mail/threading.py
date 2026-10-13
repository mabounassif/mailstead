from __future__ import annotations

import re
import uuid

from django.db import models

from accounts.models import Alias
from mail.email_headers import reference_ids
from mail.models import Folder, Message, MessageCopy, OutboundMessage

_RE_PREFIX = re.compile(r"^(re|fwd|fw)\s*:\s*", re.IGNORECASE)


def normalized_subject(subject: str) -> str:
    s = (subject or "").strip()
    while True:
        m = _RE_PREFIX.match(s)
        if not m:
            break
        s = s[m.end() :].strip()
    return s.casefold()


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


def thread_copies(anchor: MessageCopy) -> list[MessageCopy]:
    mailbox = anchor.mailbox
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

    copies = _dedupe_copies(copies)
    if len(copies) <= 1:
        copies = _dedupe_copies(_subject_fallback_copies(anchor, mailbox))

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
