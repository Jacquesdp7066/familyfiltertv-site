# Analytics and conversion tracking plan

## What exists today (inspected, not changed)

| Item | Finding |
|---|---|
| Web analytics | **No Google Analytics, no tag manager, no third-party scripts, no cookies.** The only measurement is `hit.js`, a first-party, cookie-free counter that posts to the project's own Cloud Function (`hit`, europe-west1). |
| What it records | Page path without query string, a one-word referrer category (direct, search, social, internal, other), and three click kinds: `play` (link to the Play listing), `direct` (APK link), `signup` (launch-updates form). No IP, no identifiers, nothing linking visits. |
| Consent posture | Does nothing if Do Not Track or Global Privacy Control is on. Declared in `privacy.html#counter`. |
| Search Console | A verification file exists (`googlee3a0c7bd81717f36.html`); account access not used here. Bing: IndexNow key published; see `docs/bing-webmaster-setup.md`. |
| App analytics | The app ships Firebase Analytics with the advertising ID off (privacy policy, "usage analytics"). |

Design consequence: store-link clicks are counted, installs are not. **A click on the Play button is not a download, and not a trial start, and must never be reported as one.**

## Definitions (use these words exactly in reports)

| Term | Meaning | Source |
|---|---|---|
| Organic impression and click | Appearance and click in Google or Bing results | Search Console, Bing Webmaster |
| Page view | Counter `view` event | Site counter |
| Store click | Visitor clicked a Google Play link (`play`) | Site counter |
| Direct click | Visitor clicked the APK link (`direct`) | Site counter |
| Install | First open of the app | Play Console statistics or Firebase `first_open` |
| Trial start | Subscription trial created | RevenueCat or Play Console |
| Paid conversion | First paid renewal after trial | RevenueCat |
| Revenue by channel | Paid revenue joined to install source | Only where install source is known (see UTM section) |

## Events: verified now vs proposed

Verified (no change needed): page views by path and referrer category, `play` clicks, `direct` clicks, `signup` form submits.

