# Deploy on Railway

The fastest path is the published template: [Deploy Mailstead](https://railway.com/deploy/mailstead) (template code `mailstead`).

That provisions one service from this repo’s Dockerfile, a volume at `/data`, and the required variables. After deploy:

1. Wait until the healthcheck passes (`/healthz`).
2. Open `https://YOUR_DOMAIN/setup/BOOTSTRAP_TOKEN` once (`BOOTSTRAP_TOKEN` is a service variable).
3. Create users and mailboxes in **Admin** (`/admin/`).
4. Verify `MAIL_DOMAIN` in Resend (DNS) and confirm inbound webhooks (the app registers them when `PUBLIC_URL` is public).

Marketplace copy for the template lives in [`railway-template-readme.md`](railway-template-readme.md). Maintainer notes (composer JSON, icons, screenshot regen): [`railway-template.md`](railway-template.md).

## Manual service

If you are not using the template:

1. Create a service from this repo’s Dockerfile.
2. Attach a volume at `/data`.
3. Start command: `python -m mailstead.run`
4. Health check path: `/healthz` (liveness) or `/readyz` (includes worker heartbeat)
5. Set `RAILWAY_DEPLOYMENT_DRAINING_SECONDS=30`
6. Set `PUBLIC_URL=https://${RAILWAY_PUBLIC_DOMAIN}` (the template does this for you)

Required variables: `RESEND_API_KEY`, `MAIL_DOMAIN`, `ADMIN_RECOVERY_EMAIL`, plus generated `SECRET_KEY`, `APP_ENCRYPTION_KEY`, `BOOTSTRAP_TOKEN`.

See [`.env.example`](../.env.example) for optional Postgres (`DATABASE_URL`) and Web Push (`VAPID_*`). Day-two ops (backups, upgrades, quotas): [operations.md](operations.md).
