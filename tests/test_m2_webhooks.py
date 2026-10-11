import json
from unittest import mock

import pytest
from django.test import Client

from jobs.models import Job
from mail.models import WebhookEvent


@pytest.mark.django_db
def test_webhook_invalid_signature():
    client = Client()
    body = json.dumps({"type": "email.received", "data": {"email_id": "e1"}}).encode()
    resp = client.post(
        "/hooks/resend",
        data=body,
        content_type="application/json",
        HTTP_SVIX_ID="msg_1",
        HTTP_SVIX_TIMESTAMP="1",
        HTTP_SVIX_SIGNATURE="v1,bad",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_webhook_raw_body_mutation_invalid():
    client = Client()
    body = json.dumps({"type": "email.received", "data": {"email_id": "e1"}}).encode()
    with mock.patch("provider.webhooks.verify_webhook", side_effect=Exception("bad sig")):
        resp = client.post(
            "/hooks/resend",
            data=body + b"tamper",
            content_type="application/json",
            HTTP_SVIX_ID="msg_tamper",
            HTTP_SVIX_TIMESTAMP="1",
            HTTP_SVIX_SIGNATURE="v1,x",
        )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_webhook_valid_dedupes():
    client = Client()
    body = {"type": "email.received", "data": {"email_id": "e1"}}
    raw = json.dumps(body).encode()

    with mock.patch("provider.webhooks.verify_webhook"):
        r1 = client.post(
            "/hooks/resend",
            data=raw,
            content_type="application/json",
            HTTP_SVIX_ID="msg_dup",
            HTTP_SVIX_TIMESTAMP="1",
            HTTP_SVIX_SIGNATURE="v1,x",
        )
        r2 = client.post(
            "/hooks/resend",
            data=raw,
            content_type="application/json",
            HTTP_SVIX_ID="msg_dup",
            HTTP_SVIX_TIMESTAMP="1",
            HTTP_SVIX_SIGNATURE="v1,x",
        )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert WebhookEvent.objects.count() == 1
    assert Job.objects.filter(kind="inbound").count() == 1


@pytest.mark.django_db
def test_webhook_verifies_raw_body():
    client = Client()
    body = json.dumps({"type": "email.received", "data": {"email_id": "e1"}}).encode()
    mutated = body + b" "
    with mock.patch("provider.webhooks.verify_webhook") as verify:
        verify.side_effect = lambda payload, headers, secret: (_ for _ in ()).throw(Exception("bad sig"))
        resp = client.post(
            "/hooks/resend",
            data=mutated,
            content_type="application/json",
            HTTP_SVIX_ID="msg_raw",
            HTTP_SVIX_TIMESTAMP="1",
            HTTP_SVIX_SIGNATURE="v1,x",
        )
    assert resp.status_code == 400
    assert verify.call_args[0][0] == mutated
