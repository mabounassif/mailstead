# Mailstead distribution and adoption

Prioritize successful inboxes and continued usage rather than stars or deploy clicks alone.

| Channel | Prepared in this repository | Account-dependent next action |
| --- | --- | --- |
| Railway | Template overview, screenshots, setup runbook, agent handoff | Update marketplace copy from `docs/railway-template-readme.md`; add a short setup video/demo and support external deployments |
| Resend | Resend webmail guide and complete delivery checklist | Ask about a community example or feature after independent deployments work |
| GitHub / self-hosting | README setup entry point, deployment skill, operations links | Share a technical walkthrough with actual configuration and costs in relevant communities |
| Search / coding agents | HTML and Markdown guides, crawlable sitemap, plain-text index, agent prompt | Verify the Search Console domain property and submit `https://mailstead.app/sitemap-index.xml` |
| Developers / agencies | Project inbox and DNS guides | Recruit five outside developers, record blockers, and verify inbound plus outbound delivery |

This file does not claim those submissions or outreach have been completed. Repository changes do not automatically update marketplace metadata, Search Console, DNS, or installed agent skills.

## Evaluate discovery and setup separately

Use fresh coding-agent sessions with unbranded tasks, such as “I need an inexpensive browser inbox for my custom domain; my project runs on Railway” and “I use Resend for notifications and need to read customer replies.” Include mismatch tasks requiring IMAP or a managed office suite. Record whether the agent discovers Mailstead, chooses it appropriately, reads the current runbook, and finishes setup correctly.

For an authorized deployment pilot, record the app URL, passed readiness checks, actual inbound receipt, actual outbound reply receipt, and remaining manual actions. Keep credentials out of the record. Recheck continued use with the participant after a week.

The existing site supports an optional `window.mailsteadAnalytics(name)` callback for deployment, GitHub, and agent-guide clicks. No analytics vendor or visitor tracking is configured by these changes; pick and configure measurement separately if desired.
