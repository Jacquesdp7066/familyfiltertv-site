# 90-day growth roadmap

Business goal: 1,000,000 cumulative app downloads in 24 to 36 months. That is an ambition, not a forecast; SEO alone is unlikely to reach it. This roadmap covers what SEO and AI search can do and how to measure it. Day 1 is the day the technical PR is merged and live.

Rule for every phase: prioritise by measured data. Until Search Console has 28 days of data, priorities below are judgement.

## Days 1 to 7: foundation

| Action | Owner | Done when |
|---|---|---|
| Merge the SEO PR and verify live URLs (list in `IMPLEMENTATION_REPORT.md`) | Jacques approves; Ben verifies | New pages return 200, sitemap lists 58 URLs, 404 page works, canonical on each. |
| Submit sitemap in Search Console; request indexing for home, how-it-works, faq, demo | Jacques | Sitemap status Success. |
| Run Rich Results Test and validator.schema.org on home, faq, how-it-works, demo, setup | Ben | No errors. |
| Confirm the analytics baseline (`ANALYTICS_PLAN.md`); decide on the proposed events | Jacques | Decisions recorded. |
| Export the first Search Console and Bing data | Jacques | Files in `docs/seo/gsc-exports/`. |
| Run the first AI visibility test | Gretchen or Donna | First log rows. |

## Days 8 to 30: landing pages, demonstration, store

| Action | Notes |
|---|---|
| Record the live demo on a real television (martial-arts scene, as planned) | Must show the app genuinely filtering. Add to `demo.html` with captions, transcript, VideoObject. Jacques approves the video before any upload. |
| Publish the video to YouTube with the transcript and the site link | Standing rule: Jacques approves first. |
| Apply the Play listing edits after 1.1.13 is live | `GOOGLE_PLAY_ASO.md`. One Console edit. |
| Improve the top five pages by Search Console impressions | Rewrite the title and first paragraph for the queries that actually appear. |
| Re-check competitor prices and facts on the comparison pages | Dated sources; update `lastmod`. |
| Sync the title pages and the font preload after the other PR merges | The generator needs the same preload line. |

## Days 31 to 60: supporting content and AI

| Action | Notes |
|---|---|
| Publish the next backlog items from `CONTENT_PLAN.md` only where Search Console shows a query with no good page | At most two pages; each with a limits section. |
| Strengthen internal links with `tools/internal_links.py` | Three links per target at most. |
| Directory submissions and honest review outreach | See the off-site plan; no purchased links. |
| Second AI visibility test; fix any page that the engines quote wrongly | Compare to Day 7. |
| Review the proposed analytics events: add the approved ones | Update the privacy policy line if anything changes. |

## Days 61 to 90: learn and expand

| Action | Notes |
|---|---|
| Pages with impressions but low CTR: rewrite title and description | Test one change at a time; wait 14 days before judging. |
| Pages ranking 8 to 20: add depth, internal links, one supporting FAQ | |
| Expand topics that work; stop topics that do not | |
| Core Web Vitals review from field data | If the home page is above 2.5 s LCP in the field, inline critical CSS or ask Jacques about a CDN (account-level). |
| Third AI visibility test and a written summary | |
| Day-90 report: non-branded clicks, store clicks, installs, trial starts, paid conversions (definitions in `ANALYTICS_PLAN.md`) | A trend, not a forecast of 1,000,000. |

## Dependencies and risks

- 1.1.13 review outcome gates the Play edits and any Android-version claim.
- iOS stays out of all copy until approved (`GOOGLE_PLAY_ASO.md`).
- Another PR is changing count wording on title pages and the generator; do not touch those until it merges.
- Queries about services we do not support (Disney+, YouTube) are not targeted until Jacques verifies the feature.
