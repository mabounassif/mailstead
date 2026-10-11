from __future__ import annotations

from django.conf import settings
from django.core.cache import cache

from provider.resend_client import ResendError, list_domains


def list_domains_status() -> list[dict]:
    try:
        data = list_domains()
        return data.get("data") or data.get("domains") or []
    except ResendError:
        return []


def domain_capabilities(domain_name: str) -> dict:
    cache_key = f"domain_cap:{domain_name}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    for d in list_domains_status():
        if d.get("name") == domain_name:
            caps = d.get("capabilities") or {}
            result = {
                "sending": caps.get("sending", "unknown"),
                "receiving": caps.get("receiving", "unknown"),
                "status": d.get("status"),
            }
            cache.set(cache_key, result, 300)
            return result
    return {"sending": "unknown", "receiving": "unknown", "status": "unknown"}


def assert_sending_allowed(domain_name: str) -> None:
    caps = domain_capabilities(domain_name)
    if caps.get("sending") != "enabled":
        raise ValueError(f"Domain {domain_name} is not enabled for sending")


def configured_domains() -> list[str]:
    domains = [settings.MAIL_DOMAIN]
    return [d for d in domains if d]
