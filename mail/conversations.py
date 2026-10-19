from __future__ import annotations

import re
from email.utils import parseaddr

from mail.chats import contact_key, counterparty
from mail.email_headers import reference_ids
from mail.models import (
    Conversation,
    ConversationEvent,
    ConversationParticipant,
    Message,
    MessageCopy,
    OutboundMessage,
)
from mail.threading import (
    display_topic,
    effective_message_id,
    mailbox_from_addresses,
    reference_chain,
    topic_is_generic,
    topic_key,
)

_MENTION = re.compile(r"(?<![\w.+-])@([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})")
_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class ChatSpec:
    def __init__(self) -> None:
        self.to: list[str] = []
        self.cc: list[str] = []
        self.bcc: list[str] = []
        self.subject = ""
        self.text = ""
        self.in_reply_to = ""
        self.references = ""
        self.conversation: Conversation | None = None
        self.created = False
        self.activate: list[tuple[str, str, str]] = []
        self.drop = ""
        self.drop_name = ""
        self.project = None


def bare_address(value: str) -> str:
    _name, addr = parseaddr(value or "")
    return (addr or (value or "")).strip().lower()


def address_name(value: str) -> str:
    name, _addr = parseaddr(value or "")
    return name.strip()


def _split_addresses(value: str) -> list[str]:
    found: list[str] = []
    for part in (value or "").replace(";", ",").split(","):
        addr = bare_address(part)
        if addr and addr not in found:
            found.append(addr)
    return found


def _valid_emails(values: list[str]) -> list[str]:
    found: list[str] = []
    for value in values:
        addr = bare_address(value)
        if addr and _EMAIL.match(addr) and addr not in found:
            found.append(addr)
    return found


def mention_addresses(body: str) -> list[str]:
    found: list[str] = []
    for match in _MENTION.finditer(body or ""):
        addr = match.group(1).lower()
        if addr not in found:
            found.append(addr)
    return found


def parse_address_list(raw: str) -> list[str]:
    return _valid_emails(re.split(r"[\s,;]+", raw or ""))


def bcc_notice(address: str, display_name: str = "") -> str:
    name = (display_name or "").strip() or address.split("@", 1)[0]
    return f"-Bcc @{name} (moving to BCC to save inbox)"


def added_event_body(address: str) -> str:
    return f"System: {address} was added to the thread"


def dropped_event_body(address: str) -> str:
    return f"System: {address} was moved to BCC"


def _header_ids(message: Message) -> set[str]:
    return {token for token in reference_ids(message.references_text, message.in_reply_to, effective_message_id(message)) if token}


def _sort_message(message: Message):
    return message.sent_at or message.created_at


def latest_message(conversation: Conversation) -> Message | None:
    messages = list(conversation.messages.all())
    if not messages:
        return None
    messages.sort(key=_sort_message)
    return messages[-1]


def conversation_for_topic(mailbox, key: str, *, contact: str = "", project=None) -> Conversation | None:
    qs = Conversation.objects.filter(mailbox=mailbox, topic_key=key)
    if project is not None:
        qs = qs.filter(project=project)
    else:
        qs = qs.filter(project__isnull=True)
    if contact:
        qs = qs.filter(participants__address=contact)
    return qs.distinct().order_by("-id").first()


def _project_for(copies: list[MessageCopy]):
    projects = [copy.project for copy in copies if copy.project_id]
    return projects[0] if projects else None


def _seed_participants(conversation: Conversation, messages: list[Message], mailbox) -> None:
    own = mailbox_from_addresses(mailbox)
    seen: set[str] = set(conversation.participants.values_list("address", flat=True))
    ordered = sorted(messages, key=_sort_message)
    for message in ordered:
        from_addr = bare_address(message.from_address)
        tos = _split_addresses(message.to_index)
        ccs = _split_addresses(message.cc_index)
        primary = ""
        if from_addr and from_addr not in own:
            primary = from_addr
        else:
            for addr in tos:
                if addr not in own:
                    primary = addr
                    break
        for addr in [primary, *tos, *ccs]:
            if not addr or addr in own or addr in seen:
                continue
            seen.add(addr)
            kind = ConversationParticipant.Kind.TO if addr == primary else ConversationParticipant.Kind.CC
            name = address_name(message.from_address) if addr == from_addr else ""
            ConversationParticipant.objects.create(
                conversation=conversation,
                address=addr,
                display_name=name,
                kind=kind,
                active=True,
            )


