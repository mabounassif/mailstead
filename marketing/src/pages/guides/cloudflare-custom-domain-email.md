---
layout: ../../layouts/Article.astro
slug: cloudflare-custom-domain-email
section: guides
title: Connect Cloudflare DNS to Mailstead and Resend
description: Configure the mail domain and webmail hostname separately and preserve existing receiving routes.
h1: Connect Cloudflare DNS to Mailstead and Resend
intent: Configure Cloudflare DNS for custom-domain mail.
published: "2026-10-14"
updated: "2026-10-14"
sourceChecked: "2026-10-14"
author: mabounassif
---

To use `hello@example.com` in Mailstead, configure email delivery for `example.com` in Resend. To open webmail at `inbox.example.com`, configure that separate hostname in Railway. They are different DNS tasks.

## Inspect existing mail routing first

Inspect the current MX records. If the domain receives mail through another provider, plan a migration before replacing its records. Keep the current values for rollback. A pilot on a separate subdomain can preserve the existing route, but its addresses will use that subdomain.

Do not mix unrelated MX targets to try to duplicate delivery. If Cloudflare forwarding or another provider currently receives the same domain’s mail, review that configuration first. The receiving domain needs the records specified by your selected receiving provider.

## Configure the mail domain in Resend

Add the selected domain to Resend and configure both sending and receiving. Copy the exact record names, types, priorities, and values shown by Resend into Cloudflare DNS.

| Record | Purpose | Value to publish |
| --- | --- | --- |
| Receiving MX | Route incoming mail | Current Resend receiving values and priorities |
| DKIM | Verify signed outgoing mail | Domain-specific values shown by Resend |
| SPF / sending records | Authorize transport | Resend’s instructions reconciled with existing senders |
| DMARC | Authentication policy and reporting | A policy appropriate to the actual domain senders |

Do not create two SPF records at the same name, guess a DKIM target, or replace an existing DMARC policy without reviewing its effect. Follow the provider’s DNS-only requirements for mail-related hostnames where Cloudflare offers proxying.

Wait for verification. A verified sending domain does not prove that inbound receiving is configured.

## Configure the webmail hostname in Railway

Railway’s generated hostname works for the application while you test. For `inbox.example.com`:

1. Add that hostname to the Mailstead service’s custom domains in Railway.
2. Copy the exact DNS records Railway provides (including the CNAME target and any TXT verification record) into Cloudflare for the `inbox` hostname. Start DNS-only while verifying the hostname and TLS.
3. Wait for Railway to confirm the domain and HTTPS.
4. Set `PUBLIC_URL=https://inbox.example.com`. Keep `MAIL_DOMAIN=example.com` if that is your mail domain.
5. Confirm the Resend webhook points to `https://inbox.example.com/hooks/resend`.

Keep the existing website records intact. The website can stay on `example.com` while webmail runs on `inbox.example.com`.

## Verify delivery

Create the exact recipient mailbox. Check `/readyz`, receive a message from an outside account, and reply to it. Confirm external receipt. If receiving fails, inspect MX and the webhook before changing unrelated website records.

Follow the [complete setup checklist](/docs/agent-setup/) or [give the guide to your coding agent](/for-agents/).

## Sources

- [Mailstead deployment](https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md).
- [Resend custom receiving domains](https://resend.com/docs/receiving/custom-domains).
- [Cloudflare Email Routing DNS](https://developers.cloudflare.com/dns/troubleshooting/email-issues/).
- [Railway public networking](https://docs.railway.com/networking/domains/working-with-domains).
