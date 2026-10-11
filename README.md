# Mailstead

Self-hosted webmail portal backed by [Resend](https://resend.com) for sending and receiving. Designed for small teams (roughly 10–50 users), one Docker service, and a persistent data volume—no Redis, Celery, or separate mail server in the default stack.

**Stack:** Django 5.2, HTMX, SQLite (or Postgres via `DATABASE_URL`), background jobs in-process with a dedicated worker.

## Features

- Inbox, Sent, Drafts, Archive, Junk, Trash; compose, reply, forward, attachments
- Inbound mail via Resend webhooks; outbound via Resend API
- Per-mailbox quotas, usage dashboard, optional enterprise entitlements API
- Railway-friendly: health (`/healthz`), readiness (`/readyz`), volume at `/data`

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # edit with your values
export DEBUG=1 SECRET_KEY=dev APP_ENCRYPTION_KEY=dev BOOTSTRAP_TOKEN=dev \
  RESEND_API_KEY=re_test MAIL_DOMAIN=mail.test ADMIN_RECOVERY_EMAIL=admin@test \
  DATA_ROOT=/tmp/mailstead-data PUBLIC_URL=http://localhost:8000
mkdir -p "$DATA_ROOT"
python manage.py migrate
python manage.py createcachetable
python manage.py runserver
```

Create the first admin once at `/setup/<BOOTSTRAP_TOKEN>`.

Run the job worker in another terminal (required for send/receive processing):

```bash
python manage.py worker
```

## Tests

```bash
pytest
```

Postgres (optional): `DATABASE_URL=postgres://mailstead:mailstead@localhost:5432/mailstead pytest -m postgres`

## Docker

```bash
docker compose up --build
```

## Deploy

- [Railway (manual)](docs/deploy-railway.md)
- [Railway template composer](docs/railway-template.md) (for publishing or customizing the template)
- [Operations](docs/operations.md) — backups, upgrades, quotas

Copy [`.env.example`](.env.example) for all configuration knobs.

## Project status

Core milestones (mailbox, jobs, webhooks, storage, enterprise hooks) are implemented. See [PLAN.md](PLAN.md) for architecture notes and milestone history.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and feature requests: [GitHub Issues](https://github.com/mabounassif/mailstead/issues).

## License

[MIT](LICENSE)
