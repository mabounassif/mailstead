Build a new standalone project: a lightweight, self-hosted email portal built around Resend, designed for easy deployment as a Railway template.

The intended scale is 10–50 users with modest email traffic. Prioritize low memory usage, modest disk requirements, mature dependencies, and straightforward maintenance.

The product has a useful free core and optional licensed enterprise services provided by us. Purchasing/activating a license should unlock supported paid capabilities immediately without redeploying the portal. Advanced spam filtering is the first paid capability. Keep the client independent of the filtering engine used by our hosted service.

This document is the complete project specification. Follow the active mode: in Plan mode, produce a concise implementation plan; in execution mode, implement the requested milestones through verification. Make reasonable decisions and record important assumptions.

**1. Architecture**

Use Django 5.2 LTS on a current supported patch release, Django templates with HTMX, Django's authentication/sessions/admin, and the official Resend Python SDK.

Default to SQLite on a persistent Railway volume at /data. Support PostgreSQL when DATABASE_URL is supplied, using the same models and migrations. I may connect an existing Railway Postgres instance; other deployers must be able to deploy without Postgres.

The default deployment requires one application service and one persistent volume. Use a durable database-backed job queue and one bounded worker in that service. Manage the web/worker lifecycle explicitly, with graceful shutdown and restart recovery.

Keep Redis, Celery, a separate frontend runtime, object storage, and SMTP/IMAP servers out of the default deployment. This is a browser portal.

Target approximately 128–256 MB steady memory. Bound message sizes, processing concurrency, retries, and temporary storage. Report measurements where available and distinguish estimates.

Before implementing provider-specific behavior, verify current official Resend and Railway documentation. Prefer a few focused modules and well-maintained libraries over a general-purpose framework for plugins or jobs.

**2. Core mailbox**

Each user gets an address such as `user@mail.example.com`. Make the domain configurable.

Build a clean, responsive interface with Inbox, Sent, Drafts, Archive, Junk, and Trash; compose/reply/reply-all/forward; attachments; unread state; pagination; basic sender/recipient/subject/body search; and mailbox storage usage.

A plain text composer is sufficient initially. Use standard Message-ID, In-Reply-To, and References headers for threading. Respect Reply-To, avoid duplicate reply-all recipients, and protect BCC information.

All core mailbox functions, storage reporting, Resend usage reporting, and account management must work without an enterprise license.

**3. Users and administration**

Use Django admin for account management, with a small custom operations dashboard where needed.

Admins can create/disable users, assign mailbox addresses and aliases, set quotas, reset passwords, inspect failed jobs and delivery status, manage overflow, and activate enterprise services.

Keep login identity, mailbox address, and external recovery email separate. Recovery must work when the user cannot access the portal mailbox. Public registration is disabled.

Create the initial administrator once on first startup. Use a generated one-time setup credential/token, require password setup, and disable bootstrap access after completion. Never log credentials or reset them on redeployment.

Use Django's password and recovery machinery, secure sessions/cookies, CSRF protection, expiring reset tokens, login/reset rate limits, and session invalidation on password resets.

**4. Dedicated email storage and accurate dashboards**

Dedicate /data/mail to email blobs and enforce a configurable global email storage budget. Keep database/support files separately under /data. A directory and application budget are sufficient; do not require physical partitioning.

Define and display distinct quantities:
- Physical volume capacity, physical used space, and currently usable free space.
- Global email budget, actual email storage consumed, pending reservations, overflow consumption, and email capacity remaining.
- Quotas allocated to mailboxes and capacity still available to allocate.
- Each mailbox's charged usage, quota, remaining allowance, and percentage used.

Read filesystem statistics for the mounted data volume, not the container's ephemeral filesystem. Verify whether those statistics reflect Railway's provisioned volume limit. Support a clearly labeled configured capacity limit if necessary; distinguish measured values from configured values. Do not invent Railway capacity data.

Reserve headroom for the database, indexes, temporary files, and bounded overflow. Effective writable email capacity must respect both the email budget and usable physical free space after the reserve.

Default each mailbox to 250 MB, configurable globally and individually. Admins see all mailbox usage; users see only their own. Warn at configurable thresholds, initially 80%, 90%, and 100%. Include usage bars, bytes remaining, and last-updated timestamps.

