from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import SimpleTestCase
from django.utils import timezone

from mail.templatetags.mail_extras import mail_list_date


class MailListDateTests(SimpleTestCase):
    def test_today_shows_time(self):
        tz = ZoneInfo("UTC")
        now = datetime(2026, 10, 13, 15, 7, tzinfo=tz)
        with patch("django.utils.timezone.now", return_value=now):
            label = mail_list_date(now)
        self.assertEqual(label, "3:07 PM")

    def test_same_year_shows_month_day(self):
        tz = ZoneInfo("UTC")
        dt = datetime(2026, 3, 5, 10, 0, tzinfo=tz)
        frozen = datetime(2026, 10, 13, 12, 0, tzinfo=tz)
        with patch("django.utils.timezone.now", return_value=frozen):
            label = mail_list_date(dt)
        self.assertEqual(label, "Mar 5")

    def test_other_year_shows_full_date(self):
        tz = ZoneInfo("UTC")
        dt = datetime(2024, 1, 15, 10, 0, tzinfo=tz)
        frozen = datetime(2026, 10, 13, 12, 0, tzinfo=tz)
        with patch("django.utils.timezone.now", return_value=frozen):
            label = mail_list_date(dt)
        self.assertEqual(label, "1/15/2024")