def _match_existing_conversation(mailbox, messages: list[Message]) -> Conversation | None:
    for message in messages:
        in_reply = (message.in_reply_to or "").strip()
        candidates = [in_reply] if in_reply else []
        candidates.extend(reversed(reference_ids(message.references_text)))
        for mid in candidates:
            if not mid:
                continue
            parent = (
                Message.objects.filter(copies__mailbox=mailbox, message_id=mid, conversation__isnull=False)
                .select_related("conversation")
                .first()
            )
            if parent is not None and parent.conversation.mailbox_id == mailbox.id:
                return parent.conversation
    return None


def _assign_buckets(mailbox, buckets: list[dict]) -> Conversation:
    messages = [bucket["message"] for bucket in buckets]
    messages.sort(key=_sort_message)
    existing = _match_existing_conversation(mailbox, messages)
    key = topic_key(messages[0].subject)
    if existing is not None and (key == existing.topic_key or topic_is_generic(messages[0].subject)):
        Message.objects.filter(pk__in=[message.pk for message in messages]).update(conversation=existing)
        _seed_participants(existing, messages, mailbox)
        return existing
    if existing is not None:
        copies: list[MessageCopy] = []
        for bucket in buckets:
            copies.extend(bucket["copies"])
        conversation = Conversation.objects.create(
            mailbox=mailbox,
            topic=display_topic(messages[0].subject) or messages[0].subject,
            topic_key=key,
            project=existing.project or _project_for(copies),
            spun_from=existing,
        )
        _copy_participants(existing, conversation)
        Message.objects.filter(pk__in=[message.pk for message in messages]).update(conversation=conversation)
        _seed_participants(conversation, messages, mailbox)
        return conversation
    return _create_for_buckets(mailbox, buckets)


def _create_for_buckets(mailbox, buckets: list[dict]) -> Conversation:
    messages = [bucket["message"] for bucket in buckets]
    messages.sort(key=_sort_message)
    copies: list[MessageCopy] = []
    for bucket in buckets:
        copies.extend(bucket["copies"])
    first = messages[0]
    topic = display_topic(first.subject) or first.subject or ""
    conversation = Conversation.objects.create(
        mailbox=mailbox,
        topic=topic,
        topic_key=topic_key(first.subject),
        project=_project_for(copies),
    )
    Message.objects.filter(pk__in=[message.pk for message in messages]).update(conversation=conversation)
    _seed_participants(conversation, messages, mailbox)
    return conversation


def ensure_mailbox_conversations(mailbox) -> None:
    copies = list(
        MessageCopy.objects.filter(mailbox=mailbox, message__conversation__isnull=True).select_related("message")
    )
    if not copies:
        return
    by_pk: dict = {}
    for copy in copies:
        by_pk.setdefault(copy.message_id, {"message": copy.message, "copies": []})["copies"].append(copy)

    parent = {pk: pk for pk in by_pk}

    def find(pk):
        while parent[pk] != pk:
            parent[pk] = parent[parent[pk]]
            pk = parent[pk]
        return pk

    def union(left, right):
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    index: dict[str, object] = {}
    for pk, bucket in by_pk.items():
        ids = _header_ids(bucket["message"])
        if not ids:
            continue
        for mid in ids:
            other = index.get(mid)
            if other is not None:
                union(pk, other)
            else:
                index[mid] = pk

    groups: dict = {}
    loose: list[dict] = []
    for pk, bucket in by_pk.items():
        if _header_ids(bucket["message"]):
            groups.setdefault(find(pk), []).append(bucket)
        else:
            loose.append(bucket)
    for buckets in groups.values():
        _assign_buckets(mailbox, buckets)

    bundled: dict = {}
    for bucket in loose:
        message = bucket["message"]
        who = contact_key(counterparty(message, mailbox.address))
        project_id = bucket["copies"][0].project_id if bucket["copies"] else None
        bundled.setdefault((who, topic_key(message.subject), project_id), []).append(bucket)
    for buckets in bundled.values():
        _assign_buckets(mailbox, buckets)


def _reply_headers(message: Message | None) -> tuple[str, str]:
    if message is None:
        return "", ""
    mid = effective_message_id(message)
    if not mid:
        return "", ""
    return mid, reference_chain(message) or mid


def _active_map(conversation: Conversation) -> dict[str, ConversationParticipant]:
    return {part.address: part for part in conversation.participants.all()}


