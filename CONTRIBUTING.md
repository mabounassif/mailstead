# Contributing

Thanks for your interest in Mailstead.

## Development setup

See [README.md](README.md) for local environment variables, migrations, and running the dev server.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Optional Postgres integration tests:

```bash
DATABASE_URL=postgres://mailstead:mailstead@localhost:5432/mailstead pytest -m postgres
```

## Pull requests

1. Fork the repo and branch from `main`.
2. Keep changes focused; match existing style and patterns.
3. Add or update tests when behavior changes.
4. Ensure `pytest` passes before opening the PR.

## Documentation

Deployment and operations live under [docs/](docs/). Update them when you change env vars, health checks, or Railway template steps.
