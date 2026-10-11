import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from accounts.models import Mailbox
from mail.deletion import move_to_trash, purge_message_copy, restore_from_trash
from mail.models import Blob, Folder, Message, MessageCopy
from storage.models import MailboxStorage, StorageLedger


@pytest.mark.django_db
def test_move_to_trash_and_restore():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg = Message.objects.create(subject="s")
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX)
    move_to_trash(copy)
    copy.refresh_from_db()
    assert copy.folder == Folder.TRASH
    restore_from_trash(copy)
    copy.refresh_from_db()
    assert copy.folder == Folder.INBOX


@pytest.mark.django_db
def test_purge_releases_storage():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test", quota_bytes=10_000)
    StorageLedger.objects.create(pk=1, email_consumed_bytes=500)
    MailboxStorage.objects.create(mailbox=mb, charged_bytes=500)
    blob = Blob.objects.create(sha256="a" * 64, size_bytes=500, path="/tmp/x")
    msg = Message.objects.create(subject="s", blob=blob)
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.TRASH)
    purge_message_copy(copy)
    assert not Message.objects.filter(pk=msg.pk).exists()
    ms = MailboxStorage.objects.get(mailbox=mb)
    assert ms.charged_bytes == 0
    ledger = StorageLedger.objects.get(pk=1)
    assert ledger.email_consumed_bytes == 0


@pytest.mark.django_db
def test_purge_only_from_trash_via_view():
    User = get_user_model()
    u1 = User.objects.create_user("u1", password="x")
    u2 = User.objects.create_user("u2", password="x")
    m1 = Mailbox.objects.create(user=u1, address="a@mail.test")
    m2 = Mailbox.objects.create(user=u2, address="b@mail.test")
    msg = Message.objects.create(subject="secret")
    copy = MessageCopy.objects.create(message=msg, mailbox=m1, folder=Folder.INBOX)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    resp = client.post(f"/mail/m/{copy.id}/purge/")
    assert resp.status_code == 404
    client.post("/accounts/login/", {"username": "u2", "password": "x"})
    resp = client.post(f"/mail/m/{copy.id}/purge/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_trash_link_moves_message():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg = Message.objects.create(subject="s")
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    client.get(f"/mail/m/{copy.id}/trash/")
    copy.refresh_from_db()
    assert copy.folder == Folder.TRASH