def known_addresses(mailbox) -> list[str]:
    found: list[str] = []

    def add(raw: str) -> None:
        for addr in _split_addresses(raw):
            if addr not in found:
                found.append(addr)

    for message in Message.objects.filter(copies__mailbox=mailbox).only("from_address", "to_index", "cc_index")[:300]:
        add(message.from_address)
        add(message.to_index)
        add(message.cc_index)
    own = mailbox_from_addresses(mailbox)
    return [addr for addr in found if addr not in own][:50]


def plan_chat_send(
    mailbox,
    *,
    mode: str,
    chats: list[dict],
    contact_address: str,
    project,
    thread: str,
    subject: str,
    body: str,
    add_raw: str = "",
    drop_raw: str = "",
    extra_to: list[str] | None = None,
) -> ChatSpec:
    ensure_mailbox_conversations(mailbox)
    contact = contact_key(contact_address) if contact_address else ""
    open_conv = None
    if thread:
        open_conv = conversation_for_topic(mailbox, thread, contact=contact, project=project)
    posted = (subject or "").strip() or (open_conv.topic if open_conv else "")
    if topic_is_generic(posted):
        raise ValueError("Add a topic before sending.")
    key = topic_key(posted)
    display = display_topic(posted) or posted
    drop = bare_address(drop_raw)
    extras = parse_address_list(add_raw) + mention_addresses(body)
    own = mailbox_from_addresses(mailbox)

    spec = ChatSpec()
    spec.project = project
    spec.drop = drop
    continuing = None
    spin_from = None
    if open_conv is not None and open_conv.topic_key == key:
        continuing = open_conv
    elif open_conv is not None and open_conv.topic_key != key:
        spin_from = open_conv
    else:
        continuing = conversation_for_topic(mailbox, key, contact=contact, project=project)

    try:
        _fill_delivery(
            spec,
            mailbox,
            mode,
            chats,
            contact,
            project,
            key,
            display,
            drop,
            extras,
            own,
            continuing,
            spin_from,
            body,
            extra_to or [],
        )
    except ValueError:
        discard_failed_spec(spec)
        raise
    return spec


def _fill_delivery(spec, mailbox, mode, chats, contact, project, key, display, drop, extras, own, continuing, spin_from, body, extra_to):
    if spin_from is not None:
        spec.conversation = Conversation.objects.create(
            mailbox=mailbox,
            topic=display,
            topic_key=key,
            project=project or spin_from.project,
            spun_from=spin_from,
        )
        spec.created = True
        for part in spin_from.participants.filter(active=True):
            if part.address == drop or part.address in own:
                continue
            ConversationParticipant.objects.create(
                conversation=spec.conversation,
                address=part.address,
                display_name=part.display_name,
                kind=part.kind,
                active=True,
            )
        parent = latest_message(spin_from)
        spec.in_reply_to, spec.references = _reply_headers(parent)
        old_topic = spin_from.topic or (display_topic(parent.subject) if parent else "")
        spec.subject = f"{display} (was: {old_topic})"
    elif continuing is not None:
        spec.conversation = continuing
        parent = latest_message(continuing)
        spec.in_reply_to, spec.references = _reply_headers(parent)
        spec.subject = f"Re: {continuing.topic}" if parent is not None else continuing.topic
    else:
        spec.conversation = Conversation.objects.create(
            mailbox=mailbox,
            topic=display,
            topic_key=key,
            project=project,
        )
        spec.created = True
        spec.subject = display

    participants = _active_map(spec.conversation)
    if drop:
        part = participants.get(drop)
        if part is None or not part.active:
            raise ValueError("That person is not in this conversation.")
        if part.kind != ConversationParticipant.Kind.CC:
            raise ValueError("Only people on Cc can be moved to Bcc.")
        spec.drop_name = part.display_name
        part_active = {addr: item for addr, item in participants.items() if addr != drop and item.active}
    else:
        part_active = {addr: item for addr, item in participants.items() if item.active}

    to_list: list[str] = []
    cc_list: list[str] = []
    if mode == "new":
        to_list = [addr for addr in _valid_emails(extra_to or []) if addr not in own]
    elif mode == "contact" and contact:
        to_list = [contact]
    else:
        for addr, part in part_active.items():
            if part.kind == ConversationParticipant.Kind.TO and addr not in own:
                to_list.append(addr)
        if not to_list:
            for item in chats:
                addr = contact_key(counterparty(item["copy"].message, mailbox.address))
                if addr and "@" in addr and addr not in own and addr != drop and addr not in to_list:
                    to_list.append(addr)

    for addr, part in part_active.items():
        if addr in own or addr in to_list or addr == drop:
            continue
        if part.kind == ConversationParticipant.Kind.CC or addr not in to_list:
            if addr not in cc_list and addr not in to_list:
                cc_list.append(addr)

    for addr in extras:
        if addr in own or addr == drop or addr in to_list or addr in cc_list:
            continue
        cc_list.append(addr)

    if not to_list and not cc_list:
        raise ValueError("This conversation has no recipient yet.")
    if not to_list:
        to_list = [cc_list.pop(0)]

    notice = ""
    if drop:
        notice = bcc_notice(drop, spec.drop_name)
        text = f"{body.strip()}\n{notice}".strip() if body.strip() else notice
    else:
        if not body.strip():
            raise ValueError("Write a message first.")
        text = body.strip()

    names: dict[str, str] = {}
    for addr in to_list:
        existing = participants.get(addr)
        names[addr] = existing.display_name if existing else ""
        spec.activate.append((addr, ConversationParticipant.Kind.TO, names[addr]))
    for addr in cc_list:
        existing = participants.get(addr)
        spec.activate.append((addr, ConversationParticipant.Kind.CC, existing.display_name if existing else ""))

    spec.to = to_list
    spec.cc = cc_list
    spec.bcc = [drop] if drop else []
    spec.text = text


