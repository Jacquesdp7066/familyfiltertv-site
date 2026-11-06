# Baseline audit: familyfiltertv.com

Audited 6 November 2026 against `main` at 4c805b2 (before this mission) and the live site. Repeatable with `python3 tools/seo_audit.py` (static, every page) and `python3 tools/check_site.py` (links, JSON-LD, sitemap).

Search Console was not accessed (no login by design). Nothing here claims a page is indexed; the site is crawlable, which is not the same thing. Export steps for the real index data are at the end.

## 1. Stack and deployment

| Layer | Finding |
|---|---|
| Frontend | Hand-written static HTML plus one stylesheet (`style.css`). No framework, no bundler. Content is in the HTML, so crawlers and AI fetchers see it without running JavaScript. |
| Generated pages | `tools/build_titles.py` and `tools/weekly_refresh.py` generate `/titles/<film>/` pages from Firestore ratings (read-only). `tools/test_build_titles.py`: 74 tests. |
| JavaScript | `hit.js` (cookie-free counter), `price.js` (local Play price and launch-offer counter from `data/prices.json`; no longer loaded on the homepage after the plans decision), `signup.js` (launch-updates form). All `defer`, none needed to read the content. |
| Backend | Firebase Cloud Functions in europe-west1 (`hit`, `signup`, `launchLadderState`), called from the page. |
| Hosting | GitHub Pages from `main`, custom domain via `CNAME`. HTTP/2, valid TLS, `cache-control: max-age=600` (not configurable on Pages). |
| Pipeline | A merge to `main` publishes in about 3 minutes. `.github/workflows/indexnow.yml` waits 180 s then pings IndexNow with every sitemap URL. There is no build step and no staging site. |

## 2. HTTP and canonical domain (checked with curl)

| Request | Result |
|---|---|
| `http://familyfiltertv.com/` | 301 to `https://familyfiltertv.com/` |
| `http://www.familyfiltertv.com/`, `https://www.familyfiltertv.com/` | 301 to `https://familyfiltertv.com/` |
| `https://familyfiltertv.com/nope` | 404 (GitHub's default page; this mission adds a branded `404.html`) |
| All 55 sitemap URLs | 200 |
| `/robots.txt`, `/sitemap.xml`, `/llms.txt`, `.well-known/assetlinks.json` | 200 |
| `/page` and `/page.html` | Both 200 (Pages serves both). Every page has a canonical to one form, so this is consolidated, not a duplicate-content problem. |
| `X-Robots-Tag` header | Not sent (Pages cannot send custom headers). Robots directives are meta tags only. |

## 3. robots.txt and sitemap

- `robots.txt`: `Allow: /` for all agents; disallows `/link.html`, `/join*`, `/creator*`, `/apk/`, `/admin.html`; points to the sitemap. No AI crawler is blocked (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, Bingbot all allowed by the wildcard). This is the right posture for visibility; it does not guarantee inclusion in AI answers.
- `sitemap.xml`: 55 URLs, valid XML, all canonical, all indexable, all 200. No `noindex` page is listed. Every title page is included. Added in this mission: how-it-works, faq, demo (58 URLs).
- Gap found: the old URL `android-tv-profanity-filter.html` was indexable, not in the sitemap, and canonicalised to `profanity-filter-android-tv.html` (a near-duplicate left over from the first SEO pass, Sept 2026).

## 4. Page-level audit (64 HTML files before this mission)

Method: `tools/seo_audit.py`. Rules: title present and at most 65 chars; description present, 70 to 165 chars; canonical equals the served URL; one H1; no skipped heading level; Open Graph and Twitter card tags; image alt and dimensions; sitemap membership; inbound internal links; word count.

| Result | Detail |
|---|---|
| Canonicals, H1, OG tags, Twitter card, image alt | All present and correct on every indexable page. |
| Meta descriptions | 10 pages over 165 characters (download page 238, Google TV page 199). Trimmed in this mission. |
| Title length | Home 68 and Android TV guide 66 characters. Fixed. |
| Heading order | `which-tvs.html` jumped from h1 to h3. Fixed. |
| Orphans | None (the duplicate Android TV URL had two inbound links, now re-pointed). |
| Thin pages | None among indexable non-title pages (smallest is about 360 words). |
| Noindex pages | `admin`, `link`, `join`, `creator`, `tiktok-*` and `apk/` are noindex and also disallowed in robots.txt. One caveat: a URL blocked in robots.txt cannot have its `noindex` read, so these could still appear as URL-only results if linked externally. Low risk; they are not linked from public pages. |
| Title pages `/titles/*` | The title tag is a normal length; per-film count wording is being changed by another PR and is out of scope here. |

## 5. Structured data

- 138 JSON-LD blocks, all valid JSON, all matching content visible on the page. Types in use: SoftwareApplication with an Offer (a yearly US dollar amount; removed in this mission, see IMPLEMENTATION_REPORT.md), VideoObject, FAQPage, BreadcrumbList, Article, Organization, Movie, WebSite and ImageObject on title pages.
- No `aggregateRating`, review, download-count or award markup anywhere, which is correct: none is real.
- Gaps: the homepage nested the Organization inside `publisher` and had no standalone Organization or WebSite entity. Added in this mission.
- FAQPage markup is on many pages. Google now shows FAQ rich results only for a few site types, so expect no rich result; the markup still describes the visible Q&A accurately for other consumers. Not removed.
- Validation here is structural (JSON parses, types allowed, text matches the page). Google's Rich Results Test and validator.schema.org need a browser or Google's tool and were not run from this lane; run both on the five key URLs before announcing (see the checklist in IMPLEMENTATION_REPORT.md).

## 6. Rendering and indexability

All content is in server-delivered HTML. Before this mission the only JavaScript-injected content was the local price and launch-offer figures (`price.js`), deliberately marked `data-nosnippet` and kept out of the static text after Google's AI Overview quoted a hard-coded example as the price. The static page now carries no amount (plans decision).

## 7. Performance and accessibility (Lighthouse 13.5, mobile preset, simulated slow 4G)

| Page | Perf | A11y | Best practices | SEO | LCP | CLS | TBT |
|---|---|---|---|---|---|---|---|
| Live home (before) | 84 | 100 | 96 | 100 | 3.9 s | 0 | 50 ms |
| Local build, home (after; consent banner showing) | 97 | 100 | 96 | 100 | 2.5 s | 0 | 10 ms |
| Local build, how-it-works / faq / demo | 100 / 100 / 99 | 100 | 96 | 100 | 1.4 / 1.7 / 2.1 s | 0.001 / 0.018 / 0.002 | 0 |
| Local build, a title page (Frozen) | 99 | 100 | 96 | 100 | 1.8 s | 0.01 | 0 |

Lab numbers are not field data. Core Web Vitals at the 75th percentile need Search Console's report (below). The local builds have no network latency; on the live site expect a few tenths of a second more (GitHub Pages' time to first byte was about 350 ms in the baseline run). Removing `price.js` and halving the hero poster are the likely reasons the local home page scores higher than the live baseline (local and live runs are not like for like). The live number must be re-measured after deployment. Inlining critical CSS or putting a CDN in front are the next levers if the field data is above 2.5 s (the CDN is an account-level change).

