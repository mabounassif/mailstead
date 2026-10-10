from __future__ import annotations

import email
import logging
from email import policy

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from mail.blobs import write_blob
from mail.filtering import folder_for_inbound
from mail.models import Folder, Message, MessageAttachment, MessageCopy, UnroutedMessage
from mail.routing import resolve_recipients
from mail.storage_hook import reserve_inbound_bytes
from provider.resend_client import ResendError, get_receiving_email

logger = logging.getLogger(__name__)


def _max_bytes() -> int:
    return int(getattr(settings, "MAX_MESSAGE_BYTES", 30 * 1024 * 1024))


def download_raw(url: str) -> bytes:
    resp = requests.get(url, timeout=(5, 60), stream=True)
    resp.raise_for_status()
    chunks: list[bytes] = []
    total = 0
    for chunk in resp.iter_content(65536):
        if not chunk:
            continue
        total += len(chunk)
        if total > _max_bytes():
            raise ResendError("message too large", error_type="message_too_large")
        chunks.append(chunk)
    return b"".join(chunks)


def ingest_inbound(email_id: str, webhook_meta: dict | None = None) -> None:
    if Message.objects.filter(resend_email_id=email_id).exists():
        return

    meta = webhook_meta
    need_fetch = meta is None or not (meta.get("raw") or {}).get("download_url")
    if need_fetch:
        try:
            meta = get_receiving_email(email_id)
        except ResendError as exc:
            if "quota" in str(exc).lower() or getattr(exc, "error_type", "") == "email_above_quota":
                _record_unretrievable(email_id, webhook_meta or {}, "email_above_quota")
                return
            raise

    recipients = resolve_recipients(meta)
    if not recipients:
        UnroutedMessage.objects.get_or_create(
            resend_email_id=email_id,
            defaults={"envelope": meta},
        )
        return

    raw_info = meta.get("raw") or {}
    url = raw_info.get("download_url")
    if not url:
        raise ResendError("missing raw download_url")
    try:
        raw_bytes = download_raw(url)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code in (403, 410):
            meta = get_receiving_email(email_id)
            url = (meta.get("raw") or {}).get("download_url")
            if not url:
                raise
            raw_bytes = download_raw(url)
        else:
            raise

    api_attachments = meta.get("attachments") or []
    _validate_attachment_sizes(raw_bytes, api_attachments)

    primary = recipients[0]
    with reserve_inbound_bytes(primary, len(raw_bytes)):
        with transaction.atomic():
            blob = write_blob(raw_bytes)
            msg = Message.objects.create(
                blob=blob,
                resend_email_id=email_id,
                message_id=meta.get("message_id") or "",
                subject=meta.get("subject") or "",
                from_address=_from(meta),
                to_index=_join_addresses(meta.get("to")),
                cc_index=_join_addresses(meta.get("cc")),
                reply_to=_reply_to(meta),
                sent_at=timezone.now(),
                auth_spf=(meta.get("authentication") or {}).get("spf") or "",
                auth_dkim=(meta.get("authentication") or {}).get("dkim") or "",
                auth_dmarc=(meta.get("authentication") or {}).get("dmarc") or "",
                body_text_index=_body_index(raw_bytes),
                archived=True,
            )
            _store_attachment_metadata(msg, api_attachments)
            bcc_list = meta.get("bcc") or []
            bcc_str = ",".join(_bare(x) for x in bcc_list)
            for mb in recipients:
                folder = folder_for_inbound(mb, meta)
                MessageCopy.objects.create(
                    message=msg,
                    mailbox=mb,
                    folder=folder,
                    bcc_snapshot=bcc_str if _is_sender_copy(mb, meta) else "",
                )


def _bare(value) -> str:
    if isinstance(value, dict):
        return value.get("email") or value.get("address") or ""
    s = str(value)
    if "<" in s and ">" in s:
        return s.split("<", 1)[1].split(">", 1)[0].strip()
    return s.strip()


def _join_addresses(values) -> str:
    if not values:
        return ""
    return ",".join(_bare(v) for v in values)


def _reply_to(meta) -> str:
    rt = meta.get("reply_to")
    if isinstance(rt, list) and rt:
        return _bare(rt[0])
    if isinstance(rt, str):
        return rt
    return ""


def _validate_attachment_sizes(raw: bytes, api_attachments: list) -> None:
    if not api_attachments:
        return
    parsed = email.message_from_bytes(raw, policy=policy.default)
    total = 0
    for att in api_attachments:
        size = int(att.get("size") or 0)
        total += size
    if total > _max_bytes():
        raise ResendError("attachments exceed cap")


def _store_attachment_metadata(msg: Message, api_attachments: list) -> None:
    for att in api_attachments:
        MessageAttachment.objects.create(
            message=msg,
            provider_attachment_id=att.get("id") or "",
            filename=att.get("filename") or "attachment",
            content_type=att.get("content_type") or "",
            size_bytes=int(att.get("size") or 0),
        )


def _is_sender_copy(mailbox, meta) -> bool:
    return mailbox.address.lower() == _from(meta).lower()


def _from(meta) -> str:
    f = meta.get("from")
    if isinstance(f, str):
        return _bare(f)
    return ""


def _body_index(raw: bytes) -> str:
    try:
        msg = email.message_from_bytes(raw, policy=policy.default)
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return (part.get_content() or "")[:5000]
        return (msg.get_content() or "")[:5000]
    except Exception:
        return ""


def _record_unretrievable(email_id: str, meta: dict, reason: str) -> None:
    recipients = resolve_recipients(meta)
    with transaction.atomic():
        msg, _ = Message.objects.get_or_create(
            resend_email_id=email_id,
            defaults={
                "unretrievable": True,
                "unretrievable_reason": reason,
                "archived": False,
                "subject": meta.get("subject") or "",
                "from_address": _from(meta),
            },
        )
        for mb in recipients:
            MessageCopy.objects.get_or_create(
                message=msg,
                mailbox=mb,
                folder=Folder.INBOX,
                defaults={"is_unread": True},
            )
