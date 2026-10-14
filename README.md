# Mailstead

Self-hosted webmail for small teams, backed by [Resend](https://resend.com). One Docker service, a persistent data volume, and no Redis, Celery, or separate mail server in the default stack.

<p align="center">
  <img src="docs/assets/screenshots/inbox.png" alt="Mailstead inbox" width="920" />
</p>

**Stack:** Django 5.2, HTMX, SQLite (or Postgres via `DATABASE_URL`), in-process background jobs.

## Features

- Inbox, Sent, Drafts, Archive, Junk, Trash — compose, reply, forward, attachments, search
- Inbound mail via Resend webhooks; outbound via the Resend API
- Per-mailbox quotas and a Resend usage panel
- Ops dashboard at `/ops/` (storage, worker, webhooks)
- Installable web app; optional Web Push when VAPID keys are set
- Railway-ready: `/healthz`, `/readyz`, volume at `/data`

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Load env vars (Django does not read `.env` on its own), then run migrations and the dev server:

```bash
set -a && source .env && set +a
export DEBUG=1 DATA_ROOT=/tmp/mailstead-data PUBLIC_URL=http://localhost:8000
mkdir -p "$DATA_ROOT"
python manage.py migrate
python manage.py createcachetable
python manage.py runserver
```

Create the first admin at `/setup/<BOOTSTRAP_TOKEN>`.

In another terminal (same environment), start the worker — required for send/receive:

```bash
python manage.py worker
```

Full local notes, project layout, and screenshot regen: **[Local development](docs/development.md)**.

## Screenshots

<p align="center">
  <img src="docs/assets/screenshots/compose.png" alt="Compose a message" width="920" />
</p>

<p align="center">
  <img src="docs/assets/screenshots/login.png" alt="Sign in" width="920" />
</p>

## Configuration

Copy [`.env.example`](.env.example) and set at least:

| Variable | Purpose |
|----------|---------|
| `RESEND_API_KEY` | Send + receive via Resend |
| `MAIL_DOMAIN` | Domain verified in Resend |
| `ADMIN_RECOVERY_EMAIL` | Password-reset delivery |
| `SECRET_KEY` / `APP_ENCRYPTION_KEY` / `BOOTSTRAP_TOKEN` | Generated in production |
| `PUBLIC_URL` | Public origin (webhooks, links) |
| `DATA_ROOT` | SQLite + mail blobs (default `/data` in Docker) |

Optional: `DATABASE_URL` for Postgres; `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` for push.

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

- **[Railway template](https://railway.com/deploy/mailstead)** — one service, volume, generated secrets
- [Manual Railway setup](docs/deploy-railway.md)
- [Operations](docs/operations.md) — backups, upgrades, quotas

Publishing or customizing the marketplace template: [Railway template composer](docs/railway-template.md).

## Marketing site

The public site for mailstead.app is a separate static build in [`marketing/`](marketing/README.md). It does not serve the webmail app.

```bash
cd marketing && npm install && npm run build && npm run check
```

## Documentation

| Doc | For |
|-----|-----|
| [Local development](docs/development.md) | Setup, worker, layout, screenshots |
| [Deploy on Railway](docs/deploy-railway.md) | Template + manual service |
| [Operations](docs/operations.md) | Backups, Postgres move, quotas |
| [Railway template](docs/railway-template.md) | Composer JSON, icons, marketplace |
| [Roadmap](ROADMAP.md) | Shipped vs planned |
| [Contributing](CONTRIBUTING.md) | PRs and tests |
| [Security](SECURITY.md) | Vulnerability reports |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bugs and ideas: [GitHub Issues](https://github.com/mabounassif/mailstead/issues).

## License

[MIT](LICENSE)
