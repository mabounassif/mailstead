# Mailstead marketing site

Static site for <https://mailstead.app>. It is not the Django webmail app. Customer mailboxes stay on the origins those customers deploy.

## Commands

```bash
cd marketing
npm ci
npm run check    # calculator and static-server tests
npm run build    # writes dist/
npm run check:site # verify built pages, links, exports and sitemap
npm run preview  # local preview of dist/
npm start        # production static server; honors PORT
```

`npm run dev` serves a local draft with live reload.

| | |
| --- | --- |
| Build | `npm run build` |
| Output | `marketing/dist/` |
| Preview | `npm run preview` |
| Production index | Indexable unless `MARKETING_NOINDEX=true` |

Set `MARKETING_NOINDEX=true` only for a preview or staging build. A production build must leave that variable unset. `robots.txt` allows public pages and points at `https://mailstead.app/sitemap-index.xml`. It is not an access-control mechanism. Do not put the Django admin, mailbox, or webhook routes on this origin.

## Deploy on Railway

Use a second Railway service, not the webmail service.

1. Create a service from this repository with root directory `marketing` (or build from `marketing/` in CI and upload `dist/`).
2. Build command: `npm ci && npm run build`.
3. Start command: `npm start`. This serves `dist/` with correct file types, directory redirects, and real HTTP 404 responses. Remove any existing `serve -s` or other SPA fallback override. For a Docker deployment, select `marketing/Dockerfile` with `marketing/` as the build context; this is separate from the repository’s Django Dockerfile.
4. Add the custom domain `mailstead.app` on that service. Buying the domain does not create the DNS record. At the registrar, point the domain at the target Railway shows for this service, then wait until the certificate is issued.
5. Leave `MARKETING_NOINDEX` unset. Confirm `https://mailstead.app/robots.txt` and a page’s canonical URL use `https://mailstead.app/` with a trailing slash.
6. Do not attach the webmail volume or `RESEND_API_KEY` to this service.

Redirect HTTP to HTTPS at the platform. Keep one trailing-slash style: this build emits directories (`/pricing/`).

## Prices and articles

Shared figures live in `src/data/pricing.mjs` (`pricingVersion`, `sourceChecked`). The calculator and the pricing scenario table both call `src/lib/cost.mjs`. Article prose that repeats a number must be edited in the same change.

`src/data/manifest.mjs` records slug, intent, author, publication date, update date, and last source-check date. Do not bump those dates because the site was rebuilt. Bump `updated` when the article’s meaning changes. Bump `sourceChecked` only after re-reading the cited page. If a price cannot be re-read, remove the public figure instead of guessing.

Outdated comparisons are the articles whose `sourceChecked` is older than the pricing file’s `sourceChecked`, or whose tables still name a plan that the pricing module no longer exports.

Click tracking is optional. Deploy and GitHub links emit `data-track="deploy"` and `data-track="github"`. If you define `window.mailsteadAnalytics = (name) => { ... }` before those clicks, it receives the name. The site does not load an analytics script itself.

## Search Console

After `mailstead.app` answers over HTTPS:

1. Add the domain property in [Google Search Console](https://search.google.com/search-console) and complete the DNS verification Google shows. HTML-file checks belong on this static service, not on a customer’s webmail host.
2. Submit `https://mailstead.app/sitemap-index.xml`.
3. Inspect a representative URL, such as `https://mailstead.app/pricing/`, and confirm the fetched HTML contains the H1 and the canonical.
4. Later, use the Performance report for queries and pages. Indexing is not guaranteed. Google’s [AI features documentation](https://developers.google.com/search/docs/appearance/ai-features) says ordinary search eligibility is what matters; `llms.txt` is only a convenience index.

## Crawlers

`robots.txt` allows all user agents to read public marketing URLs. It does not change Google-Extended or other training-crawler policies. Those were left untouched on purpose.

## Agent documentation and site checks

`/for-agents/` provides a copyable setup prompt. The canonical runbook is `src/pages/docs/agent-setup.md`; the normal build emits HTML and the postbuild exports Markdown. The deployment skill is maintained at `public/skills/deploy-mailstead/SKILL.md` and is copied as a static asset, so building only `marketing/` needs no parent-directory sources. Read and install it using the chosen agent client's supported mechanism; it is not installed automatically.

`/llms.txt` indexes Markdown and HTML. `/llms-full.txt` concatenates the runbook and articles without Astro frontmatter. `/sitemap-index.xml` is the primary sitemap; `/sitemap.xml` is an explicit compatibility alias. Unknown URLs must return HTTP 404 rather than homepage HTML. The included production server enforces this; external static hosts must be configured accordingly.

After changing pages, run `npm run check`, `npm run build`, and `npm run check:site`. The last command validates internal links/anchors, one H1 per page, descriptions/canonicals, Markdown exports, sitemap entries, and the skill export. CI runs these commands for every PR. A passing build is not a live email delivery test.

Account-dependent distribution actions and measurements are tracked in [distribution.md](../docs/distribution.md).
