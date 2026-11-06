# Keyword strategy

Scope: the target terms in Jacques's brief, mapped to one page each so no two pages compete for the same intent.

## Evidence limits (read first)

- No keyword-volume tool or Search Console data was available to this lane. **No search-volume or difficulty figure is quoted here, because none was measured.** "Demand" below is a judgement from intent and from the fact that these are the head terms of an established product category (VidAngel and ClearPlay have run for years), not a measurement.
- Replace the judgement with data after 28 days of Search Console (Performance, Queries; export steps in `BASELINE_AUDIT.md`). Re-rank this table then.
- Competition is described only as "established brands own the head terms; long-tail and device-specific terms are open". Verify with a manual SERP check per term before spending effort.
- Service-specific terms are targeted only where the product does it today. Verified against the live Play listing (6 Nov 2026) and the site's own pages: Stremio (external player), Netflix and other Android TV apps (follow-along mode, English titles), Android TV, Google TV, Windows (early beta). **Not verified, so not targeted or claimed: Disney+, YouTube, Prime Video, Hulu, Max.** If Jacques tests and confirms follow-along on any of them, add a short section to the Netflix page (or a new page only if the steps differ) and update `AI_SEARCH_STRATEGY.md`.

## Mapping (one primary page per intent)

| Cluster | Keywords | Intent | Primary URL | Status | Priority |
|---|---|---|---|---|---|
| Product head terms | profanity filter app; automatic profanity filter; profanity filter for movies; movie language filter; mute profanity in movies and TV | Commercial: find a tool | `/` (home page) | Retitled and rewritten this mission | P0 |
| Device: Android TV | profanity filter for Android TV; filter bad language on TV | Commercial | `/profanity-filter-android-tv.html` | Exists; duplicate URL folded in | P0 |
| Device: Google TV | profanity filter for Google TV | Commercial | `/google-tv-profanity-filter.html` | Exists | P1 |
| Informational: mechanism | how to filter swear words in movies; how automatic profanity filtering works; how to mute profanity on TV | Informational | `/how-it-works.html` (mechanism), `/mute-swearing-on-tv.html` (experience) | New this mission | P0 |
| Mute swear words | mute swear words in movies; mute swearing on TV | Informational then commercial | `/mute-swearing-on-tv.html` | Exists | P1 |
| Netflix | profanity filter for Netflix; does Netflix have a profanity filter | Informational then commercial | `/does-netflix-have-a-profanity-filter.html` (question), `/mute-swearing-on-netflix.html` (steps) | Exist | P1 |
| Stremio | profanity filter for Stremio | Commercial | `/stremio-profanity-filter.html` | Exists | P1 |
| Windows | profanity filter for Windows PC | Commercial, low volume | `/windows-profanity-filter.html` | Exists (early beta, stated plainly) | P3 |
| Family-friendly viewing | family-friendly streaming; family movie night without swearing; parental controls vs profanity filter | Informational | `/family-movie-night-without-swearing.html`, `/parental-controls-vs-profanity-filter.html` | Exist | P2 |
| Competitors | alternatives to VidAngel; alternatives to ClearPlay; VidAngel vs ClearPlay | Commercial investigation | `/vidangel-clearplay-alternative.html`; also `/movie-filtering-services-compared.html`, `/tvguardian-alternative.html`, `/cleancut-alternative-android-tv.html`, `/enjoy-movies-your-way-alternative.html` | Exist | P1 |
| Per-film language | is [film] OK for kids; swearing in [film] | Informational, long tail | `/titles/<film>/` | Exist, generated, another PR owns them | P2 |
| Questions | does it work on my TV; how much does it cost; is there a free trial | Informational | `/faq.html`, `/which-tvs.html` | `/faq.html` new | P1 |
| Video | profanity filter demo; family filter tv demo | Navigational | `/demo.html` | New this mission | P2 |

## Decisions on the brief's suggested URLs (no duplicate pages)

| Suggested URL | Decision | Why |
|---|---|---|
| `/profanity-filter/`, `/movie-profanity-filter/` | Not created. The home page targets these head terms. | Two more pages would split one intent three ways and the home page already has the strongest internal links. Revisit if Search Console shows the home page cannot rank for them. |
| `/android-tv-profanity-filter/` | Exists as `/profanity-filter-android-tv.html`. | Do not move an established URL. |
| `/google-tv-profanity-filter/` | Exists as `/google-tv-profanity-filter.html`. | Same. |
| `/how-it-works/` | Created as `/how-it-works.html`. | Genuinely missing. |
| `/supported-platforms/` | Not created. Covered by the home page table, `/which-tvs.html` and `/download.html`. | Would duplicate three pages. |
| `/compare/vidangel-alternative/`, `/compare/clearplay-alternative/` | Not created. `/vidangel-clearplay-alternative.html` covers both. | Splitting them would give two thin pages for one query pair. Split only if Search Console shows separate demand for each. |
| `/faq/` | Created as `/faq.html`. | Hub for people and AI answers. |

URL style: the site uses flat `.html` files, so new pages follow it. Folder URLs (`/how-it-works/`) would need a migration plan and 301s, which Pages cannot send.

## Rules to avoid cannibalisation and stuffing

1. One primary page per query; secondary pages link to the primary with descriptive anchor text, not the other way round.
2. Title and H1 vary per page; do not repeat "profanity filter" in every H2.
3. Never mention a streaming service in a title unless the page shows the steps that work today.
4. `tools/internal_links.py` audits keyword-to-page links; targets were updated (the Android TV key pointed at the duplicate URL).

## Next review

Day 30: pull the Queries export, list queries with 20 or more impressions and position 8 to 30, and give each to the page in the table above. If a query has no good page, add it to `CONTENT_PLAN.md`.
