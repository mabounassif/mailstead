import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { articles } from "../src/data/manifest.mjs";

const root = fileURLToPath(new URL("..", import.meta.url));
const dist = join(root, "dist");
const documents = ["# Mailstead documentation", "", "Self-hosted custom-domain webmail. Resend transports mail; your deployment stores mailboxes.", ""];

for (const article of articles) {
  const source = join(root, "src/pages", article.section, `${article.slug}.md`);
  const raw = await readFile(source, "utf8");
  const body = raw.replace(/^layout:.*\n/m, "");
  const target = join(dist, article.section, `${article.slug}.md`);
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, body);
  const prose = raw.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, "");
  documents.push(`## ${article.title}`, `Source: https://mailstead.app/${article.section}/${article.slug}/`, "", prose, "");
}

await copyFile(join(root, "public/robots.txt"), join(dist, "robots.txt"));

await writeFile(join(dist, "llms-full.txt"), documents.join("\n"));
await copyFile(join(dist, "sitemap-0.xml"), join(dist, "sitemap.xml"));
