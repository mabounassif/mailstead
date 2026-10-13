from provider.usage_service import usage_period_rows


def test_usage_period_rows_formats_daily_and_monthly():
    parsed = {
        "daily": {"used": 10, "limit": 100, "sent": 8, "received": 2, "remaining": 90, "resets_at": "midnight"},
        "monthly": {"used": 50, "limit": 3000, "sent": 40, "received": 10, "remaining": 2950, "resets_at": "2026-11-01"},
    }
    rows = usage_period_rows(parsed)
    assert len(rows) == 2
    assert rows[0]["title"] == "Daily"
    assert rows[0]["used"] == 10
    assert rows[1]["title"] == "Monthly"
