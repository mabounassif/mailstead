import os
import signal
import time
from concurrent.futures import ThreadPoolExecutor

from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import WorkerHeartbeat
from jobs.queue import claim_next, worker_owner
from jobs.worker_runtime import _run_job, _tick_schedules

_shutdown = False


def _handle_sigterm(*_args):
    global _shutdown
    _shutdown = True


class Command(BaseCommand):
    help = "Background job worker."

    def handle(self, *args, **options):
        signal.signal(signal.SIGTERM, _handle_sigterm)
        signal.signal(signal.SIGINT, _handle_sigterm)
        pid = os.getpid()
        owner = worker_owner()
        self.stdout.write(f"Worker started pid={pid} owner={owner}")

        # Register job handlers
        import mail.jobs  # noqa: F401
        import provider.jobs  # noqa: F401
        import storage.jobs  # noqa: F401

        with ThreadPoolExecutor(max_workers=2) as pool:
            while not _shutdown:
                WorkerHeartbeat.objects.update_or_create(pk=1, defaults={"pid": pid})
                _tick_schedules()
                job = claim_next(owner)
                if job:
                    pool.submit(_run_job, job)
                else:
                    time.sleep(1)
        self.stdout.write("Worker shutting down")
