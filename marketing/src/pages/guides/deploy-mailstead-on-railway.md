---
layout: ../../layouts/Article.astro
slug: deploy-mailstead-on-railway
section: guides
title: How to deploy Mailstead on Railway
description: The supported Railway template path, including the volume, bootstrap, Resend domain verification, webhooks, and a send/receive check.
h1: How to deploy Mailstead on Railway
intent: Procedural deploy guide for the published Railway template.
published: "2026-10-14"
updated: "2026-10-14"
sourceChecked: "2026-10-14"
author: mabounassif
---

Use the published template if you want the path this project documents: [Deploy Mailstead](https://railway.com/deploy/mailstead). It creates one service from the repository image, a volume mounted at `/data`, and generated secrets. It does not verify your domain, create mailboxes, or send a test message. Those remain after the container is up.

You need a Resend API key with access to send and receive, a domain whose DNS you can edit, and an address for admin password recovery. Postgres and Web Push are optional.

## After the template finishes

1. Wait until the health check passes. Liveness is `/healthz`. Readiness is `/readyz`, which also looks at the worker heartbeat.
2. Open `https://YOUR_DOMAIN/setup/BOOTSTRAP_TOKEN` once. The token is a service variable. Create the first admin there.
3. In Admin (`/admin/`), create users and mailboxes on `MAIL_DOMAIN`.
4. In Resend, verify that domain and publish the DNS records Resend shows you. The app registers its inbound webhook when `PUBLIC_URL` is a public origin. The template sets `PUBLIC_URL` from Railway’s public domain.
5. Confirm the webhook is present, then send mail to a mailbox and reply from it.

The start command in a manual service is `python -m mailstead.run`. It migrates, then runs one gunicorn worker. Jobs run in that same process. Set `RAILWAY_DEPLOYMENT_DRAINING_SECONDS=30` on a manual service. The template’s variable list is in [deploy-railway.md](https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md).

## What has to stay attached

The volume at `/data` holds SQLite and mail blobs unless you set `DATABASE_URL` for Postgres. Removing the volume wipes that store. Hobby’s platform limits include a 5 GB maximum volume and two custom domains ([Railway pricing](https://railway.com/pricing), checked 2026-10-14). The Railway-provided `*.up.railway.app` hostname is enough for `PUBLIC_URL` while you test. Your mail domain is the Resend domain, which can be different from the hostname people use to open the app.

Required variables: `RESEND_API_KEY`, `MAIL_DOMAIN`, `ADMIN_RECOVERY_EMAIL`, plus generated `SECRET_KEY`, `APP_ENCRYPTION_KEY`, and `BOOTSTRAP_TOKEN`. Web Push needs `VAPID_PUBLIC_KEY` and `VAPID_PRIVATE_KEY`. Without them, the app still runs; push stays off.

## Send and receive checklist

- Health check is green.
- You can sign in as the admin you created.
- Resend shows the domain as verified.
- A webhook points at `https://YOUR_PUBLIC_URL/hooks/resend`.
- A message from an outside account arrives in the mailbox, not only in Resend’s logs.
- A reply leaves through Resend and arrives at the outside account.
- `/ops/` shows storage and the worker. The usage panel shows Resend quota, which needs an API key that can read usage.

If inbound mail never appears, check `PUBLIC_URL`, the webhook signing setup, and that the recipient is a mailbox on `MAIL_DOMAIN`. If outbound mail fails, check the API key and the Resend quota. Received messages count toward that quota. See [Resend for a team inbox](/guides/resend-webmail/).

## Day two

Redeploying runs migrations on start and does not reset the bootstrap token. Backups are a volume backup plus `python manage.py export` for configuration and metadata, not a blob export. Details: [operations](https://github.com/mabounassif/mailstead/blob/main/docs/operations.md).

This marketing site is not the webmail service. Deploying Mailstead does not publish mailstead.app, and mailstead.app will not show your mail.

## Sources

- Repository, [docs/deploy-railway.md](https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md) and [README](https://github.com/mabounassif/mailstead/blob/main/README.md).
- Railway, [pricing and plan limits](https://railway.com/pricing), checked 2026-10-14.
- Resend, [pricing](https://resend.com/pricing), inbound mail counts toward the transactional quota, checked 2026-10-14.
