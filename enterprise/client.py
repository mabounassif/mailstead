from __future__ import annotations

import json
import urllib.request

from django.conf import settings

from enterprise.entitlements import cache_entitlement, installation_id
from provider.crypto import decrypt, encrypt


def _api(path: str, payload: dict, bearer: str | None = None) -> dict:
    base = settings.ENTERPRISE_API_URL.rstrip("/")
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(base + path, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def activate(license_key: str) -> None:
    from enterprise.models import License

    lic = License.objects.first() or License.objects.create()
    body = {
        "license_key": license_key,
        "installation_id": installation_id(),
        "domains": [settings.MAIL_DOMAIN],
        "client_version": "0.1.0",
    }
    result = _api("/v1/activate", body)
    lic.license_key_encrypted = encrypt(license_key)
    lic.service_credential_encrypted = encrypt(result["service_credential"])
    token = result["entitlement_token"]
    cache_entitlement(token)
    lic.active = True
    lic.save()


def refresh_entitlements() -> None:
    from enterprise.models import License

    lic = License.objects.filter(active=True).first()
    if not lic or not lic.service_credential_encrypted:
        return
    credential = decrypt(lic.service_credential_encrypted)
    result = _api("/v1/entitlements/refresh", {}, bearer=credential)
    cache_entitlement(result["entitlement_token"])
