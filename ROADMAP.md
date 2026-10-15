# Roadmap

Mailstead is becoming a conversation workspace for people and agents, starting
with working self-hosted custom-domain email. Read [the vision](docs/VISION.md)
and [coding-agent handoff](docs/CURSOR_START_HERE.md). This public app owns the
interface and mail resources; the separate platform owns agent publication,
authority and execution. Planned features below are not availability claims.

## Shipped

- **Conversations** — Contact/group chat views, optional subjects and subject filters, compose, reply, forward, attachments, search, unread state; mail folders remain underlying records
- **Navigation** — Messages / Drive / Contacts / Settings; people derived from mail, attachment listing, text-card Wallets and encrypted password entries in Settings. Local AgentProfile removed. No agent installs, payments or credential broker yet.
- **Mail pipeline** — Resend webhooks, inbound ingest, outbound send, idempotent jobs, reconcile and `import_received`
- **Filtering** — Local filter rules and junk folder; DMARC-based junk routing
- **Operations** — `/data` storage ledger, quotas, overflow, ops dashboard; Resend usage snapshots and alert records
- **Deploy** — Single-container web + worker, Docker, [Railway docs](docs/deploy-railway.md), [published template](https://railway.com/deploy/mailstead)
- **Notifications** — Web Push + PWA install path (VAPID), per-user subscription settings
- **Account safety** — Bootstrap setup, recovery email, rate limits, session handling

## Next

1. Platform activation: signup on main, isolated synthetic run + observability
   (platform #4), then private artifact publication (platform #5).
2. [#25](https://github.com/mabounassif/mailstead/issues/25): optional bridge with
   platform #7. Agree contract/fixtures first, then selected-message consent,
   agent contact, task progress and result in one conversation.
3. [#26](https://github.com/mabounassif/mailstead/issues/26): align positioning,
   exports and screenshots with verified product behavior.

The bridge is disabled by default and must preserve standalone deployment.
Runtime/permission logic belongs in the platform. The existing reliability
backlog remains valid alongside those product priorities:

| Area | Goal |
|------|------|
| Usage alerts | Email or in-app notices when thresholds fire (today: `UsageAlert` rows + minimal usage UI) |
| Provider hardening | Confirm and document Resend edge cases (custom `Message-ID`, BCC routing, quota-unretrievable mail) |
| Quality | Postgres job in CI; periodic dependency updates |

## Later

- Mailbox **aliases** and clearer multi-address routing
- **Shared mailboxes** (if demand appears)
- Richer **filter rules** UI and junk feedback
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
