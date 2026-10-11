# Roadmap

Mailstead is a self-hosted webmail portal for small teams (about 10–50 users), built on Django and [Resend](https://resend.com). This document is the public plan; use [GitHub Issues](https://github.com/mabounassif/mailstead/issues) for specific work items.

## Shipped

- **Mailbox** — Inbox, Sent, Drafts, Archive, Junk, Trash; compose, reply, forward, attachments, search, unread state
- **Mail pipeline** — Resend webhooks, inbound ingest, outbound send, idempotent jobs, reconcile and `import_received`
- **Operations** — `/data` storage ledger, quotas, overflow, ops dashboard; Resend usage snapshots and alert records
- **Deploy** — Single-container web + worker, Docker, [Railway docs](docs/deploy-railway.md), [published template](https://railway.com/deploy/mailstead)
- **Enterprise (OSS)** — License/entitlement client, mock vendor, spam classification hooks and data-flow boundaries
- **Notifications** — Web Push + PWA install path (VAPID), per-user subscription settings
- **Account safety** — Bootstrap setup, recovery email, rate limits, session handling

## Next

| Area | Goal |
|------|------|
| Usage alerts | Email or in-app notices when thresholds fire (today: `UsageAlert` rows + minimal usage UI) |
| Enterprise spam | Production hosted classifier integration, clearer operator docs for license lifecycle |
| Provider hardening | Confirm and document Resend edge cases (custom `Message-ID`, BCC routing, quota-unretrievable mail) |
| Quality | Postgres job in CI; periodic dependency updates |

## Later

- Mailbox **aliases** and clearer multi-address routing
- **Shared mailboxes** (if demand appears)
- Richer **filter rules** UI and junk feedback loop to enterprise vendor
- Stronger **search** (full-text or indexed fields beyond current basics)
- **Import/export** improvements for migrations between hosts

## Non-goals (default deployment)

These stay out of the one-service template unless there is a strong reason to add them:

- Redis, Celery, or a separate message broker
- SMTP/IMAP server or desktop mail clients as first-class targets
- A separate frontend build (React/Vue) — server templates + HTMX remain the default
- Object storage as a hard requirement (blobs on volume / provider APIs)

## How to influence the roadmap

Open an issue with your deployment size, pain point, and whether you can contribute a PR. Security reports: see [SECURITY.md](SECURITY.md).
