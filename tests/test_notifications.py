import json
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from accounts.models import Mailbox
from jobs.models import Job
from mail.models import Folder, Message, MessageCopy
from notifications.models import PushSubscription
from notifications.push import build_declarative_payload, endpoint_allowed, load_vapid_private_key, push_configured
from notifications.scheduling import pop_pending_copy_ids, schedule_new_mail_push
from notifications.services import build_new_mail_payload


@pytest.mark.parametrize(
    "endpoint,ok",
    [
        ("https://web.push.apple.com/something", True),
        ("https://fcm.googleapis.com/fcm/send/abc", True),
        ("https://evil.com/push", False),
        ("http://web.push.apple.com/x", False),
    ],
)
def test_endpoint_allowlist(endpoint, ok):
    assert endpoint_allowed(endpoint) is ok


def test_vapid_keys_load_for_tests():
    assert load_vapid_private_key() is not None
    assert push_configured() is True


def test_declarative_payload_shape():
    payload = build_declarative_payload(
        title="T",
        body="B",
        navigate="https://example.com/mail/",
        badge=2,
    )
    assert payload["web_push"] == 8030
    assert payload["notification"]["navigate"] == "https://example.com/mail/"
    assert payload["notification"]["app_badge"] == "2"


@pytest.mark.django_db
def test_subscribe_requires_auth():
    client = Client()
    resp = client.post(
        reverse("notifications_subscribe"),
        data=json.dumps({"endpoint": "https://web.push.apple.com/x", "keys": {"p256dh": "a", "auth": "b"}}),
        content_type="application/json",
    )
    assert resp.status_code == 302


@pytest.mark.django_db
def test_subscribe_rejects_bad_endpoint(client=None):
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    client = Client()
    client.force_login(user)
    with mock.patch("notifications.views.push_configured", return_value=True):
        resp = client.post(
            reverse("notifications_subscribe"),
            data=json.dumps(
                {
                    "endpoint": "https://attacker.example/push",
                    "keys": {"p256dh": "x", "auth": "y"},
                }
            ),
            content_type="application/json",
        )
    assert resp.status_code == 400
    assert resp.json()["error"] == "endpoint_not_allowed"


@pytest.mark.django_db
def test_subscribe_saves_subscription():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    client = Client()
    client.force_login(user)
    endpoint = "https://web.push.apple.com/abc"
    with mock.patch("notifications.views.push_configured", return_value=True):
        resp = client.post(
            reverse("notifications_subscribe"),
            data=json.dumps(
                {
                    "endpoint": endpoint,
                    "keys": {"p256dh": "key", "auth": "auth"},
                }
            ),
            content_type="application/json",
        )
    assert resp.status_code == 200
    assert PushSubscription.objects.filter(user=user, endpoint=endpoint).exists()


@pytest.mark.django_db
def test_schedule_new_mail_push_enqueues_job():
    from django.core.cache import cache

    cache.clear()
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    schedule_new_mail_push(mb.id, 99)
    assert Job.objects.filter(kind="push_notify_mailbox").exists()
    assert pop_pending_copy_ids(mb.id) == [99]


@pytest.mark.django_db
def test_build_new_mail_payload_skips_read():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    msg = Message.objects.create(subject="Hi", from_address="s@x.com")
    copy = MessageCopy.objects.create(message=msg, mailbox=mb, folder=Folder.INBOX, is_unread=False)
    payload = build_new_mail_payload(user, mb, [copy.id])
    assert payload is None


@pytest.mark.django_db
def test_ingest_schedules_push_for_inbox():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    meta = {
        "from": "ext@other.com",
        "to": ["a@mail.test"],
        "raw": {"download_url": "http://example/raw"},
    }
    with mock.patch("mail.inbound.get_receiving_email", return_value=meta):
        with mock.patch("mail.inbound.download_raw", return_value=b"From: a\n\nhi"):
            from mail.inbound import ingest_inbound

            ingest_inbound("e-push", meta, notify=True)
    assert Job.objects.filter(kind="push_notify_mailbox").exists()


@pytest.mark.django_db
def test_ingest_reconcile_flag_skips_push():
    User = get_user_model()
    user = User.objects.create_user("u1", password="x")
    mb = Mailbox.objects.create(user=user, address="a@mail.test")
    meta = {
        "from": "ext@other.com",
        "to": ["a@mail.test"],
        "raw": {"download_url": "http://example/raw"},
    }
    with mock.patch("mail.inbound.get_receiving_email", return_value=meta):
        with mock.patch("mail.inbound.download_raw", return_value=b"From: a\n\nhi"):
            from mail.inbound import ingest_inbound

            ingest_inbound("e-nopush", meta, notify=False)
    assert not Job.objects.filter(kind="push_notify_mailbox").exists()
