---
layout: ../../layouts/Article.astro
slug: mailstead-vs-zoho-mail
section: compare
title: Mailstead vs Zoho Mail — budget custom-domain email compared
description: Zoho’s free and annual mail plans next to a self-hosted inbox, including storage, protocols, and USD list prices.
h1: Mailstead vs Zoho Mail
intent: Compare Mailstead with Zoho Mail’s free plan and paid mail editions.
published: "2026-10-14"
updated: "2026-10-14"
sourceChecked: "2026-10-14"
author: mabounassif
---

Zoho Mail is hosted email with a free tier and low annual mail plans. Mailstead is free software that still needs a host and a transport provider. For a team that wants someone else to store the mail and is willing to prepay a year, Zoho is the direct budget comparison. For a team that wants the mailbox bytes on its own volume, Mailstead is.

USD figures come from the pricing JSON that [Zoho’s mail pricing page](https://www.zoho.com/mail/zohomail-pricing.html) requests. The visible page left price cells empty until that file loaded. Currency order in the file starts with USD. Checked 14 October 2026.

## Plans that are actually about mail

| Plan | USD | Billing | Storage and access, from the pricing page |
| --- | --- | --- | --- |
| Mail Free | $0 | — | Up to 5 users on one domain where the free plan is offered. 5 GB mail per user. IMAP, POP, and ActiveSync are not included. From the sixth user, Zoho’s tooltip says users enter a paid plan |
| Mail Lite, 5 GB | $1 per user per month | Yearly only. The monthly price cell says “Yearly subscriptions only” | 5 GB mail per user on the plan toggle |
| Mail Lite, 10 GB | $1.25 per user per month | Yearly only | 10 GB mail per user |
| Mail Premium | $4 per user per month | Yearly only | 50 GB mail per user and 50 GB retention per user, on the comparison content |
| Workplace Standard | $4 monthly, or $3 per user per month billed annually | Both | 30 GB mail per user. This is a workplace bundle, not mail-only |
| Workplace Professional | $7 monthly, or $6 per user per month billed annually | Both | 100 GB mail and 100 GB retention per user. Also a bundle |

The JSON set ids are `zplan-mail-lite`, `zplan-mail-10gb`, `zplan-premium`, `zplan-basic-monthly`, `zplan-basic-yearly`, `zplan-ultimate-monthly`, and `zplan-ultimate-yearly`. File: [mail-pricing-val.json](https://www.zohowebstatic.com/sites/zweb/json/pricing/mail-pricing-val.json).

CAD in that same file, not a conversion: Mail Lite 5 GB is 1.25, Mail Lite 10 GB is 1.57, and Mail Premium is 5, in the CAD column. Zoho’s FAQ says an annual billing discount is about 20 percent and can vary by region. For Mail Lite the file does not offer a monthly price at all.

Zoho’s FAQ also says the five free users exist only on the free mail plan. Paid plans bill every user. Five Mail Lite users are $5 per month on the annual list, paid as a year, not “five free plus a discount.”

## Where Mailstead is a different shape

| | Zoho Mail Lite | Mailstead |
| --- | --- | --- |
| Who stores messages | Zoho | Your volume, in the app |
| Per-user mail price | $1 per month, 5 GB, annual prepay | $0 software. Disk is whatever the volume costs |
| Protocols | Paid plans are the ones that move past the free plan’s missing IMAP, POP, and ActiveSync. This page does not invent which protocols Lite enables beyond leaving the free-plan restriction | No IMAP, POP, or Exchange in the default app |
| Transport quota | Zoho’s mail plans are seats and storage, not a 3,000-message Resend cap | Resend Free is 3,000 emails per month and 100 per day, received mail included |
| Five users, low volume | $0 on the free plan if you accept its limits, or $5 per month on Lite if you need what free withholds | Hobby hosting at $5 per month minimum on a new Railway account, plus Resend at $0 only while volume fits |

Workplace Standard at $3 per user per month on annual billing is the wrong row if you only wanted Mail Lite. It adds Zoho’s workplace apps. Keep it in a bundle conversation.

## When Zoho is the better fit

Choose Zoho Mail when you want hosted mail, a published per-user storage cap, and you will pay the year upfront on Lite or Premium. Choose the free plan only if five users, one domain, 5 GB, and no IMAP/POP/ActiveSync match the real constraint, and only in a region where Zoho still offers that plan. The page says the free plan is for select regions.

Choose Mailstead when the mailbox store should sit on your disk and you accept Resend as transport, a browser-only client, and your own backups. Neither option removes the domain renewal.

## Sources

- Zoho, [zohomail-pricing.html](https://www.zoho.com/mail/zohomail-pricing.html), free-plan limits and FAQ, checked 2026-10-14.
- Zoho static file, [mail-pricing-val.json](https://www.zohowebstatic.com/sites/zweb/json/pricing/mail-pricing-val.json), USD and CAD columns, checked 2026-10-14.
- Resend quota rules are summarized from [resend.com/pricing](https://resend.com/pricing), same date, and spelled out in [Can you use Resend for a team inbox?](/guides/resend-webmail/).
