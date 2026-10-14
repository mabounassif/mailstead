---
layout: ../../layouts/Article.astro
slug: custom-domain-email-no-extra-monthly-cost
section: guides
title: Can custom-domain email have no extra monthly cost?
description: Marginal cost and total cost are different. A worked example shows when the extra monthly bill can be zero, and when it cannot.
h1: Can custom-domain email have no extra monthly cost?
intent: Explain conditional zero incremental spend without a forever-free claim.
published: "2026-10-14"
updated: "2026-10-14"
sourceChecked: "2026-10-14"
author: mabounassif
---

Sometimes the extra line on this month’s card is $0. The cost of having custom-domain email is not. Those are different questions. This page answers the first one with conditions you can check, and it refuses the second as a slogan.

Nothing here is a measured story about a particular production mailbox. Usage, the Railway invoice, and the date of that usage were not recorded in the repository, so this article does not describe one person’s bill as a case study.

## Marginal cost and total cost

Total cost is everything required: the domain renewal, the hosting plan you already pay or would have to start, Resend, backups, and time. Marginal cost is what changes because you added Mailstead.

| You already have | Adding Mailstead changes the monthly card when |
| --- | --- |
| A domain | It doesn’t, until the year rolls over. Amortize the renewal if you want it in a monthly total. The [calculator](/pricing/#calculator) divides the annual price by 12 |
| Railway Hobby at $5, with unused included usage | Hosting increment is $0 while this service’s measured usage fits in the unused credit. Hobby includes $5 of usage. The credit resets each cycle and does not roll over |
| Nothing on Railway | You pay at least the Hobby fee, $5, even if resource usage is $1 |
| Resend Free, and this month stays within 3,000 emails and 100 on the busiest day | Provider increment is $0. Received mail counts |
| More mail than that | Provider increment is at least the Pro fee, $20 for 50,000 emails |

Sources, checked 2026-10-14: [Railway pricing](https://railway.com/pricing), [Resend pricing](https://resend.com/pricing).

## A conditional example, in USD

Assume the workspace already pays for Hobby, $4 of the $5 usage credit is still free, the domain renewal is already paid, backups are left at $0, and the month is 400 messages with no day above 100.

- Standalone total, as if this were the only Railway project: $5.00 hosting plus $0 Resend.
- Incremental total: $0 hosting plus $0 Resend.

The $5 did not disappear. It was already on the invoice. Call the incremental total $0. Do not call email free.

Change one assumption and the zero goes away:

| Change | Incremental provider or host |
| --- | --- |
| 3,001 messages in the month | Resend Pro at $20. Hosting can still be $0 |
| 101 messages on one day, even if the month is under 3,000 | Free is ineligible. The next included plan in this model is Pro at $20 |
| Usage of $6 and only $4 of credit left | $2 of Railway usage, plus Resend |
| A new Railway account | $5 Hobby minimum, even when usage is inside the credit |
| A domain that costs $18 per year and was not already owned | $1.50 per month if you amortize it. Google, Zoho, and Microsoft need that domain too |

Administration sits outside both totals. An hour spent on DNS is an hour, whether or not the card changed.

## What people mean by free, and what fails

Zoho’s free mail plan is $0 for up to five users on one domain in regions where it is offered, with 5 GB per user and without IMAP, POP, or ActiveSync ([Zoho pricing](https://www.zoho.com/mail/zohomail-pricing.html)). That is a hosted free tier with product limits, not an unused Railway credit. Workspace and Exchange Online Plan 1 do not have a permanent $0 custom-domain tier on the pages checked for the [cost guide](/guides/custom-domain-email-cost/).

Mailstead will not stay at a $0 provider line if the team’s mail grows. There is no load test that says 50 people fit in Resend Free. Count a month of sent plus received mail before you tell the team there is no extra charge.

The software remains $0 either way. The MIT licence is not a hosting credit.

## Sources

- Railway, [pricing](https://railway.com/pricing), Hobby fee, included usage, and the note that included usage does not accumulate, checked 2026-10-14.
- Resend, [pricing](https://resend.com/pricing), Free limits and inbound counting, checked 2026-10-14.
- Mailstead cost model, [pricing](/pricing/), same inputs as this example.
