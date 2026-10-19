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
    assert ">Drive<" in body
    assert ">Wallets<" not in body
    assert ">Junk<" not in body
    assert ">Inbox<" not in body
    assert 'class="workspace-list"' in body
    assert 'class="mail-idle"' in body
    assert "Contacts are listed under Messages." not in body
    assert ">Passwords<" not in body
    assert 'aria-label="Settings"' in body
    assert ">Contacts<" in body
    contacts_page = client.get("/mail/contacts/")
    contacts_body = contacts_page.content.decode()
    assert contacts_page.status_code == 200
    assert "Ada" in contacts_body
    assert "ada@example.com" in contacts_body
    assert ">Agents<" not in contacts_body
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
    assert "Subject:" in body
    assert 'placeholder="Set channel name"' in body
    assert 'name="subject"' in body
    assert "New channel" not in body
    posted = client.post("/mail/?new=1", {"body": "Hello there", "to": "", "subject": "Launch"})
    posted_body = posted.content.decode()
    assert posted.status_code == 200
    assert "Hello there" in posted_body
    assert "participant" in posted_body.lower()


@pytest.mark.django_db
def test_create_channel_with_title_participants_and_message():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    Mailbox.objects.create(user=user, address="a@mail.test")
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    with mock.patch("mail.views.send_compose") as send:
        sent = client.post(
            "/mail/?new=1",
            {
                "subject": "Launch",
                "to": "ada@example.com, bob@example.com",
                "body": "We are go.",
            },
        )
    assert sent.status_code == 302
    assert "channel=" in sent.url
    kwargs = send.call_args.kwargs
    assert kwargs["subject"] == "Launch"
    assert kwargs["to"] == ["ada@example.com", "bob@example.com"]
    from mail.models import Conversation

    assert Conversation.objects.filter(topic="Launch").exists()


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

    from mail.models import Conversation

    everything = client.get("/mail/?contact=ada@example.com")
    everything_body = everything.content.decode()
    assert "Direct messages" in everything_body
    assert "Channels" in everything_body
    assert "Roadmap" in everything_body
    assert "Invoice" in everything_body
    assert "All subjects" not in everything_body
    assert 'placeholder="Topic"' not in everything_body
    assert 'name="body"' in everything_body

    roadmap = Conversation.objects.get(topic_key="roadmap")
    invoice = client.get(f"/mail/?channel={roadmap.id}")
    invoice_body = invoice.content.decode()
    assert "Tuesday works." in invoice_body
    assert 'chat-bubble__text">Please pay.' not in invoice_body
    assert 'name="subject"' in invoice_body
    assert 'placeholder="Topic"' not in invoice_body

    with mock.patch("mail.views.send_compose") as send:
        sent = client.post(
            f"/mail/?channel={roadmap.id}",
            {"body": "See you then"},
        )
    assert sent.status_code == 302
    assert f"channel={roadmap.id}" in sent.url
    kwargs = send.call_args.kwargs
    assert kwargs["subject"] == "Re: Roadmap"
    assert kwargs["to"] == ["ada@example.com"]
    assert kwargs["in_reply_to"] == "<roadmap@example.com>"


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
