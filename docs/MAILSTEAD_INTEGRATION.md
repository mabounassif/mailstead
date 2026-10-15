# Conversation integration design

Status: design draft, 2026-10-15. No bridge, routes, wire schema or protocol
conformance is implemented by this document. Track public #25 / platform #7.

## Boundaries

| Public app | Platform |
| --- | --- |
| Authenticate the local user and enforce mailbox ownership | Authenticate workspace/publisher identity and approve pairing |
| Resolve selected message/attachment references | Enforce live task/version/operation/resource grants |
| Display installed agent contacts, consent and task events | Registry, installations, durable task lifecycle and isolated runs |
| Preserve mail headers, routing, files and delivery behavior | Produce validated durable events, results and diagnostics |

The platform gateway is the authority for agent operations; the public adapter
still verifies authenticated pairing and resource ownership. No duplicated grant
store or direct database/volume sharing. No shared Resend master key or vault key.

## Contract to implement together

Before adapter code, agree a versioned schema plus valid/invalid executable
fixtures checked in both repos. Define transport, service authentication,
rotation/revocation, issuer/audience and replay protection explicitly. Do not
treat an email address or user-supplied workspace ID as proof of identity.

Pair an authenticated instance and mailbox to a platform workspace explicitly.
Bind contact to installation/pinned version, conversation to task, and opaque
resource references to the source instance and mailbox. Existing IDs occupy
different namespaces and must not be guessed or equated.

Task submission carries authenticated context, selected resource references and
an idempotency key, not the whole inbox or implicit grants. Events need unique
IDs, contract revision, task/run/installation/version correlation, durable
sequence/cursor and validated type/payload. Validate bindings on every inbound
operation; duplicate/reordered/stale events cannot expand scope or regress state.

Keep credentials outside event payloads, logs and URLs. Carry only the content
needed for the authorized operation; traces do not grant publishers access to
customer prompts, results or artifacts. Authorize artifact reads separately.

## First vertical slice

1. User selects a message and invokes an installed contact.
2. Platform persists one task and queues an isolated attempt.
3. A platform-derived card requests bounded selected-message access. The user's
   authenticated decision is validated by the platform; agent text is not consent.
4. The live gateway checks the grant and calls the scoped Mailstead adapter.
5. Conversation receives progress, waiting/resumed state and a summary/artifact.

Denial, expiry, revocation, cancellation, provider failure, disconnect and retries
are explicit states. Replay events from a persisted cursor after reconnect;
delivery retries must not create duplicate tasks or effects. Disabled/unpaired
integration leaves standalone Mailstead usable and never shows simulated success.

First release prepares a result only. Sending requires a subsequent exact-action
approval tied to payload, recipient, version and expiry, plus stable effect keys
and uncertain-outcome reconciliation. Payments and vault use remain deferred.

## Evidence required

Both sides pass the same contract fixtures and cross-tenant negative tests.
Cover pairing forgery, resource substitution, attachments, event/artifact access,
replays, stale attempts, outages, and revocation on the next operation. Verify
one real isolated test run in the conversation and existing standalone mail
behavior. Mocked adapters cannot establish runtime isolation or live readiness.
