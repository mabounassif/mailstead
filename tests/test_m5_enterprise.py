from unittest import mock

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from enterprise.entitlements import cache_entitlement, installation_id, licensed_capability
from enterprise.spam import HostedClassifier, LocalRulesClassifier, run_scan
from mail.models import Message


def _keypair():
    private = Ed25519PrivateKey.generate()
    public_pem = private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private, public_pem


@pytest.mark.django_db
def test_local_classifier():
    msg = Message.objects.create(body_text_index="definitely SPAM here")
    v = LocalRulesClassifier().classify(msg)
    assert v.verdict == "spam"


@pytest.mark.django_db
def test_entitlement_verify_and_capability(settings):
    private, public_pem = _keypair()
    settings.ENTERPRISE_PUBLIC_KEYS = [public_pem]
    iid = installation_id()
    token = jwt.encode(
        {"iss": "test", "aud": iid, "exp": 9999999999, "capabilities": ["spam_filtering"]},
        private,
        algorithm="EdDSA",
    )
    cache_entitlement(token)
    assert licensed_capability("spam_filtering")


@pytest.mark.django_db
def test_hosted_classifier_payload_allowlist(settings):
    private, public_pem = _keypair()
    settings.ENTERPRISE_PUBLIC_KEYS = [public_pem]
    from enterprise.models import License

    License.objects.create(active=True, configured=True, data_flow_accepted=True, service_credential_encrypted="x")
    msg = Message.objects.create(body_text_index="MOCK-SPAM")
    with mock.patch("enterprise.client._api") as api:
        api.return_value = {
            "verdict": "spam",
            "score": 1,
            "reasons": [],
            "service": "mock-vendor (NOT a real spam filter)",
        }
        with mock.patch("enterprise.spam.licensed_capability", return_value=True):
            with mock.patch("provider.crypto.decrypt", return_value="cred"):
                HostedClassifier().classify(msg)
        keys = set(api.call_args[0][1].keys())
        assert keys <= {"message_id", "mime_b64", "envelope", "auth_results"}


@pytest.mark.django_db
def test_scan_persisted():
    msg = Message.objects.create(body_text_index="hello")
    result = run_scan(msg)
    assert result.message_id == msg.id
