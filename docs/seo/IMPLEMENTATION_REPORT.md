# Implementation report: SEO and AI search mission

Branch `seo/mission-2026-11-06` (rebased on `main` at 621dedd, after PRs #85 and #86). Date 6 November 2026.

**Deployment status: not deployed. Awaiting approval.** Merging to `main` is the production deploy (GitHub Pages, about 3 minutes, then the IndexNow workflow pings the sitemap after 180 s). Nothing was merged, pushed to production, or changed in Google Play, Search Console, GA4, Bing or Cloudflare.

## In plain words

The home page now leads with "Automatically Mute Profanity in Movies & TV Shows", has the two buttons from the brief, a compatibility table, a trial explanation, a why-choose list and an install section. Three new pages exist (how it works, questions and answers, a demo video page with captions and a transcript), plus a proper 404 page. Prices are no longer shown as amounts anywhere on the pages I touched: the site says "Choose a 30-day or 1-year plan after your 14-day free trial, current prices are shown in Google Play". A consent banner and Google Analytics 4 events are built but switched off until Jacques pastes a Measurement ID. Eight planning documents are in `docs/seo/`.

## 1. Completed changes (commits, oldest first)

| Commit | What |
|---|---|
| Add tools/seo_audit.py | Static audit of every page (title, description, canonical, H1, OG, alt, schema, sitemap, orphans). `--strict` exits 1 on findings. |
| Technical SEO fixes | `404.html` (noindex); duplicate `android-tv-profanity-filter.html` turned into a canonical plus meta-refresh stub and its two internal links re-pointed; 10 meta descriptions trimmed; Android TV guide title shortened; heading jump fixed on `which-tvs.html`. |
| New pages | `how-it-works.html`, `faq.html` (21 answers), `demo.html` (video landing page), `assets/media/launch-video.en.vtt` captions; added to sitemap (58 URLs), `llms.txt`, `llms-full.txt`, `guides.html`. |
| Homepage | New H1, supporting line, CTAs "Try Free for 14 Days" (Google Play) and "Watch How It Works" (#video); retitled; compatibility table; trial section; why-choose; install section; standalone Organization and WebSite JSON-LD; trial FAQ; captions on the video. |
| Performance | Font preload on non-generated pages; hero poster halved (124 KB to 60 KB). |
| Plans | Dollar amounts replaced by the plan sentence on the home page, new pages, facts, llms files and ten guide and comparison pages; SoftwareApplication Offer removed; `price.js` no longer loaded on the home page; "cheapest service" claim dropped. |
| Consent and GA4 | `consent.js` (dormant), banner styles, `data-cta` attributes, generator updated so title pages load it. |
| Docs | The eight files below. |

Kept as is on purpose: all existing URLs, the cookie-free counter `hit.js`, robots.txt (nothing blocked that should be open), existing JSON-LD on other pages.

## 2. Verified fixes

- 404 for unknown URLs returns HTTP 404 (GitHub default today; branded page after deploy).
- Every indexable page: one canonical to its served URL, one H1, OG and Twitter tags, JSON-LD parses. `tools/seo_audit.py`: one remaining finding, the description length on `titles/methodology/` (188 characters), left for the title-page owner.
- Sitemap: 58 URLs, all map to files, none noindex.
- CTA destinations: every "Try Free for 14 Days" and "Get the app" link points to the Play listing for `com.familyfiltertv.app`, which loads (HTTP 200, public page read 6 Nov 2026). The direct install and Windows beta links still go to `download.html` sections.
- Compatibility, devices, filter levels, Android 7.0 minimum, trial and follow-along limits checked against the public Play listing text, the app `minSdk` (24 = Android 7.0) and existing site pages. No iOS content anywhere.
- External links on the site: 35 checked, 27 return 200 and the others (VidAngel help, TVGuardian, Britannica, learnofchrist) answer 403, 406 or 429 to a script; they are bot blocks, not dead links.
- Consent behaviour tested in headless Chrome against a copy with a test ID: no Google request before a choice, Accept and Reject the same size, events only after Accept and none after Reject, choice carries across pages including title pages.

## 3. Test and build results

| Check | Result |
|---|---|
| `python3 tools/check_site.py --allow-lost Offer` | OK: 68 HTML files, 145 JSON-LD blocks, about 2,100 internal links, 58 sitemap URLs. (`--allow-lost` added so the deliberate Offer removal passes.) |
| `python3 -m unittest tools.test_build_titles` | 80 tests OK. (Was 74 before PR #86 added tests.) |
| `python3 tools/seo_audit.py` | 1 finding (methodology description length, not mine). |
| Build | None: the site is static, there is no build step. |
| Lighthouse 13.5, mobile, local build | Home 97 (banner showing), how-it-works 100, faq 100, demo 99, a title page 99. Accessibility 100 and SEO 100 on all. LCP 1.4 to 2.5 s, CLS at most 0.018, TBT at most 10 ms. Live baseline before the work was 84 and LCP 3.9 s. Re-measure after deployment; lab is not field data. |
| Rich Results Test, validator.schema.org | Not run (they need Google's tools). JSON-LD was validated for syntax and for agreement with the visible text only. |

Responsive layout was checked on the 412-pixel mobile Lighthouse render of the home page (no horizontal scroll, readable table). No full cross-browser pass was run.

## 4. Remaining issues

1. **Dollar amounts still on four pages**: `terms.html` (US$14.99 a year and device add-on prices in the legal text), `creators.html` (R250 or US$15 payout threshold, which is a creator payout, not a price), `creator.html` and `join.html` (R250 a year and "14 days free" in the join flow). These are legal text and flows I did not edit. Terms must be rewritten for the two plans.
2. **Launch-discount copy is still on the home FAQ and other pages** ("first 200 subscribers... 50% off their first year"). It has no amounts, but it is written for a yearly plan. Jacques should confirm it still applies with a 30-day plan. The live seat counter on the home page was removed with `price.js`.
3. **Free-week PR #75** ("no-card free week replaces the 14-day trial", draft, do not merge) rewrites the same sentences in many of the same files. If it merges, my new pages, the home trial section, the faq and demo need the same change; if mine merges first, rebase #75 and extend its replacements to `how-it-works.html`, `faq.html`, `demo.html` and `consent.js` event names (`trial_*` still work).
4. Live demo recording: the page has a source comment where it goes, but the martial-arts video does not exist, so no live-filtering claim or VideoObject exists for it.
5. The counter's reachability check logs an HTTP 405 console error on every page (Best Practices 96). Fix is a backend change (`HEAD` returns 204).
6. `price.js` and `data/prices.json` are now unused on the home page; delete them when the plan prices are final.
7. Core Web Vitals field data (INP in particular) is unknown without Search Console.

## 5. Needs credentials or external account access (not done)

- Search Console: submit the sitemap, request indexing for the four key pages, export Performance, Page indexing and Core Web Vitals (steps in `BASELINE_AUDIT.md`). Bing Webmaster likewise.
- **Jacques: create the GA4 property and give the Measurement ID.** Then paste it into `consent.js` (`GA4_ID`) after the privacy policy is updated (draft below).
- Google Play Console: nothing touched. Listing edits wait for 1.1.13 (`GOOGLE_PLAY_ASO.md`).
- Rich Results Test and validator.schema.org on home, faq, how-it-works, demo, setup.

## 6. Needs Jacques's approval or input

1. Approve the home page headline and the broader "Movies & TV Shows" framing (it moves away from the "Android TV" H1 that the page had; Android TV stays in the title tag description, lead and table).
2. Approve merging this PR (this is the production deploy).
3. GA4: provide the ID; approve the privacy wording below; decide the optional counter events and the UTM referrer on Play links (`ANALYTICS_PLAN.md`).
4. Confirm the launch-discount wording still applies to the 1-year plan (remaining issue 2).
5. Terms page rewrite for the 30-day and 1-year plans.
6. Order of merging against PR #75.
7. Play listing edits after 1.1.13 (title option "Family Filter TV: Mute Swears", short description, full description sentence).
8. Whether any streaming service beyond Netflix can be named once tested (Disney+, YouTube): none are claimed.

## 7. TODO checklist: fill in the plan prices once 1.1.13 is live

- [ ] Read both plan prices (30-day and 1-year) from the live Play listing or the Play Developer API for US, UK, Canada, Australia, South Africa.
- [ ] Decide the wording: amounts per country, or keep "current prices are shown in Google Play".
- [ ] Update: `index.html` (cta note, trial step 3, price panel, FAQ and its JSON-LD), `faq.html`, `how-it-works.html`, `demo.html`, `facts.html`, `llms.txt`, `llms-full.txt`, the comparison and guide pages listed in the Plans commit, `terms.html`, and `GOOGLE_PLAY_ASO.md`.
- [ ] Re-add the SoftwareApplication `offers` (price, currency, plan names) only with real, confirmed numbers, and re-run `tools/check_site.py`.
- [ ] Re-check the comparison pages' claims about being cheaper or dearer than competitors, and the competitor prices (last sourced in September and October).
- [ ] Decide whether to restore the live launch seat counter (`price.js` plus the home price block) or delete it.

## 8. Claims left out (not verified, so not published)

- Per-country plan prices and any dollar amount (decision above).
- Whether Google Play needs a card to start the 14-day trial.
- Support for Disney+, YouTube, Prime Video, Hulu, Max or any service beyond Netflix and Stremio.
- iPhone or iPad availability, any iOS badge or claim.
- Any rating, review, testimonial, download count (the Play page shows a download band, not used) or endorsement.
- Compatibility guarantees for specific TV models or Android TV versions beyond "if the TV has the Google Play Store".
- That the demo video's mute was done live by the app: the page says it is a produced launch video that illustrates the effect, with one word muted for the demo.
- Any 1.1.13 version number or feature: none is on the new copy (the app repo checkout I read is versionName 1.1.1; the live direct APK is 1.0.1).

## 9. GA4 privacy wording: draft for Jacques to review (not published)

The current privacy page says the website sets no cookies and uses no third-party analytics (section "Website visit counter (no cookies)"). It has no analytics-cookie wording for the site, so it must change before the ID goes in. Draft, to be reviewed by Jacques or a lawyer (not legal advice):

> **Website analytics (only if you accept)**
> If you press Accept on the banner, we use Google Analytics 4 to count which pages and buttons are used on this website, so we can improve it. Google Analytics sets cookies in your browser (named `_ga` and `_ga_` followed by letters) and receives your page address, a random identifier, your approximate location from your IP address, and your browser and device type. We do not turn on Google's advertising features or share this data with Google for advertising, and Google signals and ad personalisation are off. Nothing is sent to Google, and no analytics cookies are set, unless you accept. If you press Reject, or your browser sends Do Not Track or Global Privacy Control, nothing is sent. You can change your mind at any time from the "Analytics choices" link at the bottom of every page; choosing Reject removes the analytics cookies. We only record that a button was pressed, such as a link to the Google Play listing; this is not a count of downloads or installs. The cookie-free visit counter described above runs either way. Google processes this data under its own terms and may do so outside your country. Data is kept for [14 months, the GA4 default; Jacques to choose 2 or 14 months in GA4].

Also update the "Website visit counter" sentence "No third-party analytics or advertising service is used for it" so it refers only to the counter, and add the Google Analytics entry to any list of processors.

## 10. After approval: go-live verification (Phase 14)

1. Merge. Wait 3 minutes. Check: `/`, `/how-it-works.html`, `/faq.html`, `/demo.html`, `/sitemap.xml` (58 URLs), `/robots.txt`, `/llms.txt`, a bogus URL returns the new 404 page with HTTP 404, `/android-tv-profanity-filter.html` lands on the guide.
2. `curl -I` the three new pages for 200; confirm the canonical in each; confirm `http://` and `www` still 301 to `https://familyfiltertv.com/`.
3. Click through: home hero button, install button, header "Get the app", "Watch How It Works", demo play with captions, the faq links.
4. Search Console: submit the sitemap; request indexing for `/`, `/how-it-works.html`, `/faq.html`, `/demo.html`; later export Page indexing.
5. Run the AI visibility prompts once and log the baseline (`AI_SEARCH_STRATEGY.md`).
6. Run Lighthouse on the live home page and compare with the baseline (84, LCP 3.9 s).

## 11. Documents

`docs/seo/BASELINE_AUDIT.md`, `KEYWORD_STRATEGY.md`, `AI_SEARCH_STRATEGY.md`, `CONTENT_PLAN.md`, `GOOGLE_PLAY_ASO.md`, `ANALYTICS_PLAN.md`, `90_DAY_ROADMAP.md`, `IMPLEMENTATION_REPORT.md`. Evidence limit: no keyword-volume data and no Search Console access were available, so the keyword strategy ranks by intent and fit and says so.
