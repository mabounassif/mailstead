"""Pytest settings: set env defaults before loading production settings."""

import os

_DEFAULTS = {
    "DEBUG": "1",
    "SECRET_KEY": "test-secret-key-" + "x" * 40,
    "APP_ENCRYPTION_KEY": "test-encryption-key",
    "RESEND_API_KEY": "re_test_key",
    "MAIL_DOMAIN": "mail.test",
    "ADMIN_RECOVERY_EMAIL": "admin-recovery@test",
    "BOOTSTRAP_TOKEN": "bootstrap-test-token",
    "SKIP_WORKER_HEARTBEAT_CHECK": "1",
    "PUBLIC_URL": "http://testserver",
    "DATA_ROOT": "/tmp/mailstead-test-data",
    "RESEND_WEBHOOK_SECRET": "whsec_test",
    "VAPID_PUBLIC_KEY": "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U",
    "VAPID_PRIVATE_KEY": "UUxI4O8-FbRWD_A7SWv7KwJlwn_-jJasAJB0DXwUgj1E",
}
for key, value in _DEFAULTS.items():
    os.environ.setdefault(key, value)

from core.settings import *  # noqa: F403

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "mailstead-tests",
    }
}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