Count retained bodies, MIME originals, attachments, drafts, Sent, Junk, and Trash consistently. Explain logical mailbox charges versus physical storage if deduplication or compression causes them to differ. Avoid unnecessary duplication.

Reserve capacity atomically before writes; handle concurrent operations, failed writes, purges, crashes, and orphaned files. Maintain counters for ordinary requests and reconcile periodically without scanning the entire volume on every page view.

Prevent accidental allocation beyond the global budget by default. Quota reductions below current usage should produce an explicit over-quota state rather than delete mail.

Implement bounded, admin-visible overflow with warnings, expiry behavior, and recovery after space is freed. Never silently drop messages. Quarantine and unknown-recipient handling must also have storage limits.

Resend already accepted incoming mail before delivering the webhook. A webhook error cannot reject that email through SMTP. Make this limitation explicit in full-mailbox handling.

**5. Resend sending, receiving, and retention**

The deployer's `MAIL_DOMAIN` may already be configured for receiving in Resend. Verify sending capability separately and support other domains through configuration.

For inbound mail:
- Verify signatures against the raw webhook body.
- Persist a deduplicated job before acknowledging success.
- Retrieve and store the full message and attachment bytes.
- Mark archival complete only after required content is safely persisted.
- Retry transient failures with backoff and bounded concurrency.
- Periodically reconcile received messages to recover missed webhooks.
- Provide an initial import of history still available from Resend.
- Verify routing semantics, including aliases and BCC, using authoritative provider data.

Keep original MIME available for export and filtering. Stored messages must remain accessible independently of Resend retention and expiring download URLs.

For outbound mail, persist before sending, enforce authorized From addresses, use Resend idempotency keys, track provider identifiers and delivery states, and reconcile uncertain outcomes. Do not blindly resend after the provider's idempotency window expires.

Respect current API rate limits. Support idempotent automatic webhook registration once the public URL exists, storing its identifier and signing secret.

**6. Resend account subscription and quota visibility**

Provide an admin Resend account panel using the documented GET /usage endpoint with the required API-key permissions. Verify the current response schema and SDK support; use a small REST fallback if the SDK lacks a documented endpoint.

Show daily and monthly email usage, sent/received breakdowns, limits, remaining allowance, reset timestamps, and API rate limits. Show other returned quotas in a secondary view where relevant.

Treat these as account/team-wide provider counters: they may include other applications using the same Resend account. If showing portal-only counts, label them separately.

Fetch usage periodically with bounded polling, cache the last successful snapshot, provide manual refresh, and show freshness/error state. Preserve a stale snapshot with a clear warning if refresh fails. Missing data means unknown, not zero. Handle null limits as uncapped where documented.

Display subscription/plan identity only if supplied by an official API. The current documented usage response provides counters and limits, not a plan-name field: verify this before coding. If an authoritative plan name is unavailable, allow an admin-set subscription label and mark its source clearly. Do not present a guess from quota values as a verified subscription.

Notify admins at configurable warning thresholds and when a quota reaches/exceeds its allowance. Deduplicate alerts, reset them appropriately across provider periods, and retain in-app notices when notification email cannot be sent.

Distinguish quota allowance reached from provider sending actually blocked. Paid overages may be enabled; do not assume a reached allowance always stops delivery. Support an optional local send budget to avoid unwanted spending, and display provider quota failures without losing queued mail.

References to verify:
https://resend.com/docs/api-reference/usage/retrieve-usage
https://resend.com/changelog/account-usage-api

**7. Enterprise licensing and vendor-hosted services**

Provide an admin Enterprise page showing license status, enabled capabilities, expiry where applicable, service availability, and activation/refresh controls.

Use an opaque license/activation credential to contact our configurable HTTPS enterprise API. Exchange it for installation-scoped service credentials and versioned entitlements. Persist an installation identifier and enforce customer/domain scope and service limits on the vendor side.

After valid activation or an entitlement upgrade, already-supported paid capabilities become usable immediately, without restarting or redeploying. Keep licensed, configured, and healthy states distinct. Future client UI features may require a client upgrade; do not imply arbitrary new client code appears through activation.

