from __future__ import annotations

from django.db import transaction

from accounts.models import Mailbox
from mail.models import Folder, Message, MessageCopy
from storage.services import release_retained_bytes


def retained_bytes_for_message(message: Message) -> int:
    total = 0
    seen: set[str] = set()
    if message.blob_id:
        blob = message.blob
        if blob.sha256 not in seen:
            seen.add(blob.sha256)
            total += blob.size_bytes
    for att in message.attachments.select_related("blob"):
        if att.blob_id and att.blob.sha256 not in seen:
            seen.add(att.blob.sha256)
            total += att.blob.size_bytes
    return total


def _charging_mailbox_id(message: Message) -> int | None:
    return message.copies.order_by("id").values_list("mailbox_id", flat=True).first()


def move_to_trash(copy: MessageCopy) -> None:
    if copy.folder == Folder.TRASH:
        return
    existing = MessageCopy.objects.filter(
        message=copy.message,
        mailbox=copy.mailbox,
        folder=Folder.TRASH,
    ).first()
    if existing:
        copy.delete()
        return
    copy.folder = Folder.TRASH
    copy.save(update_fields=["folder"])


def restore_from_trash(copy: MessageCopy, target: str = Folder.INBOX) -> None:
    if copy.folder != Folder.TRASH:
        return
    if target not in Folder.values or target == Folder.TRASH:
        target = Folder.INBOX
    existing = MessageCopy.objects.filter(
        message=copy.message,
        mailbox=copy.mailbox,
        folder=target,
    ).first()
    if existing:
        copy.delete()
        return
    copy.folder = target
    copy.save(update_fields=["folder"])


def purge_message_copy(copy: MessageCopy) -> None:
    message = copy.message
    charging_mailbox_id = _charging_mailbox_id(message)
    with transaction.atomic():
        copy.delete()
        if message.copies.exists():
            return
        nbytes = retained_bytes_for_message(message)
        message.delete()
        if nbytes and charging_mailbox_id:
            release_retained_bytes(Mailbox.objects.get(pk=charging_mailbox_id), nbytes)


def empty_trash(mailbox: Mailbox) -> int:
    copies = list(MessageCopy.objects.filter(mailbox=mailbox, folder=Folder.TRASH).select_related("message"))
    count = 0
    for copy in copies:
        purge_message_copy(copy)
        count += 1
    return count
