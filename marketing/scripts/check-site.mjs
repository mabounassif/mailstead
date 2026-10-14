import assert from "node:assert/strict";
import { readFile, readdir, stat } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { articles } from "../src/data/manifest.mjs";

const root = fileURLToPath(new URL("../dist/", import.meta.url));
async function* walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) yield* walk(path);
    else yield path;
  }
}
let pages = 0;
for await (const file of walk(root)) {
  if (!file.endsWith(".html")) continue;
  const html = await readFile(file, "utf8");
  assert.equal((html.match(/<h1(?:\s|>)/g) || []).length, 1, `One H1: ${file}`);
  assert.match(html, /<meta name="description" content="[^"]+"/, `Description: ${file}`);
  assert.match(html, /<link rel="canonical" href="https:\/\/mailstead\.app\//, `Canonical: ${file}`);
  for (const match of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
    const href = match[1].replaceAll("&amp;", "&");
    if (/^(https?:|mailto:|tel:|data:|#)/.test(href)) continue;
    const url = new URL(href, "https://mailstead.app/" + file.slice(root.length).replace(/index\.html$/, ""));
    let target = resolve(root, "." + decodeURIComponent(url.pathname));
    if ((await stat(target).catch(() => null))?.isDirectory()) target = join(target, "index.html");
    assert.ok((await stat(target).catch(() => null))?.isFile(), `Missing target ${href} in ${file}`);
    if (url.hash && target.endsWith(".html")) {
      const content = await readFile(target, "utf8");
      assert.ok(content.includes(`id="${decodeURIComponent(url.hash.slice(1))}"`), `Missing anchor ${href} in ${file}`);
    }
  }
  pages++;
}
const sitemap = await readFile(join(root, "sitemap-0.xml"), "utf8");
for (const article of articles) {
  const path = `${article.section}/${article.slug}`;
  const markdown = await readFile(join(root, path + ".md"), "utf8");
  assert.ok(!/^layout:/m.test(markdown), `Leaked layout: ${path}`);
  assert.ok(sitemap.includes(`https://mailstead.app/${path}/`), `Missing sitemap article: ${path}`);
}
assert.ok(!/\.md<|\.txt<|\/404/.test(sitemap), "Only canonical HTML pages in sitemap");
assert.equal(await readFile(join(root, "sitemap.xml"), "utf8"), sitemap);
const full = await readFile(join(root, "llms-full.txt"), "utf8");
assert.match(full, /^# Mailstead documentation/);
assert.match(full, /Set up custom-domain email/);
assert.ok(!full.includes("<!DOCTYPE") && !/^layout:/m.test(full));
const skill = await readFile(join(root, "skills/deploy-mailstead/SKILL.md"), "utf8");
assert.equal(skill, await readFile(fileURLToPath(new URL("../public/skills/deploy-mailstead/SKILL.md", import.meta.url)), "utf8"));
console.log(`Verified ${pages} HTML pages, internal links and anchors, ${articles.length} Markdown exports, sitemap, full documentation, and deployment skill.`);
