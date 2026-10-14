---
layout: ../../layouts/Article.astro
slug: agent-setup
section: docs
title: Mailstead agent setup guide for custom-domain email
description: A complete coding-agent runbook for deploying Mailstead on Railway, connecting Resend and DNS, creating mailboxes, and verifying inbound and outbound delivery.
h1: Set up custom-domain email with Mailstead
intent: Agent deployment and verification runbook.
published: "2026-10-14"
updated: "2026-10-14"
sourceChecked: "2026-10-14"
author: mabounassif
---

Mailstead is MIT-licensed self-hosted webmail. Deploy the application on Railway, store mailbox data on a persistent volume, and use Resend for inbound and outbound transport. The marketing site at mailstead.app does not host customer mailboxes.

## 1. Check the fit and gather inputs

Use Mailstead when the user wants a browser inbox for custom-domain addresses and can operate one web application. It has no default IMAP or POP3 service, office suite, or managed mailbox hosting. If the task is only application notifications, a sending API may be sufficient without Mailstead.

Gather the desired mailbox addresses, a Railway project, a Resend account/API key with the access needed for sending, receiving, and webhook management, DNS access, and an existing external recovery inbox. Use secure service variables for secrets. Never echo API keys, bootstrap tokens, passwords, or encryption keys into chat, logs, commits, or URLs in a handoff report.

Clarify two different domains:

| Input | Example | Purpose |
| --- | --- | --- |
| `MAIL_DOMAIN` | `example.com` | Addresses such as `hello@example.com`; verified for sending and receiving in Resend |
| `PUBLIC_URL` | `https://inbox.example.com` or a Railway hostname | Browser access and the Resend webhook origin |

A Railway hostname is enough for the web app. Do not change the website’s apex DNS merely to configure mail.

## 2. Inspect existing mail routing

Inspect existing MX, SPF, DKIM, and DMARC records before writing DNS. An existing Google Workspace, Microsoft 365, forwarding, or other receiving setup needs an explicit migration decision. Do not mix unrelated MX targets to try to deliver the same address to both providers. Use a separate mail subdomain for a pilot when keeping the existing inbox service.

Record the current DNS values for a possible rollback. Read the current provider-generated values; do not invent DNS targets, copy another domain’s DKIM, or create a second SPF record at the same name. See the [Cloudflare DNS guide](/guides/cloudflare-custom-domain-email/).

## 3. Deploy the application

Use the [Railway template](https://railway.com/deploy/mailstead), which creates one Docker service with a volume mounted at `/data` and generated application secrets. Check the actual template result rather than assuming each step succeeded.

| Variable | Required setup |
| --- | --- |
| `RESEND_API_KEY` | Store a real Resend API key in service variables |
| `MAIL_DOMAIN` | Set the selected mail domain, with no scheme or address prefix |
| `ADMIN_RECOVERY_EMAIL` | Use an existing inbox the admin can access |
| `PUBLIC_URL` | Set the public HTTPS origin, without a path; the template defaults to Railway’s public hostname |
| `DATA_ROOT` | `/data`, matching the persistent volume mount |
| `SECRET_KEY`, `APP_ENCRYPTION_KEY`, `BOOTSTRAP_TOKEN` | Keep the template-generated values private and preserve them across redeploys |

Optional `DATABASE_URL` changes the database to Postgres; mail blobs still need persistent storage. Optional VAPID keys enable Web Push. Neither is required for an initial inbox.

For manual deployment, use the repository Dockerfile, mount `/data`, start `python -m mailstead.run`, and set `RAILWAY_DEPLOYMENT_DRAINING_SECONDS=30`. See [the repository deployment guide](https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md).

## 4. Verify DNS in Resend

Add the chosen `MAIL_DOMAIN` to Resend. Follow its current instructions for both sending and receiving, including the receiving MX records. Sending-domain verification alone does not prove that inbound mail is enabled. Wait until Resend reports the required configuration ready.

If using a custom webmail hostname, point that separate hostname at the target Railway provides. Confirm HTTPS before changing `PUBLIC_URL`. Keep mail routing records separate from web app routing.

## 5. Bootstrap and create mailboxes

Open `/setup/<BOOTSTRAP_TOKEN>` on the deployed application, using the token from private service variables. Create the first admin. Bootstrap is a one-time operation; do not reset data or rotate secrets to regain the setup screen.

Create the required users and mailboxes in `/admin/`. Confirm exact addresses match `MAIL_DOMAIN`. Bootstrap also creates an admin mailbox when `MAIL_DOMAIN` is set; inspect it before adding duplicates. A domain or webhook does not automatically create every possible recipient mailbox.

## 6. Confirm inbound webhook registration

The application registers a Resend webhook using `PUBLIC_URL`. Confirm a webhook exists at `https://YOUR_WEBMAIL_HOST/hooks/resend` and includes `email.received`. The endpoint is `/hooks/resend`, with no trailing slash. Check the app’s operations dashboard at `/ops/` and registration logs if it is missing or disabled.

If the public hostname changes, update `PUBLIC_URL` and verify registration for the new endpoint. A stale webhook can leave the app healthy while inbound mail fails.

## 7. Check readiness and real delivery

For a shell session, set `MAILSTEAD_URL` to the public app origin, without a trailing slash, then run:

```bash
curl --fail --silent --show-error "$MAILSTEAD_URL/healthz"
curl --fail --silent --show-error "$MAILSTEAD_URL/readyz"
```

`/healthz` is liveness. `/readyz` checks the database, volume writability, migrations, and worker heartbeat. It does **not** verify DNS, provider quotas, webhook delivery, or actual inbound/outbound mail.

Complete the delivery checks with the user’s authorized external test inbox:

- Sign in and confirm the intended mailbox exists.
- Send a uniquely identifiable message from the external inbox to that mailbox.
- Confirm the message appears inside Mailstead, not merely in Resend’s event log.
- Reply from Mailstead and confirm receipt in the external inbox.
- Inspect `/ops/` and provider usage for errors or quota limits.

Do not claim these tests passed if you only verified the container. Report unavailable account access or a missing external test as pending.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Healthy app, no inbound mail | Receiving DNS, exact mailbox address, `email.received` webhook, signing configuration, worker, and quota |
| Webhook missing | Valid API key and permissions, public HTTPS `PUBLIC_URL`, registration logs |
| Reply fails | Verified sending domain, API key access, quota, outbound job/error logs |
| Readiness degraded | Database access, pending migrations, writable `/data`, worker heartbeat |
| Custom hostname gives Bad Request | `PUBLIC_URL`, Railway custom domain, and the app’s allowed-host configuration |
| Setup link no longer works | Bootstrap may already be consumed; use the existing admin account/recovery path |

## Handoff and day-two operations

Report the public app URL, mailbox addresses, which checks passed, and remaining actions. Exclude secrets and the bootstrap URL. Explain that total cost includes hosting, Resend usage, the domain, backups, and maintenance; free software does not establish a zero total bill.

Preserve the data volume and encryption key. Back up the volume as well as the metadata export: `python manage.py export` does not include mail blobs. See [operations](https://github.com/mabounassif/mailstead/blob/main/docs/operations.md).

## Sources

- [Repository deployment guide](https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md).
- [Readiness implementation](https://github.com/mabounassif/mailstead/blob/main/core/health.py).
- [Webhook registration implementation](https://github.com/mabounassif/mailstead/blob/main/provider/webhook_register.py).
- [Bootstrap implementation](https://github.com/mabounassif/mailstead/blob/main/core/bootstrap.py).
