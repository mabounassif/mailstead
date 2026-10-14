import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import { articles } from "./src/data/manifest.mjs";

const contentDates = new Map(
  articles.map((article) => [`https://mailstead.app/${article.section}/${article.slug}/`, article.updated]),
);

export default defineConfig({
  site: "https://mailstead.app",
  trailingSlash: "always",
  build: {
    format: "directory",
  },
  integrations: [
    sitemap({
      filter: (page) =>
        !page.endsWith(".md") &&
        !page.endsWith(".txt") &&
        !page.includes("/skills/") &&
        !page.includes("/404"),
      serialize(item) {
        item.lastmod = contentDates.get(item.url) || "2026-10-14";
        return item;
      },
    }),
  ],
});
