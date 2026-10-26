# Local development

Mailstead is a Django 5.2 app. The browser UI is server-rendered templates plus a little HTMX and CSS — there is no Node frontend build.

## Prerequisites

- Python 3.12+
- A virtualenv

Postgres is optional. SQLite on `DATA_ROOT` is the default.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Django reads **process environment**, not `.env` automatically. Load the file, then turn on debug:

```bash
set -a && source .env && set +a
export DEBUG=1
export DATA_ROOT="${DATA_ROOT:-/tmp/mailstead-data}"
export PUBLIC_URL="${PUBLIC_URL:-http://localhost:8000}"
mkdir -p "$DATA_ROOT"
```

In `DEBUG=1`, empty `SECRET_KEY` / Resend values are allowed so you can run the UI without a live provider. Sending and receiving mail still need a real `RESEND_API_KEY` and verified `MAIL_DOMAIN`.

```bash
python manage.py migrate
python manage.py createcachetable
python manage.py runserver
```

In a second terminal, with the same environment:

```bash
python manage.py worker
```

The worker is required for inbound webhooks, outbound sends, and scheduled jobs.

### First admin

Open `/setup/<BOOTSTRAP_TOKEN>` once (use the `BOOTSTRAP_TOKEN` from your environment). Then create users and mailboxes in `/admin/`.

## Tests

```bash
pytest
node --test core/static/mailstead/review_queue.test.js
```

Postgres integration tests (opt-in):

```bash
DATABASE_URL=postgres://mailstead:mailstead@localhost:5432/mailstead pytest -m postgres
```

A Compose profile can start Postgres:

```bash
docker compose --profile postgres up postgres
```

## Docker

```bash
docker compose up --build
```

The image runs `python -m mailstead.run` with a volume at `/data`. That command migrates, then replaces itself with gunicorn (one worker, four threads). The job loop runs inside that worker. Local `runserver` still needs a separate `python manage.py worker`.

## Project layout

| Path | What it is |
|------|------------|
| `accounts/` | Login, bootstrap setup, mailboxes |
| `mail/` | Folders, compose, inbound/outbound, search |
| `jobs/` | DB-backed job queue; in-process under gunicorn, or `manage.py worker` with `runserver` |
| `provider/` | Resend API, webhooks, usage |
| `storage/` | Quotas, ops dashboard (`/ops/`) |
| `notifications/` | Web Push, PWA bits, and optional Expo device tokens |
| `api/` | Versioned JSON API for the phone app (`/api/v1/`) |
| `mobile/` | Optional Expo client. Not part of the Docker image |
| `core/` | Settings, health checks, static CSS/JS |
| `templates/` | Django templates |
| `railway/` | Published Railway template config |

## Screenshots

Marketplace and README shots live in `docs/assets/screenshots/`. Recapture after UI changes:

```bash
pip install -e ".[screenshots]"
playwright install chromium
python scripts/capture_template_screenshots.py
```

The script migrates an isolated `DATA_ROOT`, seeds a demo mailbox, starts a temporary server, and writes `login.png`, `inbox.png`, and `compose.png`.

## Configuration

All knobs are listed in [`.env.example`](../.env.example). Deploy notes: [Railway](deploy-railway.md), [operations](operations.md).

Web Push is optional. Generate VAPID keys (`uv run vapid --gen`, then `uv run vapid --applicationServerKey -k private_key.pem`) and set `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`. On iPhone, use Safari → Add to Home Screen, then **Notifications** in the mail sidebar.

Native push for the Expo app is also optional. Set `EXPO_ACCESS_TOKEN` only when you want the server to deliver to registered phones. Without it, the app still saves notification preferences.
