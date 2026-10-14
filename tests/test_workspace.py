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
    assert ">Sent<" not in body
    assert ">Drafts<" not in body
    assert ">Archive<" not in body
    assert ">Messages<" in body
    assert ">Data<" in body
    assert ">Wallets<" in body
    assert ">Inbox<" not in body
    assert 'class="workspace-list"' in body
    assert ">Passwords<" in body
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
