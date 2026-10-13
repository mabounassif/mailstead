from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from accounts.models import Mailbox
from mail.models import Folder, Message, MessageCopy


@pytest.mark.django_db
def test_message_page_has_inline_reply_form():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg = Message.objects.create(subject="Hello", from_address="sender@example.com")
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    resp = client.get(f"/mail/m/{copy.id}/")
    html = resp.content.decode()
    assert resp.status_code == 200
    assert 'id="thread-reply-form"' in html
    assert 'name="body"' in html
    assert "Open full compose" in html


@pytest.mark.django_db
def test_full_reply_compose_uses_main_panel():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg = Message.objects.create(subject="Hello", from_address="sender@example.com")
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    resp = client.get(f"/mail/m/{copy.id}/reply/?full=1")
    html = resp.content.decode()
    assert resp.status_code == 200
    assert "mail-pane--compose" in html
    assert 'id="body"' in html


@pytest.mark.django_db
def test_reply_get_redirects_to_inline_compose():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg = Message.objects.create(subject="Hello", from_address="sender@example.com")
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    resp = client.get(f"/mail/m/{copy.id}/reply/")
    assert resp.status_code == 302
    assert resp.url == f"/mail/m/{copy.id}/?compose=reply"


@pytest.mark.django_db
def test_inline_reply_post_queues_and_redirects():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg = Message.objects.create(subject="Hello", from_address="sender@example.com")
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX)
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    with mock.patch("mail.views.send_compose"):
        resp = client.post(f"/mail/m/{copy.id}/reply/", {"body": "Thanks!"})
    assert resp.status_code == 302
    assert resp.url == f"/mail/m/{copy.id}/"
