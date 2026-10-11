from unittest import mock

import pytest

from accounts.models import Alias, Mailbox
from django.contrib.auth import get_user_model

from mail.inbound import ingest_inbound
from mail.models import Folder, Message, MessageCopy, UnroutedMessage
from provider.resend_client import ResendError


@pytest.mark.django_db
def test_alias_routing():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="primary@mail.test")
    Alias.objects.create(mailbox=mb, address="alias@mail.test")
    meta = {
        "from": "ext@other.com",
        "to": ["alias@mail.test"],
        "raw": {"download_url": "http://example/raw"},
    }
    with mock.patch("mail.inbound.get_receiving_email", return_value=meta):
        with mock.patch("mail.inbound.download_raw", return_value=b"From: a\n\nhi"):
            ingest_inbound("e-alias", meta)
    assert MessageCopy.objects.filter(mailbox=mb, folder=Folder.INBOX).exists()


@pytest.mark.django_db
def test_unknown_recipient_quarantine():
    meta = {"from": "x@y.com", "to": ["nobody@mail.test"], "raw": {"download_url": "http://x"}}
    with mock.patch("mail.inbound.get_receiving_email", return_value=meta):
        with mock.patch("mail.inbound.download_raw", return_value=b"body"):
            ingest_inbound("e-unknown", meta)
    assert UnroutedMessage.objects.filter(resend_email_id="e-unknown").exists()


@pytest.mark.django_db
def test_email_above_quota_metadata_only():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    webhook = {"to": ["a@mail.test"], "from": "s@x.com", "subject": "blocked"}
    with mock.patch(
        "mail.inbound.get_receiving_email",
        side_effect=ResendError("email_above_quota", error_type="email_above_quota"),
    ):
        ingest_inbound("e-quota", webhook)
    msg = Message.objects.get(resend_email_id="e-quota")
    assert msg.unretrievable
    assert MessageCopy.objects.filter(mailbox=mb).exists()


@pytest.mark.django_db
def test_oversize_download():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    Mailbox.objects.create(user=user, address="a@mail.test")
    meta = {"from": "a@b.com", "to": ["a@mail.test"], "raw": {"download_url": "http://x"}}
    with mock.patch("mail.inbound.get_receiving_email", return_value=meta):
        with mock.patch("mail.inbound.download_raw", side_effect=ResendError("too big", error_type="message_too_large")):
            with pytest.raises(ResendError):
                ingest_inbound("big", meta)


@pytest.mark.django_db
def test_ingest_idempotent():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    meta = {"from": "s@x.com", "to": ["a@mail.test"], "raw": {"download_url": "http://x"}}
    with mock.patch("mail.inbound.get_receiving_email", return_value=meta):
        with mock.patch("mail.inbound.download_raw", return_value=b"From: s\n\nx"):
            ingest_inbound("dup", meta)
            ingest_inbound("dup", meta)
    assert Message.objects.filter(resend_email_id="dup").count() == 1
