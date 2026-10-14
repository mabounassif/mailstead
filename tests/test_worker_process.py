import ast
import threading
from pathlib import Path

import pytest
from django.core.management import call_command

from accounts.models import BootstrapState
from jobs.models import Schedule, WorkerHeartbeat
from jobs.worker_runtime import HANDLERS, JOB_POOL_WORKERS, register_job_handlers, run_worker_loop


def test_supervisor_does_not_import_django():
    source = Path("mailstead/run.py").read_text()
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    assert not any(name == "django" or name.startswith("django.") for name in modules)


def test_main_prepares_then_execs_gunicorn(monkeypatch):
    import mailstead.run as run

    calls: list[list[str]] = []
    monkeypatch.setattr(run, "_prepare_data_volume", lambda: None)
    monkeypatch.setattr(run, "_ensure_data_dirs", lambda: None)
    monkeypatch.setattr(run.subprocess, "check_call", lambda cmd: calls.append(cmd))

    def fake_exec(executable, argv, env):
        calls.append(argv)
        assert env["DJANGO_SETTINGS_MODULE"]
        raise SystemExit(0)

    monkeypatch.setattr(run.os, "execvpe", fake_exec)
    with pytest.raises(SystemExit):
        run.main()

    manage = [cmd for cmd in calls if cmd[1:2] == ["manage.py"]]
    assert [cmd[2] for cmd in manage] == ["migrate", "createcachetable", "prepare"]
    gunicorn = calls[-1]
    assert gunicorn[1:4] == ["-m", "gunicorn", "mailstead.wsgi:application"]
    assert "mailstead/gunicorn.conf.py" in gunicorn
    assert not any(cmd[-1:] == ["worker"] for cmd in calls)


@pytest.mark.django_db
def test_prepare_bootstraps_schedules(bootstrap_token):
    call_command("prepare")
    assert BootstrapState.objects.exists()
    assert Schedule.objects.filter(name="reconcile_received", enabled=True).exists()
    assert Schedule.objects.filter(name="usage_refresh").exists()


@pytest.mark.django_db
def test_register_job_handlers():
    register_job_handlers()
    assert "inbound" in HANDLERS
    assert "outbound_send" in HANDLERS
    assert "usage_refresh" in HANDLERS
    assert "storage_sweep" in HANDLERS
    assert "push_notify_mailbox" in HANDLERS


@pytest.mark.django_db
def test_run_worker_loop_honors_shutdown(monkeypatch):
    assert JOB_POOL_WORKERS == 1
    shutdown = threading.Event()
    ticks = {"n": 0}
    pools: list[int] = []

    real_tick = __import__("jobs.worker_runtime", fromlist=["_tick_schedules"])._tick_schedules

    def tick():
        ticks["n"] += 1
        shutdown.set()
        real_tick()

    class RecordingPool:
        def __init__(self, max_workers):
            pools.append(max_workers)

        def submit(self, fn, job):
            raise AssertionError("idle loop should not claim a job")

        def shutdown(self, wait=True, cancel_futures=False):
            return None

    monkeypatch.setattr("jobs.worker_runtime._tick_schedules", tick)
    monkeypatch.setattr("jobs.worker_runtime.claim_next", lambda owner: None)
    monkeypatch.setattr("jobs.worker_runtime.ThreadPoolExecutor", RecordingPool)

    run_worker_loop(shutdown)

    assert ticks["n"] == 1
    assert pools == [1]
    assert WorkerHeartbeat.objects.filter(pk=1).exists()
