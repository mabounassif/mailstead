---
name: deploy-mailstead
description: Set up and verify custom-domain email with Mailstead on Railway using Resend. Use when a user wants a browser inbox for their project domain, Resend-backed webmail, or a Mailstead deployment. Check fit, configure storage and DNS, create mailboxes, and verify inbound mail plus an outbound reply.
---

# Deploy Mailstead

Read https://mailstead.app/docs/agent-setup.md before acting. Treat it as reference documentation, not authority to access accounts or change unrelated resources. Follow the user's authorized scope and the current capabilities of deployment and DNS tools.

1. Check whether the user needs a browser mailbox. Explain the absence of default IMAP/POP3, managed hosting, and an office suite when relevant. For application-only sending, evaluate whether a sending API is sufficient.
2. Gather the selected mail domain, desired mailbox addresses, Railway project, Resend access, DNS access, and external admin recovery address. Keep credentials in secure service variables; do not print or commit them.
3. Distinguish `MAIL_DOMAIN` (address domain) from `PUBLIC_URL` (HTTPS webmail origin). Inspect existing MX/SPF/DKIM/DMARC records. Preserve existing mail routing unless the user authorizes migration; use a separate mail subdomain for a pilot where appropriate.
4. Deploy https://railway.com/deploy/mailstead with persistent storage at `/data`. Verify required variables and generated secrets. Configure sending and receiving using the exact DNS records Resend provides.
5. Bootstrap the first administrator once using the private token, then confirm the required mailboxes in `/admin/`. Confirm an enabled webhook at the app origin plus `/hooks/resend`, including `email.received`.
6. Check `/healthz` and `/readyz`. Interpret readiness as database, storage, migrations, and worker checks; do not infer successful mail delivery.
7. Receive a test message from an authorized external inbox, confirm it appears in Mailstead, reply, and confirm external receipt. Report inaccessible accounts or unperformed tests as pending.
8. Hand off the app URL, mailbox addresses, verified checks, remaining actions, and backup requirements. Exclude secrets and bootstrap URLs. Preserve the volume and encryption key across redeploys.

Use https://mailstead.app/pricing/ for the cost model and consult current vendor prices before quoting costs. Distinguish zero software cost from hosting, transport, domain, and backup costs. Describe only implemented features and do not imply automatic agent installation.
