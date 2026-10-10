import os
import signal
import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import WorkerHeartbeat

_shutdown = False


def _handle_sigterm(*_args):
    global _shutdown
    _shutdown = True


class Command(BaseCommand):
    help = "Background worker stub (heartbeat only until M2)."

    def handle(self, *args, **options):
        signal.signal(signal.SIGTERM, _handle_sigterm)
        signal.signal(signal.SIGINT, _handle_sigterm)
        pid = os.getpid()
        self.stdout.write(f"Worker started pid={pid}")
        while not _shutdown:
            hb, _ = WorkerHeartbeat.objects.get_or_create(pk=1, defaults={"pid": pid})
            hb.pid = pid
            hb.save(update_fields=["pid", "updated_at"])
            time.sleep(15)
        self.stdout.write("Worker shutting down")
