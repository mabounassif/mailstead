"""Django settings for Mailstead."""

import os
from pathlib import Path

import dj_database_url

from core.paths import data_root

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")

SECRET_KEY = os.environ.get("SECRET_KEY") or ("dev-insecure-" + "x" * 50 if DEBUG else "")
if not SECRET_KEY and not DEBUG:
    raise RuntimeError("SECRET_KEY is required")

APP_ENCRYPTION_KEY = os.environ.get("APP_ENCRYPTION_KEY", "")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
MAIL_DOMAIN = os.environ.get("MAIL_DOMAIN", "")
ADMIN_RECOVERY_EMAIL = os.environ.get("ADMIN_RECOVERY_EMAIL", "")

if not DEBUG:
    for name, val in (
        ("RESEND_API_KEY", RESEND_API_KEY),
        ("MAIL_DOMAIN", MAIL_DOMAIN),
        ("ADMIN_RECOVERY_EMAIL", ADMIN_RECOVERY_EMAIL),
    ):
        if not val:
            raise RuntimeError(f"{name} is required")

BOOTSTRAP_TOKEN = os.environ.get("BOOTSTRAP_TOKEN", "")

_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
PUBLIC_URL = os.environ.get("PUBLIC_URL") or (
    f"https://{_railway_domain}" if _railway_domain else "http://localhost:8000"
)

_allowed_hosts = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
if _railway_domain and _railway_domain not in _allowed_hosts:
    _allowed_hosts.append(_railway_domain)
_private_domain = os.environ.get("RAILWAY_PRIVATE_DOMAIN", "")
if _private_domain and _private_domain not in _allowed_hosts:
    _allowed_hosts.append(_private_domain)
_on_railway = bool(os.environ.get("RAILWAY_ENVIRONMENT") or _railway_domain)
if DEBUG or _on_railway:
    for host in ("localhost", "127.0.0.1", "[::1]"):
        if host not in _allowed_hosts:
            _allowed_hosts.append(host)
if _on_railway and ".up.railway.app" not in _allowed_hosts:
    _allowed_hosts.append(".up.railway.app")
ALLOWED_HOSTS = _allowed_hosts

DATA_ROOT = data_root()
ensure_dirs = DATA_ROOT  # noqa: F841 — documented mount

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    db_path = DATA_ROOT / "db" / "mailstead.sqlite3"
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": db_path,
            "OPTIONS": {
                "timeout": 30,
                "transaction_mode": "IMMEDIATE",
            },
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "axes",
    "core",
    "accounts",
    "jobs",
    "mail",
    "provider",
    "storage",
    "enterprise",
]

ENTERPRISE_API_URL = os.environ.get("ENTERPRISE_API_URL", "http://127.0.0.1:8765")
ENTERPRISE_PUBLIC_KEYS = [k for k in os.environ.get("ENTERPRISE_PUBLIC_KEYS", "").split("---KEY---") if k.strip()]
ENTERPRISE_GRACE_HOURS = int(os.environ.get("ENTERPRISE_GRACE_HOURS", "72"))

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "mailstead.urls"
WSGI_APPLICATION = "mailstead.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "mailstead_cache",
    }
}

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "").lower() in ("1", "true") and not DEBUG

_csrf_origin = PUBLIC_URL.rstrip("/")
CSRF_TRUSTED_ORIGINS = [_csrf_origin]
if _csrf_origin.startswith("https://"):
    CSRF_TRUSTED_ORIGINS.append(_csrf_origin.replace("https://", "http://", 1))

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/mail/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_RESET_ON_SUCCESS = True

PASSWORD_RESET_TIMEOUT = 3600  # 1 hour

DEFAULT_MAILBOX_QUOTA_BYTES = int(os.environ.get("DEFAULT_MAILBOX_QUOTA_BYTES", str(250 * 1024 * 1024)))

WORKER_HEARTBEAT_MAX_AGE_SECONDS = int(os.environ.get("WORKER_HEARTBEAT_MAX_AGE_SECONDS", "120"))

MAX_MESSAGE_BYTES = int(os.environ.get("MAX_MESSAGE_BYTES", str(30 * 1024 * 1024)))
RESEND_WEBHOOK_SECRET = os.environ.get("RESEND_WEBHOOK_SECRET", "")

EMAIL_BUDGET_BYTES = os.environ.get("EMAIL_BUDGET_BYTES")
EMAIL_BUDGET_BYTES = int(EMAIL_BUDGET_BYTES) if EMAIL_BUDGET_BYTES else None
DATA_VOLUME_CAPACITY_BYTES = os.environ.get("DATA_VOLUME_CAPACITY_BYTES")
DATA_VOLUME_CAPACITY_BYTES = int(DATA_VOLUME_CAPACITY_BYTES) if DATA_VOLUME_CAPACITY_BYTES else None
DISK_RESERVE_BYTES = int(os.environ.get("DISK_RESERVE_BYTES", str(256 * 1024 * 1024)))
OVERFLOW_BUDGET_BYTES = int(os.environ.get("OVERFLOW_BUDGET_BYTES", str(50 * 1024 * 1024)))
OVERFLOW_TTL_DAYS = int(os.environ.get("OVERFLOW_TTL_DAYS", "14"))

USAGE_REFRESH_MINUTES = max(5, int(os.environ.get("USAGE_REFRESH_MINUTES", "30")))
USAGE_ALERT_THRESHOLDS = [80, 90, 100]
LOCAL_SEND_BUDGET_DAILY = os.environ.get("LOCAL_SEND_BUDGET_DAILY")
LOCAL_SEND_BUDGET_MONTHLY = os.environ.get("LOCAL_SEND_BUDGET_MONTHLY")

PASSWORD_RESET_RATE_LIMIT = os.environ.get("PASSWORD_RESET_RATE_LIMIT", "5/h")

EMAIL_BACKEND = "core.email_backends.ResendBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL") or (
    f"noreply@{MAIL_DOMAIN}" if MAIL_DOMAIN else "noreply@localhost"
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "redact": {"()": "core.logging_redaction.RedactingFilter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["redact"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
