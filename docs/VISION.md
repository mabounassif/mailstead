# Mailstead product direction

Alignment revision: 2026-10-15. This describes the target; the README and tested
code describe availability. Mailstead remains the working name.

Mailstead is a place where people and their agents exchange information and get
work done together. A person or agent is a contact; conversations hold messages,
selected files, durable tasks, permission decisions and results. An outside email
or a user request can become work, with explicit authority for what happens next.
Email is the first transport. A custom domain is useful, but is not intended to
be a prerequisite for a future platform identity.

## Two repositories, one experience

| Repository | Responsibility |
| --- | --- |
| `mailstead` (public) | Conversation UI, human contacts, email transport, mailbox-owned resources, optional integration adapter |
| `mailstead-platform` (private) | Developer onboarding, registry and immutable artifacts, installations, persistent tasks, temporary sandbox runs, permission gateway, run diagnostics |

The platform is a separate service. Public Mailstead continues to work on its
own. Never create two task state machines, two permission engines, or shared
database access to make integration convenient.

## First developer success

A fresh developer should go from signup to a privately published runnable agent
and a successful inspectable run in five minutes without operator assistance.
The browser path is primary: GitHub sign-in, automatic workspace, agent name,
invoice starter, synthetic input, bounded consent, run output/timeline, private
publication. No manual UUID/digest, admin setup, model key, billing setup or
separate observability vendor for this first experience. The five-minute goal
requires a provisioned service and must be measured, not inferred from tests.

CLI commands such as `login`, `init`, `dev`, `deploy`, and `logs --follow` are a
later optional developer interface to the same APIs. They are not available
commands or a reason to make terminal installation part of signup.

## First customer success

Select one invoice in a Mailstead conversation, ask an installed agent contact
to prepare it, approve access to that selected resource for a bounded task, and
receive a useful summary/artifact with visible progress. Use an invoice to prove
the flow; keep the contracts independent of invoice logic and agent framework.
Preparation does not authorize sending, paying, deleting or sharing with support.

Tasks and conversation history persist. Compute is temporary: waiting releases
the sandbox, and continuing starts a new run against the same task/version.
Installation and a manifest never grant mailbox access. The platform validates
authority online on every operation; the app enforces its own resource ownership.

## Current product versus later scope

Messages / Drive / Contacts / Settings is the public navigation. Contacts is
currently derived from email conversations. Drive lists mail attachments on the
local volume. Wallets stores text cards; Passwords stores app-encrypted entries.
These are not an agent registry, general object store, payment service or
credential broker. Email grouping is not yet a durable agent conversation API.

Multimedia/object exchange, brokered credential use, wallet/payment operations,
authorized automation, commercial distribution and federation belong to the
longer-term direction. Build them as separately verified capabilities after the
first complete developer and customer journeys. Use established standards and
thin adapters where useful; do not invent a universal replacement protocol now.

## Delivery order

1. Reconcile platform signup onto main and verify the browser flow.
2. Platform #4: isolated synthetic sample and built-in run observability.
3. Platform #5: private artifact publication, readiness, five-minute walkthrough;
   optional CLI follows the proven browser path.
4. Public #25 / platform #7: one selected-resource conversation integration.
5. Broader automation and distribution after these acceptance checks pass.

Public guidance is the shareable product baseline. The platform keeps a copy of
this revision; direction changes update both copies and their active issues in
the same handoff. Repository-local instructions own implementation details.
