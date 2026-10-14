---
layout: ../../layouts/Article.astro
slug: custom-domain-email-cost
section: guides
title: What does custom-domain email actually cost?
description: A buyer’s guide to custom-domain email covering subscriptions, self-hosting, the domain, message volume, backups, and administration.
h1: What does custom-domain email actually cost?
intent: General cost guide for custom-domain email, before choosing a product.
published: "2026-10-14"
updated: "2026-10-14"
sourceChecked: "2026-10-14"
author: mabounassif
---

Custom-domain email is the address `you@yourdomain`. The invoice is rarely one line. You pay for a domain, for someone to accept and deliver mail, for a place to read it, and for the time to keep that arrangement working.

This guide is for people comparing a hosted suite with running their own webmail. Amounts are USD list prices checked on 14 October 2026. They are not a quote for your renewal.

## The pieces that show up on a bill

| Piece | What it pays for | How it usually scales |
| --- | --- | --- |
| Domain | The name in the address | A yearly registrar fee, whether you use Google or a server you run |
| Seats or mailboxes | The right to have a person or a shared address | Hosted suites often bill a licence per user. A shared address is not automatically another seat; read that vendor’s policy |
| Transport | Sending and receiving on the public internet | Included in most suites. With Mailstead it is a separate Resend plan, and received mail counts toward the quota |
| Storage | Mailbox contents and file retention | Pooled gigabytes per user at Google, per-user caps at Zoho, or your own disk for a self-hosted app |
| Administration | DNS, accounts, backups, failures | A suite hides most of it. Self-hosting puts it on your calendar |

Mailstead’s own software is $0 under the MIT licence. That line does not include Railway, Resend, or the domain. The [pricing page](/pricing/) separates a new hosting bill from the extra cost on a hosting account you already pay for.

## Hosted mail, priced as licences

Google Workspace Business Starter is $7 per user per month on the annual plan ($84 per user per year) or $8.40 per user per month with no annual commitment. Both figures are Google’s published US list prices. Storage on Starter is 30 GB pooled per user. Business plans stop at 300 users. The public pricing page has also shown an introductory discount for new customers; this guide uses the standard list, because an introduction is not the renewal price. Source: [Flexible and annual plans](https://knowledge.workspace.google.com/admin/billing/compare-flexible-and-annual-fixed-term-payment-plans), checked 2026-10-14.

Microsoft’s US English page lists Exchange Online (Plan 1) at $4 per user per month, paid yearly. That is hosted mail, not the Office bundle. Microsoft 365 Business Basic is listed at $6 per user per month, paid yearly, and adds web apps, Teams, and file storage. A month-to-month Microsoft price was not on the pages checked, so it is not stated here. Sources: [Exchange Online](https://www.microsoft.com/en-us/microsoft-365/exchange/exchange-online) and [Business Basic](https://www.microsoft.com/en-us/microsoft-365/business/microsoft-365-business-basic), checked 2026-10-14.

Zoho’s pricing JSON, which the mail pricing page loads, lists Mail Lite (5 GB) at $1 per user per month and marks monthly billing as yearly-only. Mail Premium is $4 per user per month, also yearly-only, with 50 GB of mail and 50 GB of retention on the comparison tables. The free plan is $0 for up to five users on one domain where Zoho offers it, with 5 GB per user, and the page says IMAP, POP, and ActiveSync are not included. Sources: [Zoho Mail pricing](https://www.zoho.com/mail/zohomail-pricing.html) and the [pricing JSON](https://www.zohowebstatic.com/sites/zweb/json/pricing/mail-pricing-val.json) it requests, checked 2026-10-14.

Ten Business Starter users on the annual list is $70 per month before tax. Ten Exchange Online Plan 1 users on the yearly list is $40. Ten Zoho Mail Lite users is $10, prepaid as a year. None of those totals include your domain.

## Self-hosting the inbox, not the mail server

Mailstead is one Docker service. It stores mail. [Resend](https://resend.com/pricing) sends and receives it. Resend Free is $0 for 3,000 emails a month and 100 a day. Crossing either limit means a paid plan; Pro starts at $20 per month for 50,000 emails. A team of 50 can miss the free tier on volume alone.

[Railway Hobby](https://railway.com/pricing) is $5 per month and includes $5 of resource usage. If measured usage stays inside that credit, the hosting line stays $5. Usage above the credit is billed at Railway’s resource rates. That is a new account. Someone who already pays for Hobby and still has unused credit may add no hosting dollars for a small service. The [calculator](/pricing/#calculator) asks for that unused credit so the two cases stay separate.

## Worked month, labelled as an illustration

Assume 10 mailboxes and 20 messages each, sent and received together: 200 messages. The busiest day, if traffic is even across 30 days, is 7 messages. Resend Free covers that. A new Railway Hobby account with $3 of usage still costs $5, because the subscription is the minimum. Optional backups are extra and were left at $0. Domain renewal is your registrar’s number, divided by 12 if you want a monthly view.

The same 10 people on Workspace Business Starter’s annual list is $70 before the domain. The products are not equivalent: Starter includes Gmail’s suite, and Mailstead does not.

Change the illustration to 10,000 messages in a month and Resend Free no longer fits. The model then uses Pro at $20. Headcount did not cause that. Volume did.

## Backups and time

Mailstead’s operations notes recommend volume backups plus `python manage.py export`. The export command writes portal metadata, not the mail blobs. Budget a backup you can restore, or accept the risk. Put administration next to the invoice as hours times a rate. A suite still needs an admin for users and DNS; a self-hosted app also needs deploys and a look at disk and provider quotas.

## When a subscription is the better purchase

Buy a suite if you need calendars, office files, a vendor spam filter with a published efficacy claim, desktop mail clients, or a contract and support desk. Buy hosted mail if you will not operate an application. Use the comparisons for [Workspace](/compare/mailstead-vs-google-workspace/), [Microsoft 365](/compare/mailstead-vs-microsoft-365/), [Zoho](/compare/mailstead-vs-zoho-mail/), and [mailcow](/compare/mailstead-vs-mailcow/) when you already know which alternative you are weighing.

## Sources

- Google, [compare Flexible and annual plans](https://knowledge.workspace.google.com/admin/billing/compare-flexible-and-annual-fixed-term-payment-plans), checked 2026-10-14.
- Microsoft, [Exchange Online (Plan 1)](https://www.microsoft.com/en-us/microsoft-365/exchange/exchange-online) and [Business Basic](https://www.microsoft.com/en-us/microsoft-365/business/microsoft-365-business-basic), checked 2026-10-14.
- Zoho, [Mail pricing](https://www.zoho.com/mail/zohomail-pricing.html) and [mail-pricing-val.json](https://www.zohowebstatic.com/sites/zweb/json/pricing/mail-pricing-val.json), checked 2026-10-14.
- Resend, [pricing](https://resend.com/pricing), checked 2026-10-14. Received emails count toward the transactional quota.
- Railway, [pricing](https://railway.com/pricing), checked 2026-10-14.
- Mailstead [LICENSE](https://github.com/mabounassif/mailstead/blob/main/LICENSE) and [operations](https://github.com/mabounassif/mailstead/blob/main/docs/operations.md).
