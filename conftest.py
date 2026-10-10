import os

# Must be set before pytest-django imports Django settings.
os.environ.setdefault("DEBUG", "1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-" + "x" * 40)
os.environ.setdefault("APP_ENCRYPTION_KEY", "test-encryption-key")
os.environ.setdefault("RESEND_API_KEY", "re_test_key")
os.environ.setdefault("MAIL_DOMAIN", "mail.test")
os.environ.setdefault("ADMIN_RECOVERY_EMAIL", "admin-recovery@test")
os.environ.setdefault("BOOTSTRAP_TOKEN", "bootstrap-test-token")
os.environ.setdefault("SKIP_WORKER_HEARTBEAT_CHECK", "1")
os.environ.setdefault("PUBLIC_URL", "http://testserver")
os.environ.setdefault("DATA_ROOT", "/tmp/mailstead-test-data")

import pytest


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        from django.core.management import call_command

        call_command("createcachetable", verbosity=0)


@pytest.fixture(autouse=True)
def _test_env(tmp_path, settings, monkeypatch):
    data = tmp_path / "data"
    monkeypatch.setenv("DATA_ROOT", str(data))
    settings.DATA_ROOT = data
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    (data / "tmp").mkdir(parents=True, exist_ok=True)


@pytest.fixture
def bootstrap_token():
    return os.environ["BOOTSTRAP_TOKEN"]
