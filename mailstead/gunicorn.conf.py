"""Gunicorn config. Loaded by the master process; Django is imported only in the worker.

workers stays 1. Each worker starts its own job poller, and this service is a
single replica.
"""

from __future__ import annotations

import os
import signal

bind = os.environ.get("GUNICORN_BIND") or f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = 1
worker_class = "gthread"
threads = 4
timeout = 60
graceful_timeout = 25
accesslog = "-"
errorlog = "-"
control_socket_disable = True


def _chain_shutdown(previous):
    from jobs.worker_runtime import request_worker_shutdown

    def handler(signum, frame):
        request_worker_shutdown()
        if callable(previous):
            previous(signum, frame)

    return handler


def post_fork(server, worker):
    import threading
    import time

    def _run():
        # post_fork runs before the worker loads the WSGI app.
        from django.apps import apps

        while not apps.ready:
            time.sleep(0.05)
        from jobs.worker_runtime import run_worker_loop

        run_worker_loop()

    thread = threading.Thread(target=_run, name="mailstead-jobs", daemon=True)
    thread.start()
    worker.mailstead_job_thread = thread


def post_worker_init(worker):
    # init_signals() installs handlers after post_fork, so chain them here.
    # Railway stops the container with SIGTERM; worker_int only runs for SIGINT/SIGQUIT.
    signal.signal(signal.SIGTERM, _chain_shutdown(signal.getsignal(signal.SIGTERM)))
    signal.signal(signal.SIGINT, _chain_shutdown(signal.getsignal(signal.SIGINT)))
    signal.signal(signal.SIGQUIT, _chain_shutdown(signal.getsignal(signal.SIGQUIT)))


def worker_int(worker):
    from jobs.worker_runtime import request_worker_shutdown

    request_worker_shutdown()


def worker_exit(server, worker):
    try:
        from jobs.worker_runtime import request_worker_shutdown
    except Exception:
        return
    request_worker_shutdown()
    thread = getattr(worker, "mailstead_job_thread", None)
    if thread is not None:
        thread.join(timeout=20)
