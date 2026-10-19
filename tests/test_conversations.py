from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from accounts.models import Mailbox
from mail.conversations import assign_inbound_message
from mail.models import (
    Conversation,
    ConversationEvent,
    ConversationParticipant,
    Folder,
    Message,
    MessageCopy,
    OutboundMessage,
)
from mail.threading import thread_copies


@pytest.fixture(autouse=True)
def _allow_send(monkeypatch):
    monkeypatch.setattr("mail.compose.assert_sending_allowed", lambda domain: None)


def _login(address="me@mail.test"):
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mailbox = Mailbox.objects.create(user=user, address=address)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    return client, mailbox


@pytest.mark.django_db
def test_new_topic_does_not_hijack_existing_thread():
    client, mailbox = _login()
    message = Message.objects.create(
        subject="Budget",
        from_address="ada@example.com",
        message_id="<budget@example.com>",
        body_text_index="Numbers",
    )
    MessageCopy.objects.create(message=message, mailbox=mailbox, folder=Folder.INBOX)
    with mock.patch("mail.views.send_compose") as send:
        sent = client.post(
            "/mail/?contact=ada@example.com",
            {"body": "Different matter", "subject": "Plans"},
        )
    assert sent.status_code == 302
    assert "in_reply_to" not in send.call_args.kwargs
    assert send.call_args.kwargs["subject"] == "Plans"
    plans = Conversation.objects.get(topic_key="plans")
    budget = Conversation.objects.get(topic_key="budget")
    assert plans.id != budget.id
    assert plans.spun_from_id is None


@pytest.mark.django_db
def test_same_topic_replies_inside_conversation():
    client, mailbox = _login()
    message = Message.objects.create(
        subject="Budget",
        from_address="ada@example.com",
        message_id="<budget@example.com>",
        body_text_index="Numbers",
    )
    MessageCopy.objects.create(message=message, mailbox=mailbox, folder=Folder.INBOX)
    with mock.patch("mail.views.send_compose") as send:
        sent = client.post(
            "/mail/?contact=ada@example.com&thread=budget",
            {"body": "Updated", "subject": "Budget"},
        )
    assert sent.status_code == 302
    assert send.call_args.kwargs["in_reply_to"] == "<budget@example.com>"
    assert send.call_args.kwargs["subject"] == "Re: Budget"
    assert Conversation.objects.filter(topic_key="budget").count() == 1


@pytest.mark.django_db
def test_spinoff_starts_a_new_database_thread():
    client, mailbox = _login()
    message = Message.objects.create(
        subject="Budget",
        from_address="ada@example.com",
        message_id="<budget@example.com>",
        body_text_index="Numbers",
    )
    MessageCopy.objects.create(message=message, mailbox=mailbox, folder=Folder.INBOX)
    first = client.post(
        "/mail/?contact=ada@example.com&thread=budget",
        {"body": "Splitting this", "subject": "Plans"},
    )
    assert first.status_code == 302
    spun = Conversation.objects.get(topic_key="plans")
    assert spun.spun_from.topic_key == "budget"
    payload = OutboundMessage.objects.get().payload_json
    assert payload["subject"] == "Plans (was: Budget)"
    assert payload["headers"]["In-Reply-To"] == "<budget@example.com>"

    second = client.post(
        "/mail/?contact=ada@example.com&thread=plans",
        {"body": "Only the new topic", "subject": "Plans"},
    )
    assert second.status_code == 302
    follow = OutboundMessage.objects.order_by("created_at").last()
    assert follow.payload_json["subject"] == "Re: Plans"
    assert follow.payload_json["headers"]["In-Reply-To"] != "<budget@example.com>"
    anchor = MessageCopy.objects.get(message__portal_tag=str(follow.idempotency_key))
    copied = thread_copies(anchor)
    assert all(item.message.conversation_id == spun.id for item in copied)
    assert message.id not in {item.message_id for item in copied}


