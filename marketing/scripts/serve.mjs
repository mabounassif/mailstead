import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const types = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".json": "application/json", ".xml": "application/xml", ".txt": "text/plain", ".md": "text/markdown", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon" };
export function createStaticServer(directory = fileURLToPath(new URL("../dist", import.meta.url))) {
  const root = resolve(directory);
  return createServer(async (request, response) => {
    const head = request.method === "HEAD";
    const send = (status, body, type = "text/plain; charset=utf-8") => {
      response.writeHead(status, { "Content-Type": type, "Content-Length": Buffer.byteLength(body), "X-Content-Type-Options": "nosniff" });
      response.end(head ? undefined : body);
    };
    if (request.method !== "GET" && !head) {
      response.setHeader("Allow", "GET, HEAD");
      send(405, "Method not allowed");
      return;
    }
    let url, pathname;
    try {
      url = new URL(request.url, "http://localhost");
      pathname = decodeURIComponent(url.pathname);
    } catch { send(400, "Invalid URL"); return; }
    if (pathname.includes("\0") || pathname.includes("\\") || pathname.split("/").some((part) => part.startsWith("."))) {
      send(404, "Not found"); return;
    }
    let target = resolve(root, `.${pathname}`);
    if (target !== root && !target.startsWith(root + sep)) { send(404, "Not found"); return; }
    try {
      if ((await stat(target)).isDirectory()) {
        if (!url.pathname.endsWith("/")) {
          response.writeHead(308, { Location: url.pathname + "/" + url.search });
          response.end(); return;
        }
        target = resolve(target, "index.html");
      }
      const body = await readFile(target);
      const extension = extname(target);
      const type = types[extension] || "application/octet-stream";
      send(200, body, type + (/(text\/|application\/(json|xml))/.test(type) ? "; charset=utf-8" : ""));
    } catch (error) {
      if (error.code !== "ENOENT" && error.code !== "ENOTDIR") { send(500, "Unable to serve file"); return; }
      try { send(404, await readFile(resolve(root, "404.html")), "text/html; charset=utf-8"); }
      catch { send(404, "Not found"); }
    }
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const port = Number(process.env.PORT || 4321);
  createStaticServer().listen(port, "0.0.0.0", () => console.log(`Mailstead marketing listening on ${port}`));
}
