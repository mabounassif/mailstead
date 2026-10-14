import signal
import threading

from django.core.management.base import BaseCommand

from jobs.worker_runtime import run_worker_loop


class Command(BaseCommand):
    help = "Background job worker."

    def handle(self, *args, **options):
        shutdown = threading.Event()

        def _handle_signal(*_args):
            shutdown.set()

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)
        self.stdout.write("Worker started")
        run_worker_loop(shutdown)
        self.stdout.write("Worker shutting down")
