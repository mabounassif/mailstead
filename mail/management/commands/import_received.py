from django.core.management.base import BaseCommand

from mail.reconcile import reconcile_received


class Command(BaseCommand):
    help = "Import received mail history from Resend (resumable)."

    def handle(self, *args, **options):
        count = reconcile_received()
        self.stdout.write(f"Imported/enqueued {count} messages")