def finalize_chat_send(mailbox, outbound, spec: ChatSpec) -> None:
    if not isinstance(outbound, OutboundMessage) or spec.conversation is None:
        return
    message = Message.objects.filter(portal_tag=str(outbound.idempotency_key)).first()
    if message is None:
        return
    message.conversation = spec.conversation
    message.save(update_fields=["conversation"])
    copy = MessageCopy.objects.filter(message=message, mailbox=mailbox).first()
    if copy is not None:
        updates = []
        if spec.project is not None and copy.project_id != spec.project.id:
            copy.project = spec.project
            updates.append("project")
        if spec.bcc:
            copy.bcc_snapshot = ",".join(spec.bcc)
            updates.append("bcc_snapshot")
        if updates:
            copy.save(update_fields=updates)
    existing = {part.address: part for part in spec.conversation.participants.all()}
    for addr, kind, name in spec.activate:
        part = existing.get(addr)
        if part is None:
            ConversationParticipant.objects.create(
                conversation=spec.conversation,
                address=addr,
                display_name=name,
                kind=kind,
                active=True,
            )
            if kind == ConversationParticipant.Kind.CC:
                ConversationEvent.objects.create(
                    conversation=spec.conversation,
                    kind=ConversationEvent.Kind.ADDED,
                    address=addr,
                    body=added_event_body(addr),
                )
        elif not part.active:
            part.active = True
            part.kind = kind
            if name:
                part.display_name = name
            part.save(update_fields=["active", "kind", "display_name"])
            ConversationEvent.objects.create(
                conversation=spec.conversation,
                kind=ConversationEvent.Kind.ADDED,
                address=addr,
                body=added_event_body(addr),
            )
    if spec.drop:
        part = existing.get(spec.drop)
        if part is not None and part.active:
            part.active = False
            part.save(update_fields=["active"])
        ConversationEvent.objects.create(
            conversation=spec.conversation,
            kind=ConversationEvent.Kind.DROPPED,
            address=spec.drop,
            body=dropped_event_body(spec.drop),
        )


def attach_to_parent(mailbox, outbound, parent: Message) -> None:
    if not isinstance(outbound, OutboundMessage) or not parent.conversation_id:
        return
    if parent.conversation.mailbox_id != mailbox.id:
        return
    message = Message.objects.filter(portal_tag=str(outbound.idempotency_key)).first()
    if message is None or message.conversation_id:
        return
    message.conversation = parent.conversation
    message.save(update_fields=["conversation"])
    _seed_participants(parent.conversation, [message], mailbox)


def discard_failed_spec(spec: ChatSpec) -> None:
    if spec.created and spec.conversation is not None and not spec.conversation.messages.exists():
        spec.conversation.delete()


def _external_addresses(message: Message, mailbox) -> list[tuple[str, str]]:
    own = mailbox_from_addresses(mailbox)
    from_addr = bare_address(message.from_address)
    tos = _split_addresses(message.to_index)
    ccs = _split_addresses(message.cc_index)
    primary = from_addr if from_addr and from_addr not in own else ""
    if not primary:
        for addr in tos:
            if addr not in own:
                primary = addr
                break
    ordered: list[tuple[str, str]] = []
    seen: set[str] = set()
    for addr in [primary, *tos, *ccs]:
        if not addr or addr in own or addr in seen:
            continue
        seen.add(addr)
        kind = ConversationParticipant.Kind.TO if addr == primary else ConversationParticipant.Kind.CC
        ordered.append((addr, kind))
    return ordered


