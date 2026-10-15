# Contributing

Thanks for your interest in Mailstead.

Start with [AGENTS.md](AGENTS.md), [product direction](docs/VISION.md), and the
[coding-agent handoff](docs/CURSOR_START_HERE.md). Platform integration follows
the [shared design draft](docs/MAILSTEAD_INTEGRATION.md); the public app retains
its standalone deployment path.

## Development setup

Follow **[Local development](docs/development.md)** for environment variables, migrations, the worker, tests, and project layout.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Pull requests

1. Fork the repo and branch from `main`.
2. Keep changes focused; match existing style and patterns.
3. Add or update tests when behavior changes.
4. Ensure `pytest` passes before opening the PR.
5. If you change the mail UI, regenerate screenshots:

   ```bash
   pip install -e ".[screenshots]"
   playwright install chromium
   python scripts/capture_template_screenshots.py
   ```

## Documentation

Keep the [README](README.md) as the onboarding hub. Detail lives under [docs/](docs/):

- [Local development](docs/development.md)
- [Deploy on Railway](docs/deploy-railway.md)
- [Operations](docs/operations.md)
- [Railway template](docs/railway-template.md)

Update [ROADMAP.md](ROADMAP.md) when priorities shift. Update docs when you change env vars, health checks, or Railway template steps.
