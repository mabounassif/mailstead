import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createStaticServer } from "../scripts/serve.mjs";

test("static hosting preserves file types, redirects and missing-resource status", async () => {
  const root = await mkdtemp(join(tmpdir(), "mailstead-site-"));
  await mkdir(join(root, "docs"));
  await writeFile(join(root, "index.html"), "Home");
  await writeFile(join(root, "404.html"), "Page not found");
  await writeFile(join(root, "docs/index.html"), "Docs");
  await writeFile(join(root, "guide.md"), "# Guide");
  await writeFile(join(root, "llms-full.txt"), "# Documentation");
  await writeFile(join(root, ".env"), "secret");
  const server = createStaticServer(root);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  try {
    const redirect = await fetch(base + "/docs?source=agent", { redirect: "manual" });
    assert.equal(redirect.status, 308);
    assert.equal(redirect.headers.get("location"), "/docs/?source=agent");
    for (const route of ["/missing", "/missing.md", "/missing.txt", "/.env", "/%2eenv", "/%2e%2e%2f.env"]) {
      const response = await fetch(base + route);
      assert.equal(response.status, 404, route);
      assert.doesNotMatch(await response.text(), /secret|Home/);
    }
    const markdown = await fetch(base + "/guide.md");
    assert.match(markdown.headers.get("content-type"), /^text\/markdown/);
    assert.equal(await markdown.text(), "# Guide");
    const text = await fetch(base + "/llms-full.txt");
    assert.match(text.headers.get("content-type"), /^text\/plain/);
    const head = await fetch(base + "/", { method: "HEAD" });
    assert.equal(head.status, 200);
    assert.equal(await head.text(), "");
    assert.equal((await fetch(base + "/", { method: "POST" })).status, 405);
    assert.equal((await fetch(base + "/%zz")).status, 400);
  } finally {
    await new Promise((resolve) => server.close(resolve));
    await rm(root, { recursive: true, force: true });
  }
});
