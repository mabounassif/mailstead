import json
import re
from email.message import EmailMessage
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client

from accounts.models import Mailbox
from api.auth import hash_token
from api.models import ApiToken
from mail.blobs import write_blob
from mail.deletion import empty_trash
from mail.models import Folder, Message, MessageCopy, OutboundMessage, VaultEntry
from notifications.models import NativePushDevice
from notifications.services import deliver_to_user


@pytest.fixture(autouse=True)
def _allow_send(monkeypatch):
    monkeypatch.setattr("mail.compose.assert_sending_allowed", lambda domain: None)


def _client():
    return Client()


def _user(username, address, password="secret-pass"):
    user = get_user_model().objects.create_user(username, password=password)
    mailbox = Mailbox.objects.create(user=user, address=address)
    return user, mailbox


def _login(client, username="u1", password="secret-pass"):
    response = client.post(
        "/api/v1/auth/login/",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    token = response.json()["token"]
    assert token != hash_token(token)
    assert ApiToken.objects.filter(token_hash=hash_token(token), revoked_at__isnull=True).exists()
    return token


def _call(client, token, method, path, body=None):
    kwargs = {}
    if token:
        kwargs["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    if body is not None:
        kwargs["data"] = json.dumps(body)
        kwargs["content_type"] = "application/json"
    return getattr(client, method)(path, **kwargs)


@pytest.mark.django_db
def test_login_me_and_logout_round_trip():
    _user("u1", "a@mail.test")
    client = _client()
    token = _login(client)
    me = _call(client, token, "get", "/api/v1/me/")
    assert me.status_code == 200
    assert me.json()["mailbox"]["address"] == "a@mail.test"
    assert _call(client, token, "post", "/api/v1/auth/logout/").status_code == 200
    assert _call(client, token, "get", "/api/v1/me/").status_code == 401


@pytest.mark.django_db
def test_login_lockout_blocks_correct_password():
    _user("u1", "a@mail.test")
    client = _client()
    statuses = []
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login/",
            data=json.dumps({"username": "u1", "password": "wrong-password"}),
            content_type="application/json",
        )
        statuses.append(response.status_code)
    assert statuses[:4] == [401, 401, 401, 401]
    assert statuses[4] == 429
    locked = client.post(
        "/api/v1/auth/login/",
        data=json.dumps({"username": "u1", "password": "secret-pass"}),
        content_type="application/json",
    )
    assert locked.status_code == 429


@pytest.mark.django_db
def test_disabled_mailbox_cannot_log_in():
    _user_obj, mailbox = _user("u1", "a@mail.test")
    mailbox.state = Mailbox.State.DISABLED
    mailbox.save(update_fields=["state"])
    response = _client().post(
        "/api/v1/auth/login/",
        data=json.dumps({"username": "u1", "password": "secret-pass"}),
        content_type="application/json",
    )
    assert response.status_code == 403
    assert response.json()["error"] == "mailbox_disabled"


@pytest.mark.django_db
def test_password_reset_confirm_revokes_tokens():
    user, _mailbox = _user("u1", "a@mail.test")
    user.recovery_email = "recover@test"
    user.save(update_fields=["recovery_email"])
    client = _client()
    token = _login(client)
    requested = _call(client, None, "post", "/api/v1/auth/password-reset/", {"username": "u1"})
    assert requested.status_code == 200
    body = mail.outbox[-1].body
    match = re.search(r"mailstead://reset/([^/]+)/([^\s]+)", body)
    assert match
    uid, reset_token = match.group(1), match.group(2)
    rejected = _call(
        client,
        None,
        "post",
        "/api/v1/auth/password-reset/confirm/",
        {"uid": uid, "token": reset_token, "password": "short", "password_confirm": "short"},
    )
    assert rejected.status_code == 400
    confirmed = _call(
        client,
        None,
        "post",
        "/api/v1/auth/password-reset/confirm/",
        {
            "uid": uid,
            "token": reset_token,
            "password": "replacement-password",
            "password_confirm": "replacement-password",
        },
    )
    assert confirmed.status_code == 200
    assert _call(client, token, "get", "/api/v1/me/").status_code == 401
    assert _login(client, password="replacement-password")


@pytest.mark.django_db
def test_cross_mailbox_message_and_bcc_stay_private():
    _user("u1", "a@mail.test")
    _user("u2", "b@mail.test")
    client = _client()
    token1 = _login(client, "u1")
    token2 = _login(client, "u2")
    message = Message.objects.create(
        subject="Shared id",
        from_address="ada@example.com",
        body_text_index="Hello from Ada",
        to_index="a@mail.test",
    )
    copy1 = MessageCopy.objects.create(
        message=message,
        mailbox=Mailbox.objects.get(address="a@mail.test"),
        folder=Folder.INBOX,
        bcc_snapshot="hidden-bcc@example.com",
    )
    copy2 = MessageCopy.objects.create(
        message=message,
        mailbox=Mailbox.objects.get(address="b@mail.test"),
        folder=Folder.INBOX,
        bcc_snapshot="other-bcc@example.com",
    )
    own = _call(client, token1, "get", f"/api/v1/messages/{copy1.id}/")
    assert own.status_code == 200
    payload = own.json()
    assert payload["thread"][0]["bcc"] == "hidden-bcc@example.com"
    assert "other-bcc@example.com" not in own.content.decode()
    assert _call(client, token1, "get", f"/api/v1/messages/{copy2.id}/").status_code == 404
    assert _call(client, token2, "post", f"/api/v1/messages/{copy1.id}/trash/").status_code == 404
    copy1.refresh_from_db()
    assert copy1.folder == Folder.INBOX
    found = _call(client, token2, "get", "/api/v1/search/?q=hidden-bcc")
    assert found.json()["count"] == 0


@pytest.mark.django_db
def test_message_html_strips_script_and_remote_images_until_requested():
    _user("u1", "a@mail.test")
    client = _client()
    token = _login(client)
    mime = EmailMessage()
    mime["Subject"] = "Hi"
    mime.set_content("Plain hello")
    mime.add_alternative(
        '<p>Hello</p><script>alert(1)</script><img src="https://images.example/a.png" alt="pic">',
        subtype="html",
    )
    message = Message.objects.create(subject="Hi", from_address="ada@example.com", body_text_index="Plain hello")
    message.blob = write_blob(mime.as_bytes())
    message.save(update_fields=["blob"])
    copy = MessageCopy.objects.create(
        message=message,
        mailbox=Mailbox.objects.get(address="a@mail.test"),
        folder=Folder.INBOX,
        is_unread=True,
    )
    hidden = _call(client, token, "get", f"/api/v1/messages/{copy.id}/").json()
    html = hidden["thread"][0]["html"]
    assert "Hello" in html
    assert "alert(1)" not in html
    assert "https://images.example/a.png" not in html
    shown = _call(client, token, "get", f"/api/v1/messages/{copy.id}/?load_images=1").json()
    assert "https://images.example/a.png" in shown["thread"][0]["html"]
    copy.refresh_from_db()
    assert copy.is_unread is False


@pytest.mark.django_db
def test_send_reply_trash_and_search_use_mailbox_scope():
    _user_obj, mailbox = _user("u1", "a@mail.test")
    client = _client()
    token = _login(client)
    created = _call(
        client,
        token,
        "post",
        "/api/v1/conversations/",
        {"to": ["ada@example.com"], "subject": "Plans", "body": "Hello Ada"},
    )
    assert created.status_code == 201
    conversation_id = created.json()["conversation_id"]
    assert OutboundMessage.objects.filter(mailbox=mailbox, pk=created.json()["outbound_id"]).exists()
    continued = _call(
        client,
        token,
        "post",
        f"/api/v1/conversations/{conversation_id}/messages/",
        {"body": "Following up"},
    )
    assert continued.status_code == 201
    inbound = Message.objects.create(
        subject="Question",
        from_address="ada@example.com",
        reply_to="ada@example.com",
        body_text_index="A private question",
        to_index="a@mail.test",
    )
    copy = MessageCopy.objects.create(message=inbound, mailbox=mailbox, folder=Folder.INBOX)
    replied = _call(client, token, "post", f"/api/v1/messages/{copy.id}/reply/", {"body": "Answer"})
    assert replied.status_code == 201
    outbound = OutboundMessage.objects.get(pk=replied.json()["outbound_id"])
    assert outbound.payload_json["to"] == ["ada@example.com"]
    assert "bcc" not in replied.json()
    assert _call(client, token, "post", f"/api/v1/messages/{copy.id}/junk/").json()["folder"] == "junk"
    assert _call(client, token, "post", f"/api/v1/messages/{copy.id}/not-junk/").json()["folder"] == "inbox"
    trashed = _call(client, token, "post", f"/api/v1/messages/{copy.id}/trash/")
    assert trashed.json()["folder"] == "trash"
    listed = _call(client, token, "get", "/api/v1/folders/trash/")
    assert listed.json()["count"] == 1
    assert _call(client, token, "get", "/api/v1/search/?q=private+question").json()["count"] == 1
    assert _call(client, token, "post", f"/api/v1/messages/{copy.id}/restore/").status_code == 200
    copy.refresh_from_db()
    assert copy.folder == Folder.INBOX
    _call(client, token, "post", f"/api/v1/messages/{copy.id}/trash/")
    assert _call(client, token, "post", "/api/v1/trash/empty/").json()["deleted"] == 1
    assert empty_trash(mailbox) == 0


@pytest.mark.django_db
def test_vault_reveal_is_explicit_and_mailbox_scoped():
    _user("u1", "a@mail.test")
    _user("u2", "b@mail.test")
    client = _client()
    token1 = _login(client, "u1")
    token2 = _login(client, "u2")
    created = _call(
        client,
        token1,
        "post",
        "/api/v1/vault/",
        {"label": "Bank", "username": "ada", "secret": "vault-secret-value"},
    )
    assert created.status_code == 201
    entry_id = created.json()["id"]
    listed = _call(client, token1, "get", "/api/v1/vault/")
    assert "vault-secret-value" not in listed.content.decode()
    assert "secret" not in listed.json()["entries"][0]
    revealed = _call(client, token1, "post", f"/api/v1/vault/{entry_id}/reveal/")
    assert revealed.json()["secret"] == "vault-secret-value"
    stored = VaultEntry.objects.get(pk=entry_id)
    assert stored.secret != "vault-secret-value"
    assert _call(client, token2, "post", f"/api/v1/vault/{entry_id}/reveal/").status_code == 404
    assert _call(client, token2, "delete", f"/api/v1/vault/{entry_id}/").status_code == 404


@pytest.mark.django_db
def test_notification_preferences_and_expo_delivery(settings):
    user, _mailbox = _user("u1", "a@mail.test")
    client = _client()
    token = _login(client)
    updated = _call(
        client,
        token,
        "patch",
        "/api/v1/notifications/preferences/",
        {"enabled": False, "preview_mode": "subject"},
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert updated.json()["preview_mode"] == "subject"
    rejected = _call(
        client,
        token,
        "post",
        "/api/v1/notifications/expo/",
        {"token": "not-a-token"},
    )
    assert rejected.status_code == 400
    registered = _call(
        client,
        token,
        "post",
        "/api/v1/notifications/expo/",
        {"token": "ExponentPushToken[abcDEF123]", "label": "Phone"},
    )
    assert registered.status_code == 201
    settings.EXPO_ACCESS_TOKEN = "expo-test-token"
    payload = {"notification": {"title": "Hello", "body": "There", "navigate": "https://example/mail/"}}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"data":[{"status":"ok","id":"ticket"}]}'

    with mock.patch("notifications.expo.urllib.request.urlopen", return_value=_Response()) as urlopen:
        assert deliver_to_user(user, payload) == 1
    sent_body = json.loads(urlopen.call_args.args[0].data.decode())
    assert sent_body["to"] == "ExponentPushToken[abcDEF123]"
    assert "expo-test-token" not in json.dumps(sent_body)

    class _Revoked:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"data":[{"status":"error","details":{"error":"DeviceNotRegistered"}}]}'

    with mock.patch("notifications.expo.urllib.request.urlopen", return_value=_Revoked()):
        assert deliver_to_user(user, payload) == 0
    assert NativePushDevice.objects.get(user=user).revoked_at is not None