def _copy_participants(source: Conversation, target: Conversation) -> None:
    for part in source.participants.filter(active=True):
        ConversationParticipant.objects.create(
            conversation=target,
            address=part.address,
            display_name=part.display_name,
            kind=part.kind,
            active=True,
        )


def assign_inbound_message(message: Message, mailbox, copy: MessageCopy | None = None) -> None:
    if message.conversation_id and message.conversation.mailbox_id != mailbox.id:
        return
    key = topic_key(message.subject)
    matched = None
    if message.conversation_id and message.conversation.mailbox_id == mailbox.id:
        matched = message.conversation
    else:
        in_reply = (message.in_reply_to or "").strip()
        if in_reply:
            parent = (
                Message.objects.filter(copies__mailbox=mailbox, message_id=in_reply, conversation__isnull=False)
                .select_related("conversation")
                .first()
            )
            if parent is not None:
                matched = parent.conversation
        if matched is None:
            for mid in reversed(reference_ids(message.references_text)):
                parent = (
                    Message.objects.filter(copies__mailbox=mailbox, message_id=mid, conversation__isnull=False)
                    .select_related("conversation")
                    .first()
                )
                if parent is not None:
                    matched = parent.conversation
                    break
        if matched is not None and key != matched.topic_key and not topic_is_generic(message.subject):
            spun = Conversation.objects.create(
                mailbox=mailbox,
                topic=display_topic(message.subject) or message.subject,
                topic_key=key,
                project=matched.project,
                spun_from=matched,
            )
            _copy_participants(matched, spun)
            matched = spun
        elif matched is None and not topic_is_generic(message.subject):
            addrs = [addr for addr, _kind in _external_addresses(message, mailbox)]
            if addrs:
                matched = (
                    Conversation.objects.filter(
                        mailbox=mailbox,
                        topic_key=key,
                        participants__address__in=addrs,
                        participants__active=True,
                    )
                    .distinct()
                    .order_by("-id")
                    .first()
                )
        if matched is None:
            project = copy.project if copy is not None and copy.project_id else None
            matched = Conversation.objects.create(
                mailbox=mailbox,
                topic=display_topic(message.subject) or (message.subject or ""),
                topic_key=key,
                project=project,
            )
        if message.conversation_id != matched.id:
            message.conversation = matched
            message.save(update_fields=["conversation"])

    had_participants = matched.participants.exists()
    existing = {part.address: part for part in matched.participants.all()}
    for addr, kind in _external_addresses(message, mailbox):
        part = existing.get(addr)
        if part is None:
            name = address_name(message.from_address) if addr == bare_address(message.from_address) else ""
            ConversationParticipant.objects.create(
                conversation=matched,
                address=addr,
                display_name=name,
                kind=kind,
                active=True,
            )
            if had_participants:
                ConversationEvent.objects.create(
                    conversation=matched,
                    kind=ConversationEvent.Kind.ADDED,
                    address=addr,
                    body=added_event_body(addr),
                )
        elif not part.active:
            continue


def active_cc_addresses(message: Message, mailbox, exclude: list[str] | None = None) -> list[str]:
    if not message.conversation_id or message.conversation.mailbox_id != mailbox.id:
        return []
    skip = mailbox_from_addresses(mailbox) | {bare_address(addr) for addr in (exclude or [])}
    found: list[str] = []
    for part in message.conversation.participants.filter(active=True):
        if part.address in skip or part.kind != ConversationParticipant.Kind.CC:
            continue
        found.append(part.address)
    return found


def inactive_addresses(message: Message) -> set[str]:
    if not message.conversation_id:
        return set()
    return set(message.conversation.participants.filter(active=False).values_list("address", flat=True))


def with_events(items: list[dict]) -> list[dict]:
    conv_ids = [item["copy"].message.conversation_id for item in items if item["copy"].message.conversation_id]
    merged = []
    for item in items:
        merged.append({**item, "kind": "message"})
    if conv_ids:
        for event in ConversationEvent.objects.filter(conversation_id__in=conv_ids):
            merged.append(
                {
                    "kind": "event",
                    "body": event.body,
                    "sort_at": event.created_at,
                    "outgoing": False,
                }
            )
    merged.sort(key=lambda item: item["sort_at"])
    return merged