Keep adapters engine-neutral. The portal sends the required message data to our licensed spam-filtering service and receives a structured verdict, score, reasons, and service/version metadata. Our server may use any engine internally. Do not lock the portal to Rspamd or require customers to deploy a scanner.

Show that enabling hosted filtering sends email content to our service. Never send the customer's Resend API key, passwords, or unrelated account data to that service.

Separate classification from mailbox policy. Persist email before scanning; keep unavailable scans pending with retries and an explicit fallback policy. Save spam/not-spam feedback for local actions and optional vendor learning.

Use trusted server responses and established signing/verification libraries if caching signed entitlements. Keep signing private keys exclusively on the vendor side. Cache entitlement state with explicit validity and bounded outage grace; support activation, expiration, revocation, and upgrades.

Enforce paid API access on the hosted service for every request. Local feature flags and signature checks alone cannot make a modifiable self-hosted client tamper-proof. Core mail must remain functional when a license is absent, expired, revoked, or the vendor is unavailable. Preserve stored messages and prior scan results.

Implement the portal's license client, entitlement checks, enterprise adapter, documented versioned API contract, and a small runnable mock vendor service for integration tests/demo. Production billing, payment processing, license issuance infrastructure, and the production filtering backend are separate future work. The mock must never be presented as working production spam detection. State what remains necessary for a real paid launch.

Include basic local sender/domain rules, Junk actions, and trusted Resend authentication signals in the free core. Keep future paid attachment scanning, policy management, and reporting possible through focused adapters. Avoid downloading and executing arbitrary plugins.

**8. Security and operational behavior**

Sanitize and sandbox email HTML, disable remote images by default, and handle inline content safely. Authorize every message, search, attachment, and export against mailbox ownership. Prevent path traversal and redact secrets and email content from routine logs.

Keep all provider/service credentials server-side. Bound request sizes, temporary files, network timeouts, and concurrency. Expose operational status without leaking mailbox contents.

Core ingestion, outgoing delivery, storage accounting, quota monitoring, and license refresh must survive service restarts.

**9. Deployment and documentation**

Provide a production Dockerfile, startup migrations after volume mount, health/readiness endpoints, Railway configuration, local development setup, sample environment file, and reproducible template instructions.

Required deployment inputs should be approximately RESEND_API_KEY, MAIL_DOMAIN, and ADMIN_RECOVERY_EMAIL. Generate stable application secrets and one-time bootstrap credentials through the template. Derive/configure the public URL appropriately.

Optional settings include DATABASE_URL, default mailbox quota, global email budget, physical capacity override, disk reserve, size/overflow limits, usage refresh intervals, ENTERPRISE_API_URL, and enterprise credentials.

Document backups and restore, SQLite-to-Postgres migration if supported, exports, upgrades, volume resizing, provider permissions, DNS, quota behavior, enterprise data flow, and service outages. Do not claim a Railway template was published unless it actually was.

Keep core and enterprise service responsibilities explicit. Report unresolved provider API limitations instead of inventing integrations.

**10. Verification and implementation sequence**

Write meaningful tests for mailbox/attachment/BCC isolation, password recovery and bootstrap, webhook signatures/deduplication, partial downloads and restarts, outbound idempotency, HTML/path safety, quota races and accounting reconciliation, real disk exhaustion, and bounded overflow.

Test account-wide Resend usage, null/unknown/stale limits, alerts/reset behavior, provider quota errors/overages, and plan-name fallback.

Test license activation, upgrades, expiration/revocation, spoofed/invalid entitlements, vendor downtime, customer scope, remote authorization contracts, and core operation without enterprise services.

Use mocked providers and the mock enterprise service in automated tests. Verify both database backends where available and state any untested claims. Include an end-to-end smoke test and basic memory measurements.

Plan and implement in five reviewable milestones:
1. Foundation, deployment skeleton, users, admin, and bootstrap.
2. Durable sending/receiving, local retention, and mailbox interface.
3. Global/per-user storage enforcement and operations dashboard.
4. Resend account usage, subscription labeling, and alerts.
5. Enterprise client/mock contract, final verification, and template documentation.

Maintain a compact implementation plan and progress file, with decisions, completed checks, and remaining work. Complete each requested milestone through tests and a concise handoff. Prepare deployment without changing live accounts, DNS, or existing services.

