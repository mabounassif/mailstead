# Deploy on Railway

1. Create a service from this repo Dockerfile.
2. Attach a volume at `/data`.
3. Set start command: `python -m mailstead.run`
4. Health check path: `/readyz`
5. Set `RAILWAY_DEPLOYMENT_DRAINING_SECONDS=30`

Required variables: `RESEND_API_KEY`, `MAIL_DOMAIN`, `ADMIN_RECOVERY_EMAIL`, plus generated `SECRET_KEY`, `APP_ENCRYPTION_KEY`, `BOOTSTRAP_TOKEN`.

Set `PUBLIC_URL=https://${RAILWAY_PUBLIC_DOMAIN}`.

Deploy from the **mailstead** Railway template (workspace Templates or marketplace, code `_fOyE2`), or manually from this repo as below.
