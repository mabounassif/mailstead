import pytest
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory

from accounts.models import Mailbox
from mail.context_processors import mail_nav_counts
from mail.models import Folder, Message, MessageCopy


@pytest.mark.django_db
def test_mail_nav_counts_inbox_unread():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg1 = Message.objects.create(subject="a")
    msg2 = Message.objects.create(subject="b")
    MessageCopy.objects.create(message=msg1, mailbox=mb, folder=Folder.INBOX, is_unread=True)
    MessageCopy.objects.create(message=msg2, mailbox=mb, folder=Folder.INBOX, is_unread=False)
    MessageCopy.objects.create(
        message=Message.objects.create(subject="c"),
        mailbox=mb,
        folder=Folder.SENT,
        is_unread=True,
    )
    request = RequestFactory().get("/")
    request.user = user
    assert mail_nav_counts(request)["inbox_unread_count"] == 1


@pytest.mark.django_db
def test_inbox_nav_shows_unread_badge():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    MessageCopy.objects.create(
        message=Message.objects.create(subject="a"),
        mailbox=mb,
        folder=Folder.INBOX,
        is_unread=True,
    )
    client = Client()
    client.post("/accounts/login/", {"username": "u1", "password": "x"})
    resp = client.get("/mail/")
    assert resp.status_code == 200
    assert 'class="rail-btn__badge"' in resp.content.decode()
    assert ">1</span>" in resp.content.decode() or ">1<" in resp.content.decode()
