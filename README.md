# Mailstead

A conversation workspace, starting with working custom-domain email backed by [Resend](https://resend.com). One Docker service, a persistent data volume, and no Redis, Celery, or separate mail server in the default stack.

**Coding agents:** start with [AGENTS.md](AGENTS.md), the [shared vision](docs/VISION.md), and [current handoff](docs/CURSOR_START_HERE.md).

The direction is conversations where people and installed agent contacts work together. This public app owns the human interface and mail resources; a separate private platform owns agent publishing, permissions and isolated execution. The bridge is planned, not available here yet. Standalone email remains supported. See the [integration design](docs/MAILSTEAD_INTEGRATION.md).

<p align="center">
  <img src="docs/assets/screenshots/inbox.png" alt="Mailstead inbox" width="920" />
</p>

**Stack:** Django 5.2, HTMX, SQLite (or Postgres via `DATABASE_URL`), in-process background jobs. Optional Expo client in [`mobile/`](mobile/README.md) for iOS and Android (native screens over `/api/v1/`; see [docs/mobile.md](docs/mobile.md)). The website stays server-rendered.

## Features

- Contact and group conversation views with optional subjects, compose, reply, forward, attachments and search; underlying mail folders and delivery records remain
- Messages / Drive / Contacts / Settings navigation; Drive lists mail attachments, Contacts derives people from existing messages
- Settings includes text-card Wallets and encrypted password entries; these do not provide payment execution or an agent credential broker
- Inbound mail via Resend webhooks; outbound via the Resend API
- Per-mailbox quotas and a Resend usage panel
- Ops dashboard at `/ops/` (storage, worker, webhooks)
- Installable web app; optional Web Push when VAPID keys are set
- Railway-ready: `/healthz`, `/readyz`, volume at `/data`

## Custom-domain email setup

Deploy on [Railway](https://railway.com/deploy/mailstead), then follow the [complete setup and verification guide](https://mailstead.app/docs/agent-setup/). Setting up with a coding agent? Use the [agent handoff](https://mailstead.app/for-agents/), [Markdown runbook](https://mailstead.app/docs/agent-setup.md), or the optional [deployment skill](marketing/public/skills/deploy-mailstead/SKILL.md). Confirm both inbound delivery and an outbound reply before calling an inbox ready.

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

These captures show earlier mail layouts. Current navigation is Messages / Drive / Contacts / Settings; screenshot refresh is tracked in #26.

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
| [Product direction](docs/VISION.md) | Shared vision and repository responsibilities |
| [Coding-agent handoff](docs/CURSOR_START_HERE.md) | Current baseline, next issues and checks |
| [Integration design](docs/MAILSTEAD_INTEGRATION.md) | Planned optional agent-contact bridge |
| [Contributing](CONTRIBUTING.md) | PRs and tests |
| [Security](SECURITY.md) | Vulnerability reports |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bugs and ideas: [GitHub Issues](https://github.com/mabounassif/mailstead/issues).

## License

[MIT](LICENSE)
