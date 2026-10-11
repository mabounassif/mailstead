import pytest
from django.contrib.auth import get_user_model

from accounts.models import Mailbox
from storage.models import MailboxStorage, Reservation, StorageLedger
from storage.services import (
    StorageFullError,
    apply_quota_reduction,
    commit_reservation,
    release_reservation,
    reserve_inbound_bytes,
)


@pytest.mark.django_db
def test_reserve_and_commit():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@test", quota_bytes=10_000)
    StorageLedger.objects.create(pk=1)
    with reserve_inbound_bytes(mb, 1000):
        pass
    ms = MailboxStorage.objects.get(mailbox=mb)
    assert ms.charged_bytes == 1000


@pytest.mark.django_db
def test_reserve_rollback_on_exception():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@test", quota_bytes=10_000)
    StorageLedger.objects.create(pk=1)
    with pytest.raises(RuntimeError):
        with reserve_inbound_bytes(mb, 500):
            raise RuntimeError("fail")
    ledger = StorageLedger.objects.get(pk=1)
    assert ledger.reserved_bytes == 0


@pytest.mark.django_db
def test_quota_exceeded_blocks_reserve():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@test", quota_bytes=100)
    StorageLedger.objects.create(pk=1)
    MailboxStorage.objects.create(mailbox=mb, charged_bytes=90)
    with pytest.raises(StorageFullError):
        with reserve_inbound_bytes(mb, 50):
            pass


@pytest.mark.django_db
def test_quota_reduction_over_quota_flag():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@test", quota_bytes=100)
    MailboxStorage.objects.create(mailbox=mb, charged_bytes=200)
    mb.quota_bytes = 50
    mb.save()
    apply_quota_reduction(mb)
    assert mb.over_quota
