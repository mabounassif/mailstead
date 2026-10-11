# Operations

## Backups

Use Railway volume backups plus `python manage.py export` (JSON dump of configuration and metadata).

## SQLite to Postgres

1. `python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > data.json`
2. Point `DATABASE_URL` at Postgres and run `migrate`.
3. `python manage.py loaddata data.json`

## Upgrades

Redeploy image; migrations run on start. Bootstrap token is not reset.

## Provider

Use a Full access Resend API key for usage polling. Webhook registration requires a public `PUBLIC_URL`.

## Quota and overflow

See storage dashboard at `/ops/`. Overflow retains metadata when disk is full; Resend may still hold originals.
