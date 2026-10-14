---
layout: ../../layouts/Article.astro
slug: mailstead-vs-mailcow
section: compare
title: Mailstead vs mailcow — API-backed webmail or a full mail server?
description: mailcow is a mail server and groupware stack. Mailstead is a webmail app that sends and receives through Resend.
h1: Mailstead vs mailcow
intent: Compare operations, protocols, and dependencies with mailcow.
published: "2026-10-14"
updated: "2026-10-14"
sourceChecked: "2026-10-14"
author: mabounassif
---

mailcow and Mailstead both end in a browser inbox. They do not start from the same machine. mailcow: dockerized is a mail server and groupware: SMTP, IMAP, POP3, antivirus, and a database stack you operate. Mailstead is one web application. Resend accepts and delivers the mail; Mailstead stores copies and shows them.

If Thunderbird, a phone’s mail app, or port 25 matters, start with mailcow or another real mail server. If those protocols are a burden you are trying to avoid, Mailstead exists for that case.

## What you run

| | Mailstead default deploy | mailcow, from the project docs |
| --- | --- | --- |
| Processes | One container. Jobs run in that process. No Redis or Celery | Docker Compose groupware. Docs name nginx, Postfix, Dovecot, Rspamd, MariaDB, Redis, and more |
| Minimum RAM | Not published as a benchmark. The app is a Django service plus a volume | 6 GiB RAM and 1 GiB swap. 8 GiB recommended for about 5 to 10 users. A site with 15 phones on ActiveSync and about 50 concurrent IMAP connections should plan 16 GiB |
| Disk before mail | Volume you attach. Railway Hobby allows up to 5 GB | 20 GiB without emails |
| Protocols | HTTPS for the app. No SMTP, IMAP, or POP3 listener | Ports 25, 465, 587, 143, 993, 110, 995, 4190, plus 80 and 443 |
| External dependency | Resend API and webhooks, or mail does not flow | Your own MTA. Docs also list update downloads, spam-list connections, and outbound SMTP |
| Licence cost | MIT, $0 | mailcow’s docs describe the software stack; this page does not restate a support contract |

mailcow source: [Prepare your system](https://docs.mailcow.email/getstarted/prerequisite-system/), checked 2026-10-14. The page says OpenVZ, LXC, and NAS appliances are unsupported, and that a correct DNS setup is required before installation. ClamAV can be disabled if RAM is tight. Those are mailcow’s words about mailcow.

Mailstead’s default path is the [Railway template](https://railway.com/deploy/mailstead): a volume at `/data`, health check at `/healthz`, bootstrap, then DNS at Resend. Railway Hobby is $5 per month including $5 of usage ([Railway pricing](https://railway.com/pricing)). That fee does not buy port 25, and many clouds block outbound port 25 anyway. Mailstead never needed it, because Resend sends the message.

## Where each design fails

mailcow fails closed when you wanted “email” but received a mail system: firewall rules, IP reputation, certificate renewals, and spam updates. The docs are frank that this is groupware, not a tiny MTA. It is the better fit when IMAP or ActiveSync is a requirement, when mail must not depend on a third-party sending API, or when you already have a VM with the RAM above and an address that can speak SMTP.

Mailstead fails closed when Resend rejects the domain, the daily or monthly quota is exhausted, or you need a desktop client. Local junk handling is a filter rule plus DMARC-fail routing. It is not ClamAV or Rspamd. There is no claim of a tested ceiling at 50 users.

You can run Mailstead beside other Railway services and keep one volume. You should not expect to run mailcow inside a small application container. The mailcow docs tell you not to put it on container platforms that are not full virtualization.

## A practical split

Use mailcow, or a hosted suite, when the mailbox has to speak IMAP. Use Mailstead when the mailbox has to be a website, the transport can be Resend, and the operator wants one service. The [deploy guide](/guides/deploy-mailstead-on-railway/) is the Mailstead procedure. It will not install Postfix.

## Sources

- mailcow documentation, [prerequisite system](https://docs.mailcow.email/getstarted/prerequisite-system/), RAM, disk, ports, and unsupported platforms, checked 2026-10-14.
- Mailstead [README](https://github.com/mabounassif/mailstead/blob/main/README.md) and [Railway deploy notes](https://github.com/mabounassif/mailstead/blob/main/docs/deploy-railway.md).
- Railway, [pricing](https://railway.com/pricing), Hobby fee and included usage, checked 2026-10-14.
