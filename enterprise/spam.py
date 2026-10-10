from __future__ import annotations

import base64
from dataclasses import dataclass

from django.conf import settings

from enterprise.entitlements import licensed_capability
from enterprise.models import License, ScanResult


@dataclass
class Verdict:
    verdict: str
    score: float
    reasons: list[str]
    service: str
    engine_version: str = ""
    model_version: str = ""


class SpamClassifier:
    def classify(self, message) -> Verdict:
        raise NotImplementedError


class LocalRulesClassifier(SpamClassifier):
    def classify(self, message) -> Verdict:
        text = (message.body_text_index or "").upper()
        if "SPAM" in text or message.auth_dmarc == "fail":
            return Verdict("spam", 0.9, ["local-rule"], "local-rules")
        return Verdict("ham", 0.1, [], "local-rules")


class HostedClassifier(SpamClassifier):
    def classify(self, message) -> Verdict:
        if not licensed_capability("spam_filtering"):
            return Verdict("unsure", 0, ["not licensed"], "hosted-disabled")
        lic = License.objects.filter(active=True, configured=True, data_flow_accepted=True).first()
        if not lic:
            return Verdict("unsure", 0, ["not configured"], "hosted-disabled")
        from enterprise.client import _api
        from provider.crypto import decrypt

        credential = decrypt(lic.service_credential_encrypted)
        mime_b64 = ""
        if message.blob_id:
            with open(message.blob.path, "rb") as f:
                mime_b64 = base64.b64encode(f.read()).decode("ascii")
        payload = {
            "message_id": str(message.id),
            "mime_b64": mime_b64,
            "envelope": {"from": message.from_address, "to": message.to_index},
            "auth_results": {
                "spf": message.auth_spf,
                "dkim": message.auth_dkim,
                "dmarc": message.auth_dmarc,
            },
        }
        allowed = {"message_id", "mime_b64", "envelope", "auth_results"}
        assert set(payload.keys()) <= allowed
        result = _api("/v1/spam/classify", payload, bearer=credential)
        return Verdict(
            result.get("verdict", "unsure"),
            float(result.get("score", 0)),
            result.get("reasons") or [],
            result.get("service", "vendor"),
            result.get("engine_version", ""),
            result.get("model_version", ""),
        )


def run_scan(message) -> ScanResult:
    lic = License.objects.filter(active=True, configured=True).first()
    classifier = HostedClassifier() if lic and licensed_capability("spam_filtering") else LocalRulesClassifier()
    v = classifier.classify(message)
    return ScanResult.objects.create(
        message=message,
        verdict=v.verdict,
        score=v.score,
        reasons=v.reasons,
        service=v.service,
        engine_version=v.engine_version,
        model_version=v.model_version,
    )
