import { articles } from "../data/manifest.mjs";
import { site, sourceChecked } from "../data/pricing.mjs";

export function GET() {
  const lines = [
    "# Mailstead",
    "",
    "> Self-hosted webmail for a custom domain. MIT licence. Mailstead stores the mailbox; Resend transports mail. mailstead.app does not host customer mailboxes.",
    "",
    "This file is a convenience index. It is not a Google ranking requirement.",
    "",
    `- [Overview](${site.url}/)`,
    `- [Pricing](${site.url}/pricing/)`,
    `- [Compare](${site.url}/compare/)`,
    `- [Guides](${site.url}/guides/)`,
    `- [Repository](${site.repo})`,
    `- [Deploy on Railway](${site.deploy})`,
    "",
    "## Articles",
    "",
    ...articles.map(
      (article) =>
        `- [${article.title}](${site.url}/${article.section}/${article.slug}/) — sources checked ${article.sourceChecked}`,
    ),
    "",
    `Pricing data version checked ${sourceChecked}.`,
    "",
  ];
  return new Response(lines.join("\n"), {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}
