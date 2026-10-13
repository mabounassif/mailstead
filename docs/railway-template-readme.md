# Deploy and Host Mailstead with Railway

Mailstead is a self-hosted webmail portal for small teams. [Resend](https://resend.com) sends and receives mail; Mailstead stores messages and provides the browser UI on a single Railway service with a persistent volume.

## Screenshots

<img src="https://raw.githubusercontent.com/mabounassif/mailstead/main/docs/assets/screenshots/inbox.png" alt="Inbox" />

<img src="https://raw.githubusercontent.com/mabounassif/mailstead/main/docs/assets/screenshots/compose.png" alt="Compose" />

<img src="https://raw.githubusercontent.com/mabounassif/mailstead/main/docs/assets/screenshots/login.png" alt="Sign in" />

## About Hosting

Mailstead runs as a single Docker service with a **persistent volume at `/data`** (SQLite database and mail blobs). A background worker process handles inbound webhooks, outbound sends, and scheduled jobs. Attach a Railway public domain; `PUBLIC_URL` is set from `RAILWAY_PUBLIC_DOMAIN`.

## Why Deploy

- **Own your mail UI** without running a full mail stack (Postfix, Dovecot, etc.)
- **Resend** handles deliverability and inbound receiving; Mailstead stores and presents mail
- **Admin + per-user mailboxes** for 10–50 users
- **Ops dashboard** at `/ops/` for storage and worker health
- **Installable web app** with branded icon (header + Add to Home Screen); optional **push notifications** for new mail when VAPID keys are set

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

Generated at deploy: `SECRET_KEY`, `APP_ENCRYPTION_KEY`, `BOOTSTRAP_TOKEN`. Optional: `DATABASE_URL` for Postgres instead of SQLite on `/data`; `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY` for Web Push (iPhone: Safari → Add to Home Screen, then **Notifications** in the mail sidebar).

## First deploy

1. Deploy and wait until **healthcheck** passes (`/healthz` recommended on Railway).
2. Open `https://YOUR_DOMAIN/setup/BOOTSTRAP_TOKEN` once (token is in service variables).
3. Create users and mailboxes in **Admin** (`/admin/`).
4. Configure Resend DNS for `MAIL_DOMAIN` and register webhooks (scheduled job or admin).

## Volume

Do not remove the `/data` volume unless you intend to wipe mail storage.

## Health

- Liveness: `/healthz`
- Readiness: `/readyz` (includes worker heartbeat)

## Source

[GitHub: mabounassif/mailstead](https://github.com/mabounassif/mailstead)
