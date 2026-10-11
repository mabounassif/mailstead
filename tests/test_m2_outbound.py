from datetime import timedelta
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Mailbox
from mail.compose import reply_all_recipients
from mail.models import Folder, Message, MessageCopy, OutboundMessage
from mail.outbound import send_outbound
from provider.resend_client import ResendError


@pytest.mark.django_db
def test_outbound_idempotent_replay():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    ob = OutboundMessage.objects.create(
        mailbox=mb,
        payload_json={"from": "a@mail.test", "to": ["b@c.com"], "subject": "s", "text": "t"},
    )
    with mock.patch("mail.outbound.send_email", return_value={"id": "prov-1"}) as send_mock:
        send_outbound(str(ob.id))
        send_outbound(str(ob.id))
    assert send_mock.call_count == 1


@pytest.mark.django_db
def test_outbound_uncertain_after_window():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    ob = OutboundMessage.objects.create(
        mailbox=mb,
        payload_json={"from": "a@mail.test", "to": ["b@c.com"], "subject": "s", "text": "t"},
    )
    OutboundMessage.objects.filter(pk=ob.pk).update(created_at=timezone.now() - timedelta(hours=24))
    with mock.patch("mail.outbound.send_email", side_effect=ResendError("timeout", status=503)):
        send_outbound(str(ob.id))
    assert OutboundMessage.objects.get(pk=ob.pk).state == OutboundMessage.State.UNCERTAIN


@pytest.mark.django_db
def test_reply_all_dedupes_self():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="me@mail.test")
    msg = Message.objects.create(
        from_address="other@x.com",
        to_index="me@mail.test,other@x.com",
        cc_index="cc@x.com",
        reply_to="reply@x.com",
    )
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX)
    to_list, cc_list, _ = reply_all_recipients(copy, mb)
    assert "me@mail.test" not in to_list + cc_list
    assert "reply@x.com" in to_list
