# Security

## Supported versions

Security fixes are applied on the `main` branch. Deploy from a recent commit or release tag.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Email the maintainer with:

- A description of the issue and impact
- Steps to reproduce (proof of concept if possible)
- Your Mailstead version or commit SHA

You can use GitHub's [private vulnerability reporting](https://github.com/mabounassif/mailstead/security/advisories/new) if it is enabled on the repository.

We aim to acknowledge reports within a few business days.

## Secrets and deployment

Never commit `.env`, API keys, `BOOTSTRAP_TOKEN`, or TLS/SSH private keys. Use environment variables or your platform's secret store. Rotate credentials if they were ever exposed.
