from __future__ import annotations

from contextlib import contextmanager
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from storage.capacity import effective_email_capacity
from storage.models import MailboxStorage, Reservation, StorageLedger


def _ledger() -> StorageLedger:
    row, _ = StorageLedger.objects.get_or_create(pk=1)
    return row


def _mailbox_storage(mailbox) -> MailboxStorage:
    row, _ = MailboxStorage.objects.get_or_create(mailbox=mailbox)
    return row


def _update_mailbox_state(ms: MailboxStorage) -> None:
    quota = ms.mailbox.quota_bytes
    if quota <= 0:
        ms.state = MailboxStorage.State.OK
        return
    pct = (ms.charged_bytes / quota) * 100
    if ms.mailbox.over_quota or ms.charged_bytes > quota:
        ms.state = MailboxStorage.State.OVER_QUOTA
    elif pct >= 100:
        ms.state = MailboxStorage.State.FULL
    elif pct >= 90:
        ms.state = MailboxStorage.State.WARN90
    elif pct >= 80:
        ms.state = MailboxStorage.State.WARN80
    else:
        ms.state = MailboxStorage.State.OK
    ms.save(update_fields=["state", "updated_at"])


@contextmanager
def reserve_inbound_bytes(mailbox, nbytes: int):
    expires = timezone.now() + timedelta(minutes=30)
    with transaction.atomic():
        ledger = StorageLedger.objects.select_for_update().get(pk=_ledger().pk)
        ms = MailboxStorage.objects.select_for_update().get(pk=_mailbox_storage(mailbox).pk)
        if ms.charged_bytes + nbytes > mailbox.quota_bytes:
            raise StorageFullError("mailbox quota")
        if nbytes > effective_email_capacity(ledger):
            raise StorageFullError("global capacity")
        reservation = Reservation.objects.create(
            mailbox=mailbox,
            bytes=nbytes,
            purpose="inbound",
            expires_at=expires,
        )
        ledger.reserved_bytes += nbytes
        ledger.save(update_fields=["reserved_bytes"])
    try:
        yield reservation
        commit_reservation(reservation.id)
    except Exception:
        release_reservation(reservation.id)
        raise


class StorageFullError(Exception):
    pass


def commit_reservation(reservation_id) -> None:
    with transaction.atomic():
        res = Reservation.objects.select_for_update().get(pk=reservation_id, state=Reservation.State.HELD)
        ledger = StorageLedger.objects.select_for_update().get(pk=1)
        ms = MailboxStorage.objects.select_for_update().get(mailbox=res.mailbox)
        ledger.reserved_bytes -= res.bytes
        ledger.email_consumed_bytes += res.bytes
        ledger.save(update_fields=["reserved_bytes", "email_consumed_bytes"])
        ms.charged_bytes += res.bytes
        ms.save(update_fields=["charged_bytes", "updated_at"])
        res.state = Reservation.State.COMMITTED
        res.save(update_fields=["state"])
        _update_mailbox_state(ms)


def release_reservation(reservation_id) -> None:
    with transaction.atomic():
        res = Reservation.objects.select_for_update().filter(pk=reservation_id, state=Reservation.State.HELD).first()
        if not res:
            return
        ledger = StorageLedger.objects.select_for_update().get(pk=1)
        ledger.reserved_bytes = max(0, ledger.reserved_bytes - res.bytes)
        ledger.save(update_fields=["reserved_bytes"])
        res.state = Reservation.State.RELEASED
        res.save(update_fields=["state"])


def sweep_expired_reservations() -> int:
    now = timezone.now()
    count = 0
    for res in Reservation.objects.filter(state=Reservation.State.HELD, expires_at__lt=now):
        release_reservation(res.id)
        count += 1
    return count


def apply_quota_reduction(mailbox) -> None:
    ms = _mailbox_storage(mailbox)
    if ms.charged_bytes > mailbox.quota_bytes:
        mailbox.over_quota = True
        mailbox.save(update_fields=["over_quota"])
    _update_mailbox_state(ms)


def release_retained_bytes(mailbox, nbytes: int) -> None:
    if nbytes <= 0:
        return
    with transaction.atomic():
        ledger = StorageLedger.objects.select_for_update().get(pk=_ledger().pk)
        ms = MailboxStorage.objects.select_for_update().get(pk=_mailbox_storage(mailbox).pk)
        ledger.email_consumed_bytes = max(0, ledger.email_consumed_bytes - nbytes)
        ms.charged_bytes = max(0, ms.charged_bytes - nbytes)
        ledger.save(update_fields=["email_consumed_bytes"])
        ms.save(update_fields=["charged_bytes", "updated_at"])
        if mailbox.over_quota and ms.charged_bytes <= mailbox.quota_bytes:
            mailbox.over_quota = False
            mailbox.save(update_fields=["over_quota"])
        _update_mailbox_state(ms)
