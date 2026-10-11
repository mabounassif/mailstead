# Railway template composer steps

Railway Config as Code (`railway.json`) is deprecated for new projects. Configure the template in the composer:

- Build: Dockerfile
- Start: `python -m mailstead.run`
- Healthcheck: `/readyz`
- Volume mount: `/data`
- Variables:
  - `SECRET_KEY=${{secret(64)}}`
  - `APP_ENCRYPTION_KEY=${{secret(32)}}`
  - `BOOTSTRAP_TOKEN=${{secret(32)}}`
  - `PUBLIC_URL=https://${RAILWAY_PUBLIC_DOMAIN}`
  - `RESEND_API_KEY` (deployer supplied)
  - `MAIL_DOMAIN` (deployer supplied)
  - `ADMIN_RECOVERY_EMAIL` (deployer supplied)
  - `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` (optional `${{secret(...)}}` — Web Push / iPhone Home Screen notifications; generate with `py-vapid`)
  - `PUSH_DEBOUNCE_SECONDS` (optional, default `45`)

**Template branding:** use `docs/assets/mailstead-template-logo.jpg` (same file as `core/static/mailstead/icon-source.jpg`). Regenerate PNG sizes after replacing that JPEG: `python scripts/render_app_icons.py`.

**Published template:** [Deploy Mailstead](https://railway.com/deploy/mailstead) (code `mailstead`). Also listed under [Workspace → Templates](https://railway.com/workspace/templates).

Composer should match this repo:

- Build: Dockerfile
- Start: `python -m mailstead.run`
- Healthcheck: `/healthz` (use `/readyz` only if you accept worker heartbeat requirements)
- Volume mount: `/data`
