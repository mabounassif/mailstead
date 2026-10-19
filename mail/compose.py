from __future__ import annotations

import base64
import uuid
from email.utils import formataddr, parseaddr

from django.conf import settings

from accounts.models import Alias
from mail.models import Message, MessageCopy
from mail.outbound import create_outbound
from provider.domains import assert_sending_allowed

MAX_RAW_ATTACHMENTS = 25 * 1024 * 1024
PORTAL_TAG_NAME = "mailstead_outbound_id"


def authorized_from_addresses(mailbox) -> set[str]:
    addrs = {mailbox.address.lower()}
    for alias in Alias.objects.filter(mailbox=mailbox, is_active=True):
        addrs.add(alias.address.lower())
    return addrs


def _domain(addr: str) -> str:
    return addr.split("@", 1)[-1].lower()


def build_outbound_payload(
    mailbox,
    *,
    from_address: str,
    to: list[str],
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    subject: str,
    text: str,
    in_reply_to: str | None = None,
    references: str | None = None,
    reply_to: str | None = None,
    attachments: list[tuple[str, bytes, str]] | None = None,
    outbound_uuid: uuid.UUID | None = None,
) -> dict:
    from_addr = from_address.lower()
    if from_addr not in authorized_from_addresses(mailbox):
        raise ValueError("Unauthorized From address")
    assert_sending_allowed(_domain(from_address))
    outbound_uuid = outbound_uuid or uuid.uuid4()
    message_id = f"<{outbound_uuid}@{settings.MAIL_DOMAIN}>"
    headers = {"Message-ID": message_id}
    if in_reply_to:
        headers["In-Reply-To"] = in_reply_to
    if references:
        headers["References"] = references
    payload: dict = {
        "from": from_address,
        "to": to,
        "subject": subject,
        "text": text,
        "headers": headers,
        "tags": [{"name": PORTAL_TAG_NAME, "value": str(outbound_uuid)}],
    }
    if cc:
        payload["cc"] = cc
    if bcc:
        payload["bcc"] = bcc
    if reply_to:
        payload["reply_to"] = reply_to
    if attachments:
        encoded = []
        total_raw = 0
        for filename, data, content_type in attachments:
            total_raw += len(data)
            if total_raw > MAX_RAW_ATTACHMENTS:
                raise ValueError("Attachments too large")
            encoded.append(
                {
                    "filename": filename,
                    "content": base64.b64encode(data).decode("ascii"),
                    "content_type": content_type or "application/octet-stream",
                }
            )
        payload["attachments"] = encoded
    return payload


def reply_all_recipients(copy: MessageCopy, mailbox) -> tuple[list[str], list[str], list[str]]:
    """Return to, cc, bcc for reply-all; BCC only when present on sender copy."""
    msg = copy.message
    conversation = msg.conversation
    if conversation is not None and conversation.mailbox_id == copy.mailbox_id:
        return _reply_all_from_conversation(copy, mailbox)
    own = {mailbox.address.lower()}
    for alias in Alias.objects.filter(mailbox=mailbox, is_active=True):
        own.add(alias.address.lower())

    def add_unique(target: list[str], seen: set[str], raw: str) -> None:
        addr = parseaddr(raw)[1].lower() or raw.strip().lower()
        if not addr or addr in seen or addr in own:
            return
        seen.add(addr)
        target.append(addr)

    to_list: list[str] = []
    cc_list: list[str] = []
    seen: set[str] = set()
    add_unique(to_list, seen, msg.reply_to or msg.from_address)
    for field in (msg.to_index or "").split(","):
        if field.strip():
            add_unique(cc_list, seen, field)
    for field in (msg.cc_index or "").split(","):
        if field.strip():
            add_unique(cc_list, seen, field)
    bcc_list: list[str] = []
    if copy.bcc_snapshot:
        for field in copy.bcc_snapshot.split(","):
            if field.strip():
                add_unique(bcc_list, seen, field)
    return to_list, cc_list, bcc_list


def _reply_all_from_conversation(copy: MessageCopy, mailbox) -> tuple[list[str], list[str], list[str]]:
    """Active participants only. Dropped addresses stay off To, Cc, and Bcc."""
    from mail.conversations import bare_address
    from mail.threading import mailbox_from_addresses

    msg = copy.message
    own = mailbox_from_addresses(mailbox)
    inactive = set(msg.conversation.participants.filter(active=False).values_list("address", flat=True))

    def add_unique(target: list[str], seen: set[str], raw: str) -> None:
        addr = bare_address(raw)
        if not addr or addr in seen or addr in own or addr in inactive:
            return
        seen.add(addr)
        target.append(addr)

    to_list: list[str] = []
    cc_list: list[str] = []
    seen: set[str] = set()
    add_unique(to_list, seen, msg.reply_to or msg.from_address)
    for part in msg.conversation.participants.filter(active=True).order_by("id"):
        add_unique(cc_list, seen, part.address)
    if not to_list and cc_list:
        to_list.append(cc_list.pop(0))
    return to_list, cc_list, []


def send_compose(mailbox, **kwargs):
    outbound_id = kwargs.pop("outbound_uuid", None) or uuid.uuid4()
    payload = build_outbound_payload(mailbox, outbound_uuid=outbound_id, **kwargs)
    return create_outbound(mailbox, payload, outbound_uuid=outbound_id)