@pytest.mark.django_db
def test_inbound_cc_addition_is_logged_once():
    _client, mailbox = _login()
    first = Message.objects.create(
        subject="Budget",
        from_address="ada@example.com",
        to_index="me@mail.test",
        cc_index="bob@example.com",
        message_id="<budget@example.com>",
    )
    first_copy = MessageCopy.objects.create(message=first, mailbox=mailbox, folder=Folder.INBOX)
    assign_inbound_message(first, mailbox, first_copy)
    assert not ConversationEvent.objects.filter(kind=ConversationEvent.Kind.ADDED).exists()

    second = Message.objects.create(
        subject="Re: Budget",
        from_address="ada@example.com",
        to_index="me@mail.test",
        cc_index="bob@example.com,cara@example.com",
        message_id="<two@example.com>",
        in_reply_to="<budget@example.com>",
    )
    assign_inbound_message(second, mailbox, MessageCopy.objects.create(message=second, mailbox=mailbox, folder=Folder.INBOX))
    assert ConversationParticipant.objects.filter(address="cara@example.com", active=True).exists()
    assert ConversationEvent.objects.filter(address="cara@example.com").count() == 1

    third = Message.objects.create(
        subject="Re: Budget",
        from_address="ada@example.com",
        to_index="me@mail.test",
        cc_index="bob@example.com,cara@example.com",
        message_id="<three@example.com>",
        in_reply_to="<two@example.com>",
    )
    assign_inbound_message(third, mailbox, MessageCopy.objects.create(message=third, mailbox=mailbox, folder=Folder.INBOX))
    assert ConversationEvent.objects.filter(address="cara@example.com").count() == 1


@pytest.mark.django_db
def test_drop_participant_is_bcc_once_then_removed():
    client, mailbox = _login()
    message = Message.objects.create(
        subject="Budget",
        from_address="ada@example.com",
        to_index="me@mail.test",
        cc_index="bob@example.com",
        message_id="<budget@example.com>",
        body_text_index="Numbers",
    )
    MessageCopy.objects.create(message=message, mailbox=mailbox, folder=Folder.INBOX)
    dropped = client.post(
        "/mail/?contact=ada@example.com&thread=budget",
        {"body": "Taking Bob off", "subject": "Budget", "drop": "bob@example.com"},
    )
    assert dropped.status_code == 302
    first = OutboundMessage.objects.get().payload_json
    assert first["bcc"] == ["bob@example.com"]
    assert "bob@example.com" not in first.get("cc", [])
    assert first["text"].endswith("-Bcc @bob (moving to BCC to save inbox)")
    part = ConversationParticipant.objects.get(address="bob@example.com")
    assert not part.active

    again = client.post(
        "/mail/?contact=ada@example.com&thread=budget",
        {"body": "Just us", "subject": "Budget"},
    )
    assert again.status_code == 302
    second = OutboundMessage.objects.order_by("created_at").last().payload_json
    assert "bcc" not in second
    assert "bob@example.com" not in second.get("cc", [])
    assert "bob@example.com" not in second["to"]


@pytest.mark.django_db
def test_mention_adds_cc_on_later_send():
    client, mailbox = _login()
    message = Message.objects.create(
        subject="Budget",
        from_address="ada@example.com",
        message_id="<budget@example.com>",
    )
    MessageCopy.objects.create(message=message, mailbox=mailbox, folder=Folder.INBOX)
    client.post(
        "/mail/?contact=ada@example.com&thread=budget",
        {"body": "Looping @cara@example.com in", "subject": "Budget"},
    )
    first = OutboundMessage.objects.get().payload_json
    assert first["cc"] == ["cara@example.com"]
    assert ConversationEvent.objects.filter(address="cara@example.com", kind=ConversationEvent.Kind.ADDED).exists()
    client.post(
        "/mail/?contact=ada@example.com&thread=budget",
        {"body": "Following up", "subject": "Budget"},
    )
    second = OutboundMessage.objects.order_by("created_at").last().payload_json
    assert second["cc"] == ["cara@example.com"]
    assert "bcc" not in second
