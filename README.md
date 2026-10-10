# Mailstead

Self-hosted Resend-backed email portal (work in progress). See [PLAN.md](PLAN.md) for milestones.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
export DEBUG=1 SECRET_KEY=dev APP_ENCRYPTION_KEY=dev BOOTSTRAP_TOKEN=dev \
  RESEND_API_KEY=re_test MAIL_DOMAIN=mail.test ADMIN_RECOVERY_EMAIL=admin@test \
  DATA_ROOT=/tmp/mailstead-data PUBLIC_URL=http://localhost:8000
mkdir -p "$DATA_ROOT"
python manage.py migrate
python manage.py createcachetable
python manage.py runserver
```

Initial admin: open `/setup/<BOOTSTRAP_TOKEN>` once.

## Tests

```bash
pytest
```

Optional Postgres: `DATABASE_URL=postgres://mailstead:mailstead@localhost:5432/mailstead pytest -m postgres`

## Docker

```bash
docker compose up --build
```

Health: `GET /healthz`, readiness: `GET /readyz`.
