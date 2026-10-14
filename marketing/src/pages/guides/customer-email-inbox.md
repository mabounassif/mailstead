---
layout: ../../layouts/Article.astro
slug: customer-email-inbox
section: guides
title: Give your project a customer email inbox
description: Set up a browser inbox for hello@yourdomain alongside your application, with verified receiving and replies through Resend.
h1: Give your project a customer email inbox
intent: Set up a project inbox alongside an application.
published: "2026-10-14"
updated: "2026-10-14"
sourceChecked: "2026-10-14"
author: mabounassif
---

A project website can send notifications and still have nowhere useful to read customer replies. Mailstead supplies that browser inbox: incoming mail, sent messages, drafts, attachments, and search, using Resend for transport.

A founder can create `hello@example.com`, receive a customer’s question, and reply from that address. This is a mailbox workflow. Mailstead does not claim shared ticket assignment, help-desk SLAs, or an office suite.

## Choose the address and webmail hostname

Pick the mailbox address first. `MAIL_DOMAIN=example.com` uses addresses on `example.com`; `MAIL_DOMAIN=mail.example.com` uses the subdomain. Then choose where to open webmail: a Railway hostname or a custom host such as `inbox.example.com`.

If the mail domain already has a receiving provider, review the [DNS and routing guide](/guides/cloudflare-custom-domain-email/) before changing it.

## Deploy beside your application

Deploy Mailstead as its own service using the [Railway template](https://railway.com/deploy/mailstead). Keep the persistent volume at `/data`. Supply the Resend API key, mail domain, and an external recovery email as secure variables.

Verify sending and receiving in Resend, bootstrap the first administrator, and create the exact recipient mailbox. Confirm inbound events reach the webhook at the app origin plus `/hooks/resend`.

The [full runbook](/docs/agent-setup/) gives the variables, deployment sequence, troubleshooting, and delivery checks. If a coding agent is doing the setup, [give it the guide](/for-agents/).

## Test the conversation

Send from an external account to the new address. Check that it appears in Mailstead, then reply and verify external receipt. A successful application notification does not establish that customer replies reach this inbox.

Once verified, publish the address on your website. For application-generated email, use the appropriate reply-to address when you want responses to reach this mailbox. Keep sender authentication and provider limits in mind.

## Budget for the whole inbox

Software is MIT licensed. Running cost includes hosting, transport, the domain, storage/backups, and administration. An existing Railway subscription can reduce incremental spending; it does not establish a universally free deployment. Use the [pricing calculator](/pricing/) with expected received and sent volume.

Add the users and mailboxes you need and review quotas. The project targets small teams; it has no published capacity benchmark for a specific headcount.

## Sources

- [Repository features](https://github.com/mabounassif/mailstead/blob/main/README.md).
- [Deployment guide](https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md).
- [Operations and backups](https://github.com/mabounassif/mailstead/blob/main/docs/operations.md).
