import pytest

from provider.models import UsageAlert
from provider.usage_parser import parse_usage
from provider.usage_service import refresh_usage


def test_parser_null_limits():
    parsed = parse_usage({"emails": {"daily": {"used": 1, "limit": None, "resets_at": "t"}}})
    assert parsed["daily"]["limit"] == "uncapped (per Resend docs)"
    assert parsed["daily"]["used"] == 1


def test_parser_missing_fields_unknown():
    parsed = parse_usage({})
    assert parsed["daily"]["used"] == "unknown"


@pytest.mark.django_db
def test_alert_dedupe():
    from unittest import mock

    raw = {
        "emails": {
            "daily": {"used": 90, "limit": 100, "resets_at": "2026-01-01"},
            "monthly": {"used": 0, "limit": 1000, "resets_at": "2026-02-01"},
        },
        "rate_limit": {"limit": 10, "duration": "1000ms"},
    }
    with mock.patch("provider.usage_service.get_usage", return_value=raw):
        refresh_usage()
        refresh_usage()
    assert UsageAlert.objects.filter(quota="daily", threshold=90).count() == 1


@pytest.mark.django_db
def test_stale_snapshot_on_error():
    from unittest import mock
    from provider.models import UsageSnapshot
    from provider.resend_client import ResendError

    UsageSnapshot.objects.create(raw_json={"x": 1}, parsed_json={"daily": {"used": 1}}, ok=True)
    with mock.patch("provider.usage_service.get_usage", side_effect=ResendError("restricted_api_key")):
        snap = refresh_usage()
    assert not snap.ok
    assert UsageSnapshot.objects.filter(ok=True).exists()
