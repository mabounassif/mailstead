# Mailstead

Self-hosted email portal for small teams, backed by [Resend](https://resend.com) for delivery and inbound mail.

## What you get

- Web mail UI (inbox, compose, search, folders)
- Django admin for users, mailboxes, and aliases
- Durable outbound/inbound pipeline with webhooks and background jobs
- SQLite on a persistent volume by default (optional Postgres via `DATABASE_URL`)
- Staff ops dashboard at `/ops/`

## First deploy

1. Deploy this template and wait until the service is healthy (`/readyz`).
2. Open `https://<your-domain>/setup/<BOOTSTRAP_TOKEN>` once to create the administrator account.
   - Find `BOOTSTRAP_TOKEN` in your service variables (generated at deploy).
3. Sign in, create additional users and mailboxes in **Admin** (`/admin/`).
4. Point your Resend domain DNS to match `MAIL_DOMAIN` and ensure `RESEND_API_KEY` has the right permissions.

## Required variables (you supply)

| Variable | Description |
|----------|-------------|
| `RESEND_API_KEY` | Resend API key |
| `MAIL_DOMAIN` | Domain configured in Resend (e.g. `mail.example.com`) |
| `ADMIN_RECOVERY_EMAIL` | Where password-reset links are sent |

## Generated at deploy

`SECRET_KEY`, `APP_ENCRYPTION_KEY`, and `BOOTSTRAP_TOKEN` are created automatically.

`PUBLIC_URL` defaults to `https://${RAILWAY_PUBLIC_DOMAIN}`.

## Volume

Mail and SQLite data live on `/data`. **Do not remove the volume** unless you intend to wipe mail storage.

## Health checks

- Liveness: `/healthz`
- Readiness: `/readyz` (database, volume, migrations, worker heartbeat)

## Docs

- [Deploy on Railway](https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md)
- [Project README](https://github.com/mabounassif/mailstead/blob/main/README.md)