Best practices 96 on every page: the page-view counter's reachability check (`HEAD` to the Cloud Function) gets HTTP 405, which the browser logs as a console error. It is harmless to users and rankings; the fix is to make the function answer `HEAD` with 204, which is a backend change.

## 8. Content assessment

- Strong: About 20 intent-specific guides, several comparison pages with sourced competitor facts, a citable `facts.html`, `llms.txt` and `llms-full.txt`, and about 20 title pages.
- Fixed: duplicate Android TV page; no consolidated FAQ, no how-it-works explainer, no video landing page.
- Risks to watch (not changed here): `swearing-in-movies.html` and `movies-with-no-swearing.html` quote counts of films; per Jacques's rule, counts must be worded as how many times the app mutes, not as swear words. That wording is being changed site-wide by another PR.
- Outdated or unverifiable: the facts page and `llms-full.txt` said "last updated 13 October"; `llms-full.txt` now says 6 November. Competitor pricing on comparison pages was last sourced in September and October: re-check before the next promotion.

## 9. Exports to take from Search Console (no login was used)

1. Search Console, property `familyfiltertv.com` (domain property if available), Performance, Search results. Set date range to Last 16 months. Tick Clicks, Impressions, CTR, Position. Export (top right) as Google Sheets or CSV. Repeat on the Queries, Pages, Countries and Devices tabs. Filter Queries "Does not contain" `family filter` to separate non-branded queries from branded ones.
2. Indexing, Pages. Download the chart data, then click each reason under "Why pages aren't indexed" and export that list. Also export the "Indexed" list.
3. Experience, Core Web Vitals, Mobile then Desktop. Open each issue group and export. Page-level field data needs enough real visits; a new site may show "not enough data".
4. Indexing, Sitemaps: confirm `sitemap.xml` shows Success and the discovered-page count matches 58 after deployment.
5. Save all exports to `docs/seo/gsc-exports/YYYY-MM-DD/` (kept out of git if they contain anything sensitive).
6. Bing: Bing Webmaster Tools, Search Performance and Site Explorer exports (setup notes: `docs/bing-webmaster-setup.md`).
