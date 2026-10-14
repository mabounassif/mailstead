import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { articles } from "../src/data/manifest.mjs";

const root = fileURLToPath(new URL("..", import.meta.url));
const dist = join(root, "dist");

for (const article of articles) {
  const source = join(root, "src/pages", article.section, `${article.slug}.md`);
  const raw = await readFile(source, "utf8");
  const body = raw.replace(/^layout:.*\n/m, "");
  const target = join(dist, article.section, `${article.slug}.md`);
  await mkdir(dirname(target), { recursive: true });
  await writeFile(target, body);
}

await copyFile(join(root, "public/robots.txt"), join(dist, "robots.txt"));
