# Railway template

Published: [Deploy Mailstead](https://railway.com/deploy/mailstead) (code `mailstead`).

Source of truth for the composer canvas: [`railway/mailstead.serialized-config.json`](../railway/mailstead.serialized-config.json).

## Service: mailstead

| Setting | Value |
|---------|--------|
| Source | `https://github.com/mabounassif/mailstead` (Dockerfile) |
| Start | `python -m mailstead.run` |
| Healthcheck | `/healthz` |
| Volume | `/data` |
| Icon | `docs/assets/mailstead-template-icon.png` (transparent PNG on GitHub raw URL in JSON) |

## Variables

All template variables must have a **description** in the composer. Defaults and copy live in `railway/mailstead.serialized-config.json`.

| Variable | Required | Notes |
|----------|----------|--------|
| `RESEND_API_KEY` | yes | Resend dashboard |
| `MAIL_DOMAIN` | yes | Verified in Resend |
| `ADMIN_RECOVERY_EMAIL` | yes | Password reset delivery |
| `SECRET_KEY` | yes | `${{secret(64)}}` |
| `APP_ENCRYPTION_KEY` | yes | `${{secret(32)}}` |
| `BOOTSTRAP_TOKEN` | yes | `${{secret(32)}}` |
| `PUBLIC_URL` | yes | `https://${{RAILWAY_PUBLIC_DOMAIN}}` |
| `DATA_ROOT` | yes | default `/data` |
| `RAILWAY_DEPLOYMENT_DRAINING_SECONDS` | yes | default `30` |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | optional | Web Push |
| `PUSH_DEBOUNCE_SECONDS` | optional | default `45` |

## Branding

- **Template card + service icon:** 512×512 PNG with transparent background — `docs/assets/mailstead-template-icon.png`.
- Regenerate from logo JPEG: `python scripts/render_app_icons.py` (requires `pip install pillow` or dev extras).

## Maintainer sync

```bash
python scripts/sync_railway_template.py              # validate JSON
python scripts/sync_railway_template.py --publish-metadata   # CLI: readme + marketplace image
```

Railway’s public API does not update `serializedConfig`; after changing the JSON, open **Workspace → Templates → mailstead → Edit** and align icons, defaults, and variable descriptions (or import via composer if available).