Implemented in `consent.js` (GA4, after consent only): `play_store_click`, `cta_trial_click`, `direct_install_click`, `video_play`, `video_progress`. Still proposed (need Jacques's approval; not built): the counter-side events below and the UTM referrer on Play links.

| Event | Why | Privacy impact | How |
|---|---|---|---|
| `trial_cta` click, separated from other Play links | The home page now has "Try Free for 14 Days" and a header "Get the app" link going to the same listing. Separating them shows which wording converts. | None (same counter) | Add a `data-cta="trial-hero"` attribute and have `hit.js` send it as the click target name. Small change to `hit.js` plus a Cloud Function allow-list update. |
| `video_play`, `video_complete` on `demo.html` and the home video | Demonstration engagement | None (same counter, no identifiers) | Listen to the video element's `play` and `ended` events in `hit.js`. |
| `windows_download` click | Separates the Windows beta from Android | None | Add a target in `hit.js` for `download.html#windows` and the Windows file. |
| AI referrer split | `chatgpt.com`, `perplexity.ai`, `claude.ai` and similar are currently one "search" lump. | None | Return `ai` as a referrer category. |
| UTM campaign on Play links | Attribute installs to channels (see below) | Adds a campaign string to the Play URL; no personal data | Append `&referrer=utm_source%3D<site>%26utm_medium%3D<page>%26utm_campaign%3D<cta>` to the Play links. `hit.js` matches the link by prefix, so counting keeps working. Firebase Analytics in the app can read install referrer data on first open (confirm in the app's analytics setup before relying on it). |
| GA4 | **Approved by Jacques (6 Nov 2026) and built, dormant until he supplies a Measurement ID.** Consent-first: see "GA4 with consent" below. The cookie-free counter stays for the baseline. | Consent required | `consent.js` |

Not tracked and not to be added without consent: individual users, fingerprints, session replay, heatmaps, advertising pixels.

## Campaign (UTM) rules

- Use lowercase `utm_source` (site, youtube, reddit, newsletter, creator-name), `utm_medium` (organic, social, referral, email), `utm_campaign` (short slug). Apply them only to links we publish off-site to familyfiltertv.com. The counter drops query strings, so the landing page path is counted; the UTM string is read from the Play `referrer` parameter instead, once approved.
- Creator codes already attribute creators separately (creator programme); keep that separate from UTM.

## Reporting specification (monthly, first Monday)

| Metric | Source | Notes |
|---|---|---|
| Organic impressions, clicks, CTR, average position | Search Console Performance, by page and by query, last 28 days vs previous 28 | Position is an average; read it with the query list. |
| Indexed pages | Search Console, Indexing, Pages: Indexed vs Not indexed, with reasons | Expected: all 58 sitemap URLs once crawled; the noindex pages are excluded. |
| Branded vs non-branded | Performance, filter Queries containing and not containing "family filter" / "familyfiltertv" | Non-branded growth is the SEO signal. |
| Sessions by referrer category | Site counter | Search, social, direct, other. |
| Store clicks and direct clicks | Site counter | Report next to page views; state "clicks, not installs". |
| Store click rate | Store clicks divided by page views, per landing page | Per page, to find pages that attract but do not convert. |
| Installs | Play Console, Statistics, acquisition (store listing visitors and installs) | Cannot be tied to a web visit without UTM. |
| Trial starts | RevenueCat | Count from the subscription system. |
| Paid conversions and revenue | RevenueCat | By install source only if the UTM referrer is approved and captured. |
| Core Web Vitals | Search Console, Experience | LCP at most 2.5 s, INP at most 200 ms, CLS at most 0.1 at the 75th percentile. |
| AI visibility | `AI_SEARCH_STRATEGY.md` log | Separate sheet. |

Report layout: one page, five numbers on top (non-branded clicks, store clicks, installs, trial starts, paid conversions), one line each on what changed and why, then the per-page table.

## Search Console integration

Already verified for the domain per the verification file. Actions (account-level, so Jacques does these): submit `https://familyfiltertv.com/sitemap.xml` and confirm the status; link Search Console to nothing else. Bing: import from Search Console or use the IndexNow key already published.

## GA4 with consent (built, dormant)

- File: `consent.js`, loaded on every public page and in the title-page generator. One placeholder, `GA4_ID`, at the top of the file. While it is empty nothing runs: no banner, no request, no storage.
- To switch on: Jacques creates the GA4 property and gives the Measurement ID (a value like `G-ABC123XYZ9`); the privacy policy is updated first (draft in `IMPLEMENTATION_REPORT.md`); paste the ID; merge.
- Behaviour: banner with Accept and Reject of identical size; nothing is requested from Google before Accept; Do Not Track and Global Privacy Control count as Reject; choice stored in `localStorage` key `fftv-consent`; "Analytics choices" footer link reopens the banner; Reject after Accept removes `_ga` cookies and sets `ga-disable`. Google signals and ad personalisation are off; no advertising features.
- Events (all carry `page_path`; `link_location` is the button's `data-cta` or `link`; the header link is `header`):

| Event | When |
|---|---|
| `play_store_click` | Any link to the Google Play listing. A store click, never a download or install. |
| `cta_trial_click` | Only links whose `data-cta` starts with `trial` (home hero and install, how-it-works, demo, faq "Try Free for 14 Days" buttons). |
| `direct_install_click` | APK link. |
| `video_play`, `video_progress` (25, 50, 75, 100) | The 30-second launch video. The muted looping hero is ignored. |

- In GA4 mark `cta_trial_click` as a key event ("conversion"). It means a visitor pressed the button, not that a trial began.
- Verified with a headless-browser test against a copy with a test ID (nothing before choice; events only after Accept; none after Reject; choice carries across pages, including title pages).
