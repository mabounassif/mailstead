from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from accounts.models import Mailbox
from mail.models import Folder, Message, MessageCopy
from mail.threading import normalized_subject, thread_copies


@pytest.mark.django_db
def test_normalized_subject_strips_replies():
    assert normalized_subject("Re: Hello") == "hello"
    assert normalized_subject("RE: Fwd: Hi") == "hi"
    assert normalized_subject("Re: Plans (was: Budget)") == "plans"
    assert normalized_subject("New (was: Old (was: Older))") == "new"


@pytest.mark.django_db
def test_thread_links_inbound_and_sent_by_message_id():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="me@mail.test")
    t0 = timezone.now() - timedelta(hours=2)
    t1 = timezone.now() - timedelta(hours=1)
    inbound = Message.objects.create(
        subject="Project",
        from_address="them@example.com",
        message_id="<inbound@example.com>",
        sent_at=t0,
        body_text_index="First",
    )
    inbound_copy = MessageCopy.objects.create(message=inbound, mailbox=mb, folder=Folder.INBOX)
    sent = Message.objects.create(
        subject="Re: Project",
        from_address="me@mail.test",
        to_index="them@example.com",
        message_id="<sent@mail.test>",
        in_reply_to="<inbound@example.com>",
        references_text="<inbound@example.com>",
        sent_at=t1,
        body_text_index="Reply",
    )
    MessageCopy.objects.create(message=sent, mailbox=mb, folder=Folder.SENT, is_unread=False)

    copies = thread_copies(inbound_copy)
    assert [c.folder for c in copies] == [Folder.INBOX, Folder.SENT]

    copies_from_sent = thread_copies(MessageCopy.objects.get(message=sent))
    assert len(copies_from_sent) == 2


@pytest.mark.django_db
def test_thread_merges_same_subject_when_headers_miss_a_message():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="me@mail.test")
    t0 = timezone.now() - timedelta(hours=2)
    t1 = timezone.now() - timedelta(hours=1)
    t2 = timezone.now()
    first = Message.objects.create(
        subject="Hi",
        from_address="me@mail.test",
        sent_at=t0,
        body_text_index="This is a test",
    )
    MessageCopy.objects.create(message=first, mailbox=mb, folder=Folder.SENT)
    second = Message.objects.create(
        subject="Re: Hi",
        from_address="other@example.com",
        message_id="<b@example.com>",
        in_reply_to="<missing@example.com>",
        sent_at=t1,
        body_text_index="It works",
    )
    second_copy = MessageCopy.objects.create(message=second, mailbox=mb, folder=Folder.INBOX)
    third = Message.objects.create(
        subject="Re: Hi",
        from_address="me@mail.test",
        sent_at=t2,
        body_text_index="Awesome",
    )
    MessageCopy.objects.create(message=third, mailbox=mb, folder=Folder.SENT)

    copies = thread_copies(second_copy)
    assert len(copies) == 3


@pytest.mark.django_db
def test_message_page_renders_intertwined_thread():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="me@mail.test")
    inbound = Message.objects.create(
        subject="Chat",
        from_address="them@example.com",
        message_id="<a@x.com>",
        body_text_index="Hi",
    )
    inbound_copy = MessageCopy.objects.create(message=inbound, mailbox=mb, folder=Folder.INBOX)
    sent = Message.objects.create(
        subject="Re: Chat",
        from_address="me@mail.test",
        to_index="them@example.com",
        message_id="<b@x.com>",
        in_reply_to="<a@x.com>",
        body_text_index="Hello back",
    )
    MessageCopy.objects.create(message=sent, mailbox=mb, folder=Folder.SENT, is_unread=False)

    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    html = client.get(f"/mail/m/{inbound_copy.id}/").content.decode()
    assert "thread-message--outgoing" in html
    assert "Hi" in html
    assert "Hello back" in html
    assert "2 messages" in html
    assert "chat-bubble" in html
    assert "thread-message--last" in html
