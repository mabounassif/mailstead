from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Mailbox
from mail.models import Folder, Message, MessageCopy


class Command(BaseCommand):
    help = "Create a demo user and a 3-message Hi thread for local UI testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="demo",
            help="Password for the demo user (default: demo).",
        )

    def handle(self, *args, **options):
        password = options["password"]
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com"},
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        elif not user.check_password(password):
            user.set_password(password)
            user.save(update_fields=["password"])

        mailbox, _ = Mailbox.objects.get_or_create(
            user=user,
            defaults={"address": "demo@mail.test"},
        )

        MessageCopy.objects.filter(mailbox=mailbox).delete()
        Message.objects.filter(copies__mailbox=mailbox).delete()

        now = timezone.now()
        t0 = now - timedelta(minutes=43)
        t1 = now - timedelta(minutes=35)
        t2 = now

        first = Message.objects.create(
            subject="Hi",
            from_address="demo@mail.test",
            to_index="mahmoud.abounassif@gmail.com",
            message_id="<demo-hi-1@mail.test>",
            sent_at=t0,
            body_text_index="This is a test",
        )
        MessageCopy.objects.create(
            message=first,
            mailbox=mailbox,
            folder=Folder.SENT,
            is_unread=False,
        )

        second = Message.objects.create(
            subject="Re: Hi",
            from_address="Mahmoud Nassif <mahmoud.abounassif@gmail.com>",
            to_index="demo@mail.test",
            message_id="<demo-hi-2@gmail.com>",
            in_reply_to="<demo-hi-1@mail.test>",
            references_text="<demo-hi-1@mail.test>",
            sent_at=t1,
            body_text_index=(
                "It works!\n\n"
                "On Wed, Oct 14, 2026 at 9:56 AM <demo@mail.test> wrote:\n"
                "This is a test"
            ),
        )
        inbox_copy = MessageCopy.objects.create(
            message=second,
            mailbox=mailbox,
            folder=Folder.INBOX,
            is_unread=False,
        )

        third = Message.objects.create(
            subject="Re: Hi",
            from_address="demo@mail.test",
            to_index="mahmoud.abounassif@gmail.com",
            message_id="<demo-hi-3@mail.test>",
            in_reply_to="<demo-hi-2@gmail.com>",
            references_text="<demo-hi-1@mail.test> <demo-hi-2@gmail.com>",
            sent_at=t2,
            body_text_index="Awesome",
        )
        MessageCopy.objects.create(
            message=third,
            mailbox=mailbox,
            folder=Folder.SENT,
            is_unread=False,
        )

        url = f"/mail/m/{inbox_copy.id}/"
        self.stdout.write(self.style.SUCCESS("Demo thread ready."))
        self.stdout.write(f"  Login:  demo / {password}")
        self.stdout.write(f"  Inbox:  http://localhost:8000/mail/inbox/")
        self.stdout.write(f"  Thread: http://localhost:8000{url}")
