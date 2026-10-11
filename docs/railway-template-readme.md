# Deploy and Host Mailstead on Railway

Self-hosted email portal for small teams, backed by [Resend](https://resend.com) for delivery and inbound mail.

## About Hosting

Mailstead runs as a single Docker service with a **persistent volume at `/data`** (SQLite database and mail blobs). A background worker process handles inbound webhooks, outbound sends, and scheduled jobs. Attach a Railway public domain; `PUBLIC_URL` is set from `RAILWAY_PUBLIC_DOMAIN`.

## Why Deploy

- **Own your mail UI** without running a full mail stack (Postfix, Dovecot, etc.)
- **Resend** handles deliverability and inbound receiving; Mailstead stores and presents mail
- **Admin + per-user mailboxes** for 10–50 users
- **Ops dashboard** at `/ops/` for storage and worker health

## Common Use Cases

- Team shared hosting on your domain via Resend
- Internal notifications inbox with a simple web client
- Staging or production portal next to your app on Railway

## Dependencies for

### Deployment Dependencies

| You provide | Purpose |
|-------------|---------|
| `RESEND_API_KEY` | Resend API (send + receive APIs) |
| `MAIL_DOMAIN` | Domain verified in Resend |
| `ADMIN_RECOVERY_EMAIL` | Password reset delivery |

Generated at deploy: `SECRET_KEY`, `APP_ENCRYPTION_KEY`, `BOOTSTRAP_TOKEN`. Optional: `DATABASE_URL` for Postgres instead of SQLite on `/data`.

## First deploy

1. Deploy and wait until **healthcheck** passes (`/healthz` recommended on Railway).
2. Open `https://<your-domain>/setup/<BOOTSTRAP_TOKEN>` once (token is in service variables).
3. Create users and mailboxes in **Admin** (`/admin/`).
4. Configure Resend DNS for `MAIL_DOMAIN` and register webhooks (scheduled job or admin).

## Volume

Do not remove the `/data` volume unless you intend to wipe mail storage.

## Health

- Liveness: `/healthz`
- Readiness: `/readyz` (includes worker heartbeat)

## Source

[GitHub: mabounassif/mailstead](https://github.com/mabounassif/mailstead)
