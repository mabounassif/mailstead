from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 30


class ResendError(Exception):
    def __init__(self, message: str, *, status: int | None = None, error_type: str | None = None):
        super().__init__(message)
        self.status = status
        self.error_type = error_type


_PLACEHOLDER_KEYS = frozenset(
    {
        "re_placeholder",
        "re_replace_me",
        "re_test",
        "re_test_key",
        "re_xxxxxxxx",
    }
)


def resend_api_configured() -> bool:
    """True when a real Resend API key is set (not empty or a dev placeholder)."""
    key = (settings.RESEND_API_KEY or "").strip()
    if not key.startswith("re_") or len(key) < 12:
        return False
    if key in _PLACEHOLDER_KEYS:
        return False
    if key.startswith("re_xxx"):
        return False
    return True


@dataclass
class TokenBucket:
    rate: float
    capacity: float
    tokens: float
    updated: float

    def consume(self, amount: float = 1.0) -> float:
        now = time.monotonic()
        elapsed = now - self.updated
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.updated = now
        if self.tokens >= amount:
            self.tokens -= amount
            return 0.0
        need = amount - self.tokens
        return need / self.rate


_bucket_lock = threading.Lock()
_bucket: TokenBucket | None = None


def _get_bucket() -> TokenBucket:
    global _bucket
    if _bucket is None:
        rate = 5.0  # 10/s halved for headroom until usage refresh
        _bucket = TokenBucket(rate=rate, capacity=rate, tokens=rate, updated=time.monotonic())
    return _bucket


def configure_rate_limit(limit: int, duration_ms: int) -> None:
    global _bucket
    if duration_ms <= 0:
        return
    per_sec = limit / (duration_ms / 1000.0)
    with _bucket_lock:
        _bucket = TokenBucket(rate=per_sec / 2, capacity=per_sec, tokens=per_sec, updated=time.monotonic())


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {settings.RESEND_API_KEY}"
    return s


def _wait_rate_limit() -> None:
    with _bucket_lock:
        bucket = _get_bucket()
        wait = bucket.consume(1.0)
    if wait > 0:
        time.sleep(wait)


def classify_http_error(status: int, body: dict | None) -> ResendError:
    err_type = (body or {}).get("type") or (body or {}).get("name")
    message = (body or {}).get("message", f"HTTP {status}")
    return ResendError(message, status=status, error_type=err_type)


def _parse_resend_exception(exc: Exception) -> ResendError:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    err_type = None
    if hasattr(exc, "error") and isinstance(exc.error, dict):
        err_type = exc.error.get("type") or exc.error.get("name")
    text = str(exc)
    if "email_above_quota" in text:
        err_type = "email_above_quota"
    return ResendError(text, status=status, error_type=err_type)


def get_receiving_email(email_id: str) -> dict[str, Any]:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    _wait_rate_limit()
    try:
        return resend.Emails.Receiving.get(email_id=email_id)
    except Exception as exc:
        raise _parse_resend_exception(exc) from exc


def list_receiving(limit: int = 100, after: str | None = None) -> dict[str, Any]:
    import resend
    from resend.emails._receiving import Receiving

    resend.api_key = settings.RESEND_API_KEY
    _wait_rate_limit()
    params: Receiving.ListParams = {"limit": limit}
    if after:
        params["after"] = after
    try:
        response = resend.Emails.Receiving.list(params)
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return dict(response)
    except Exception as exc:
        raise _parse_resend_exception(exc) from exc


def send_email(payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    _wait_rate_limit()
    try:
        return resend.Emails.send(payload, options={"idempotency_key": idempotency_key})
    except Exception as exc:
        err = _parse_resend_exception(exc)
        if err.status == 429:
            retry_after = getattr(exc, "retry_after", None)
            if retry_after:
                time.sleep(min(float(retry_after), 30))
        raise err


def list_webhooks() -> dict[str, Any]:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    _wait_rate_limit()
    try:
        response = resend.Webhooks.list()
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return dict(response)
    except Exception as exc:
        raise _parse_resend_exception(exc) from exc


def get_webhook(webhook_id: str) -> dict[str, Any]:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    _wait_rate_limit()
    try:
        response = resend.Webhooks.get(webhook_id)
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return dict(response)
    except Exception as exc:
        raise _parse_resend_exception(exc) from exc


def create_webhook(endpoint: str, events: list[str]) -> dict[str, Any]:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    _wait_rate_limit()
    try:
        response = resend.Webhooks.create({"endpoint": endpoint, "events": events})
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return dict(response)
    except Exception as exc:
        raise _parse_resend_exception(exc) from exc


def list_domains() -> dict[str, Any]:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    _wait_rate_limit()
    return resend.Domains.list()


def get_usage() -> dict[str, Any]:
    import resend

    resend.api_key = settings.RESEND_API_KEY
    _wait_rate_limit()
    return resend.Usage.get()


def verify_webhook(payload: bytes, headers: dict[str, str], secret: str) -> None:
    import resend

    resend.Webhooks.verify(
        {
            "payload": payload.decode("utf-8"),
            "headers": {
                "id": headers.get("svix-id", ""),
                "timestamp": headers.get("svix-timestamp", ""),
                "signature": headers.get("svix-signature", ""),
            },
            "webhook_secret": secret,
        }
    )
