#!/usr/bin/env python3
"""Seed a demo user, mailbox, and sample messages for template screenshots."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

DEMO_USER = "demo"
DEMO_PASS = "demo-demo-demo"
DEFAULT_PORT = "18765"


def apply_screenshot_env() -> dict[str, str]:
    """Set isolated Django env defaults used by seed + capture."""
    port = os.environ.get("SCREENSHOT_PORT", DEFAULT_PORT)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    os.environ.setdefault("DEBUG", "1")
    os.environ.setdefault("SECRET_KEY", "screenshot-seed-key-" + "x" * 32)
    os.environ.setdefault("APP_ENCRYPTION_KEY", "screenshot-encryption-key")
    os.environ.setdefault("RESEND_API_KEY", "re_screenshot")
    os.environ.setdefault("MAIL_DOMAIN", "mail.demo")
    os.environ.setdefault("ADMIN_RECOVERY_EMAIL", "admin@demo.test")
    os.environ.setdefault("BOOTSTRAP_TOKEN", "used")
    os.environ.setdefault("DATA_ROOT", "/tmp/mailstead-screenshot-data")
    os.environ.setdefault("PUBLIC_URL", f"http://127.0.0.1:{port}")
    os.environ.setdefault("SKIP_WORKER_HEARTBEAT_CHECK", "1")
    data_root = Path(os.environ["DATA_ROOT"])
    for sub in ("db", "mail", "tmp"):
        (data_root / sub).mkdir(parents=True, exist_ok=True)
    return os.environ.copy()


def seed() -> None:
    import django

    django.setup()

    from django.contrib.auth import get_user_model
    from django.utils import timezone

    from accounts.models import Mailbox
    from mail.models import Folder, Message, MessageCopy

    User = get_user_model()

    user, _ = User.objects.update_or_create(
        username=DEMO_USER,
        defaults={
            "email": "demo@mail.demo",
            "is_staff": True,
            "is_superuser": True,
            "recovery_email": "admin@demo.test",
        },
    )
    user.set_password(DEMO_PASS)
    user.save()

    mailbox, _ = Mailbox.objects.update_or_create(
        user=user,
        defaults={"address": f"{DEMO_USER}@mail.demo", "state": Mailbox.State.ACTIVE},
    )

    now = timezone.now()
    samples = [
        {
            "folder": Folder.INBOX,
            "subject": "Q4 planning",
            "from_addr": "Alice Chen",
            "body": "Can we sync on the roadmap Tuesday? Reply with times that work.",
            "unread": True,
            "sent_at": now - timedelta(minutes=18),
        },
        {
            "folder": Folder.INBOX,
            "subject": "Resend webhook registered",
            "from_addr": "Mailstead Ops",
            "body": "Inbound mail for mail.demo is flowing. Check Junk if DMARC fails.",
            "unread": True,
            "sent_at": now - timedelta(hours=4),
        },
        {
            "folder": Folder.INBOX,
            "subject": "Welcome to Mailstead",
            "from_addr": "Mailstead",
            "body": "Your portal is ready. Compose, reply, and search from any browser.",
            "unread": False,
            "sent_at": now - timedelta(days=1, hours=2),
        },
        {
            "folder": Folder.INBOX,
            "subject": "Invoice #1842 is ready",
            "from_addr": "Acme Billing",
            "body": "The October invoice is attached in your billing portal. Due in 14 days.",
            "unread": False,
            "sent_at": now - timedelta(days=3),
        },
        {
            "folder": Folder.INBOX,
            "subject": "Office closed Friday",
            "from_addr": "HR",
            "body": "The office is closed this Friday. Reach the on-call list for urgent mail.",
            "unread": False,
            "sent_at": now - timedelta(days=12),
        },
    ]

    MessageCopy.objects.filter(mailbox=mailbox).delete()
    Message.objects.filter(resend_email_id__startswith="demo-").delete()

    for item in samples:
        rid = "demo-" + item["subject"].lower().replace(" ", "-").replace("#", "")
        msg = Message.objects.create(
            resend_email_id=rid,
            from_address=item["from_addr"],
            subject=item["subject"],
            body_text_index=item["body"],
            sent_at=item["sent_at"],
        )
        MessageCopy.objects.create(
            mailbox=mailbox,
            message=msg,
            folder=item["folder"],
            is_unread=item["unread"],
        )

    print(f"Demo login: {DEMO_USER} / {DEMO_PASS}")
    print(f"Mailbox: {mailbox.address}")


def main() -> None:
    apply_screenshot_env()
    seed()


if __name__ == "__main__":
    main()
