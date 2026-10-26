# Coding-agent handoff

Read `AGENTS.md`, `docs/VISION.md`, `ROADMAP.md`, then the active issue. For the
bridge, also read `docs/MAILSTEAD_INTEGRATION.md`. Inspect current main/open PRs
before interpreting this dated snapshot as current status.

## Reviewed baseline: 2026-10-15

Public main `d63a4da` includes contact chats, Contacts / Drive navigation and the
removal of local AgentProfile. `mail/chats.py` groups email copies;
`mail/workspace_views.py` serves contacts, attachment listings, text cards and
encrypted password entries. No hosted-agent integration or durable task/event
API exists here. README/roadmap descriptions of the earlier folder UI were stale.

## Next assignments

- #25: agree the integration contract and implement the optional public bridge
  with platform #7 after platform activation #4/#5. Keep dependencies explicit;
  do not build an alternative runtime while waiting.
- #26: align public positioning, screenshots and capability claims with verified
  behavior. Preserve the custom-domain email setup path and current branding.
- Mail reliability/account isolation fixes remain valid work at any time.
- Optional: Expo client in `mobile/` for Messages, Drive, Contacts, and Settings
  via `/api/v1/`. Store publication and native push still need the operator's
  Expo, Apple, and Google accounts. See `docs/mobile.md`.

The phone app and the Django workspace both include a center review control.
“Needs you” is a local demo queue stored on the device, with pending and
reviewed decisions. It does not grant mailbox access, send mail, purchase
insurance, or call the platform.

Platform first proves signup, an actual synthetic sandbox run, diagnostics and
private publication. Public agent UI follows the integration contract. Contract
design can precede runtime completion; do not claim an end-to-end integration
from fixtures alone.

## Handoff discipline

Start from actual main, name one issue and its user-visible acceptance check,
implement and verify that slice, then open a focused PR. Record what works,
what was checked, what is unavailable and the next dependency. Update these
documents as work lands; a PR merged into a feature branch is not main/released.

Use `docs/development.md` for setup and `CONTRIBUTING.md` for checks. Preserve
mailbox isolation and send/receive semantics. Never recreate AgentProfile,
import private platform code here or execute developer code in the web worker.
