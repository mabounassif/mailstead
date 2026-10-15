from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from accounts.models import Mailbox
from mail.models import Folder, Message, MessageCopy, Project


@pytest.mark.django_db
def test_inbox_is_project_chats_and_hides_removed_folders():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mailbox = Mailbox.objects.create(user=user, address="a@mail.test")
    message = Message.objects.create(
        subject="Roadmap",
        from_address="Ada Lovelace <ada@example.com>",
        body_text_index="See you Tuesday.",
    )
    MessageCopy.objects.create(message=message, mailbox=mailbox, folder=Folder.INBOX, is_unread=True)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})

    inbox = client.get("/mail/")
    body = inbox.content.decode()
    assert inbox.status_code == 200
    assert "Ada" in body
    assert 'aria-label="Contacts"' in body
    assert 'placeholder="New group"' not in body
    assert ">Sent<" not in body
    assert ">Drafts<" not in body
    assert ">Archive<" not in body
    assert ">Messages<" in body
    assert ">Data<" in body
    assert ">Wallets<" not in body
    assert ">Junk<" not in body
    assert ">Inbox<" not in body
    assert 'class="workspace-list"' in body
    assert 'class="mail-idle"' in body
    assert "Contacts are listed under Messages." not in body
    assert ">Passwords<" not in body
    assert 'aria-label="Settings"' in body
    assert ">Agents<" in body
    assert not Project.objects.filter(mailbox=mailbox, name="General").exists()
    contact = client.get("/mail/?contact=ada@example.com")
    assert contact.status_code == 200
    assert "Ada" in contact.content.decode()
    contact_body = contact.content.decode()
    assert "Roadmap" in contact_body
    assert "See you Tuesday." in contact_body
    assert "chat-bubble" in contact_body
    project = Project.objects.create(mailbox=mailbox, name="Home")
    group = client.get(f"/mail/?project={project.id}")
    group_body = group.content.decode()
    assert "Home" in group_body
    assert ">Group<" in group_body or "Group" in group_body


@pytest.mark.django_db
def test_new_message_starts_with_unspecified_destination():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    Mailbox.objects.create(user=user, address="a@mail.test")
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    page = client.get("/mail/?new=1")
    body = page.content.decode()
    assert page.status_code == 200
    assert "New message" in body
    assert "Unspecified" in body
    posted = client.post("/mail/?new=1", {"body": "Hello there", "to": ""})
    posted_body = posted.content.decode()
    assert posted.status_code == 200
    assert "Hello there" in posted_body
    assert "unspecified" in posted_body.lower()


@pytest.mark.django_db
def test_contact_subject_filter_and_optional_subject():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mailbox = Mailbox.objects.create(user=user, address="a@mail.test")
    first = Message.objects.create(
        subject="Roadmap",
        from_address="Ada Lovelace <ada@example.com>",
        body_text_index="Tuesday works.",
        message_id="<roadmap@example.com>",
    )
    second = Message.objects.create(
        subject="Invoice",
        from_address="Ada Lovelace <ada@example.com>",
        body_text_index="Please pay.",
    )
    MessageCopy.objects.create(message=first, mailbox=mailbox, folder=Folder.INBOX)
    MessageCopy.objects.create(message=second, mailbox=mailbox, folder=Folder.INBOX)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})

    everything = client.get("/mail/?contact=ada@example.com")
    everything_body = everything.content.decode()
    assert "All subjects" in everything_body
    assert "Filter by subject" in everything_body
    assert 'aria-label="Back to messages"' in everything_body
    assert 'name="q"' in everything_body
    assert "Tuesday works." in everything_body
    assert "Please pay." in everything_body
    assert 'placeholder="Subject (optional)"' in everything_body
    assert 'name="body"' in everything_body

    invoice = client.get("/mail/?contact=ada@example.com&thread=invoice")
    invoice_body = invoice.content.decode()
    assert "Please pay." in invoice_body
    assert "Tuesday works." not in invoice_body
    assert 'value="Invoice"' in invoice_body

    with mock.patch("mail.views.send_compose") as send:
        sent = client.post(
            "/mail/?contact=ada@example.com&thread=roadmap",
            {"body": "See you then", "subject": "Re: Roadmap"},
        )
    assert sent.status_code == 302
    assert "thread=roadmap" in sent.url
    kwargs = send.call_args.kwargs
    assert kwargs["subject"] == "Re: Roadmap"
    assert kwargs["to"] == ["ada@example.com"]
    assert kwargs["in_reply_to"] == "<roadmap@example.com>"

    with mock.patch("mail.views.send_compose") as send:
        blank = client.post(
            "/mail/?contact=ada@example.com",
            {"body": "No subject line", "subject": ""},
        )
    assert blank.status_code == 302
    assert "thread=" not in blank.url
    assert send.call_args.kwargs["subject"] == ""
    assert "in_reply_to" not in send.call_args.kwargs


@pytest.mark.django_db
def test_removed_folders_redirect_home():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    Mailbox.objects.create(user=user, address="a@mail.test")
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    for folder in ("sent", "drafts", "archive"):
        response = client.get(f"/mail/f/{folder}/")
        assert response.status_code == 302
        assert response.url == "/mail/"
