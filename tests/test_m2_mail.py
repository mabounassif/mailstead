import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from accounts.models import Mailbox
from mail.html_safety import sanitize_html, wrap_html_for_iframe
from mail.models import Folder, Message, MessageCopy


@pytest.mark.django_db
def test_wrap_html_for_iframe_sets_base_typography():
    wrapped = wrap_html_for_iframe("<html><body><p>Hi</p><blockquote>quote</blockquote></body></html>")
    assert "font-family: system-ui" in wrapped
    assert "<p>Hi</p>" in wrapped
    assert "<blockquote>quote</blockquote>" in wrapped
    assert "<html><body><p>Hi</p>" not in wrapped.replace(" ", "")


def test_html_sanitizer_strips_script():
    raw = '<p>Hi</p><script>alert(1)</script><img src="https://evil.com/x.png">'
    out = sanitize_html(raw)
    assert "<script>" not in out
    assert "blocked" in out.lower()


@pytest.mark.django_db
def test_cross_mailbox_message_is_404():
    User = get_user_model()
    u1 = User.objects.create_user("u1", password="x")
    u2 = User.objects.create_user("u2", password="x")
    m1 = Mailbox.objects.create(user=u1, address="a@mail.test")
    m2 = Mailbox.objects.create(user=u2, address="b@mail.test")
    msg = Message.objects.create(subject="secret", body_text_index="secret body")
    copy = MessageCopy.objects.create(message=msg, mailbox=m1, folder=Folder.INBOX)
    client = Client()
    client.post("/accounts/login/", {"username": "u2", "password": "x"})
    resp = client.get(f"/mail/m/{copy.id}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_bcc_not_on_non_sender_copy():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg = Message.objects.create(subject="s")
    sender_copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.SENT, bcc_snapshot="bcc@x")
    recipient_copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX, bcc_snapshot="")
    assert sender_copy.bcc_snapshot
    assert not recipient_copy.bcc_snapshot
