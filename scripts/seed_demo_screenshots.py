#!/usr/bin/env python3
"""Seed a demo user, mailbox, and sample messages for template screenshots."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
os.environ.setdefault("DEBUG", "1")
os.environ.setdefault("SECRET_KEY", "screenshot-seed-key-" + "x" * 32)
os.environ.setdefault("APP_ENCRYPTION_KEY", "screenshot-encryption-key")
os.environ.setdefault("RESEND_API_KEY", "re_screenshot")
os.environ.setdefault("MAIL_DOMAIN", "mail.demo")
os.environ.setdefault("ADMIN_RECOVERY_EMAIL", "admin@demo.test")
os.environ.setdefault("BOOTSTRAP_TOKEN", "used")
os.environ.setdefault("DATA_ROOT", "/tmp/mailstead-screenshot-data")
os.environ.setdefault("PUBLIC_URL", "http://127.0.0.1:8765")
os.environ.setdefault("SKIP_WORKER_HEARTBEAT_CHECK", "1")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Mailbox
from mail.models import Folder, Message, MessageCopy

User = get_user_model()

DEMO_USER = "demo"
DEMO_PASS = "demo-demo-demo"


def main() -> None:
    from pathlib import Path

    data_root = Path(os.environ["DATA_ROOT"])
    data_root.mkdir(parents=True, exist_ok=True)

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

    samples = [
        (Folder.INBOX, "Welcome to Mailstead", "team@mail.demo", "Your portal is ready. Compose, reply, and search from any browser."),
        (Folder.INBOX, "Resend webhook registered", "ops@mail.demo", "Inbound mail for mail.demo is flowing. Check Junk if DMARC fails."),
        (Folder.INBOX, "Q4 planning", "alice@partner.com", "Can we sync on the roadmap Tuesday? Reply with times that work."),
    ]
    for folder, subject, from_addr, body in samples:
        rid = f"demo-{subject.lower().replace(' ', '-')}"
        msg, created = Message.objects.get_or_create(
            resend_email_id=rid,
            defaults={
                "from_address": from_addr,
                "subject": subject,
                "body_text_index": body,
                "sent_at": timezone.now(),
            },
        )
        if not created:
            Message.objects.filter(pk=msg.pk).update(
                from_address=from_addr,
                subject=subject,
                body_text_index=body,
            )
        MessageCopy.objects.update_or_create(
            mailbox=mailbox,
            message=msg,
            folder=folder,
            defaults={"is_unread": subject.startswith("Q4")},
        )

    print(f"Demo login: {DEMO_USER} / {DEMO_PASS}")
    print(f"Mailbox: {mailbox.address}")


if __name__ == "__main__":
    main()
