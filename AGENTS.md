# Working on Mailstead

Read `docs/VISION.md`, `docs/CURSOR_START_HERE.md`, and `ROADMAP.md` before
planning work. Read `docs/MAILSTEAD_INTEGRATION.md` for platform-facing changes.
These instructions apply to the public, self-hosted application.

## Product and ownership

- Build one conversation surface for people and installed agent contacts.
  Email is the working first transport. Preserve Messages / Drive / Contacts /
  Settings and a short, accessible, responsive flow with one primary action.
- The separate platform owns agent definitions/versions, installations,
  persistent tasks, temporary runs, consent policy, execution and diagnostics.
  This app owns the human UI, mailbox resources and email transport. Integrate
  through authenticated versioned APIs, never shared database tables or volumes.
- Do not recreate the deleted `AgentProfile` or a local execution/permission
  engine. Contacts currently derives people from mail; agent installation is
  planned. A label or navigation item does not establish backend capability.
- Preserve standalone deployment: one Docker service, local volume, SQLite or
  optional Postgres, existing Django templates/HTMX and worker. Platform pairing,
  sandboxes, object storage and a model key must not become mandatory.
- Keep mail routing, threading, reply headers, BCC privacy, attachments, search,
  quotas and existing account protections working during UI changes.

## Delivery

Work the active issue, not every item in the vision. The first integration is
issue #25; positioning follow-up is #26. Inspect current main and open PRs before
starting. Work in a branch and leave a focused PR with outcome, verification,
limitations and next slice. Update the handoff and roadmap when behavior lands.
Continue authorized reversible work without repeated confirmation; do not infer
production activation, new spending or package release from a coding task.

Scope all messages, files, contacts, counts and integration bindings to the
authenticated mailbox. Incoming content and agent output are untrusted data;
neither may create consent or external-action authority. A contact is not a user
login. Never log secrets or expose session cookies, provider/master keys or vault
keys to agents. No payment execution or password export in the initial bridge.

Mark implemented, synthetic, disabled and planned behavior honestly. Do not claim
MCP/A2A compliance or deployable agent hosting without tested implementations.
Keep public guidance free of private platform source, credentials and operational
details. Recheck official standards/provider docs when implementing adapters.

## Verification

Follow `docs/development.md` and `CONTRIBUTING.md`. Run `pytest` for application
behavior changes; add meaningful regression coverage for changed boundaries.
For UI changes, verify desktop/mobile behavior and update relevant screenshots.
For marketing changes, run `npm run check`, `npm run build`, and
`npm run check:site` in `marketing/`. Documentation-only changes need link and
consistency checks, not new tests that merely restate prose.
