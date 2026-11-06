# AI search strategy

Goal: when someone asks Google AI Overviews, ChatGPT search, Gemini, Copilot or Perplexity about muting profanity on TV, the answer is accurate about Family Filter TV and cites familyfiltertv.com. Nothing here can guarantee inclusion; the work is to make accurate, citable facts easy to find and then measure what happens.

## What is in place (verified in the repo)

| Lever | State |
|---|---|
| Crawlable HTML | All content is server-delivered static HTML. No client rendering needed. |
| Crawler access | `robots.txt` allows everything except private and admin paths. No AI user agent is blocked. Allowing a crawler does not mean it will cite the site. |
| One citable facts page | `/facts.html`: what it is, does and does not do, devices, versions, price. Dated "last updated". |
| Plain-text briefs | `/llms.txt` and `/llms-full.txt`, updated this mission with the new pages and a 6 November date. **llms.txt is an optional experiment**, not an established ranking factor, and no major engine has said it uses it. Cost is low; do not spend more time on it than on the pages themselves. |
| Short answers | Homepage, `/faq.html` and most guides open with a one- or two-sentence answer, then detail. |
| Consistent entity data | Name "Family Filter TV" (also written FamilyFilterTV), Organization + WebSite + SoftwareApplication JSON-LD on the homepage, same sameAs profiles (YouTube, Instagram, TikTok), same price and trial everywhere. |
| Transparent price and limits | The plan structure ("a 30-day or 1-year plan after your 14-day free trial; current prices are shown in Google Play"), device limits and the "what it cannot do" lists are plain text on the page. No dollar amount is published until 1.1.13 is live, and the SoftwareApplication markup carries no Offer until then. |
| Evidence-backed comparisons | Competitor pages cite the competitors' own support pages and are dated. |
| Demonstration | `/demo.html` with captions and a written transcript. A live recording on a real television is planned (placeholder in the page source). |

## What was added this mission

1. `/how-it-works.html`: a self-contained explanation (subtitles checked against mild, family or strict; follow-along; what it cannot do). Written as question headings with short direct answers, the format answer engines quote best.
2. `/faq.html`: 21 answers, each also in FAQPage markup.
3. Homepage: compatibility table, trial section, install section, standalone Organization and WebSite markup.
4. `/demo.html`: transcript and VideoObject so the video can be understood by text-only systems.

## Rules (do not break these)

- Never invent ratings, reviews, download counts, awards, partnerships or "as seen on". None exists in the markup today.
- Keep price, trial and device facts identical across the Play listing, home page, FAQ, facts page, llms files and JSON-LD. When one changes, change all in the same PR. A stale AI-facing fact gets repeated by assistants.
- Do not target a streaming service in copy unless the steps work today (see `KEYWORD_STRATEGY.md`).
- Do not publish counts or ratings with the wrong wording: the Family-setting number is how many times the app mutes, not "swear words".

## Repeatable test method

Run monthly (first Monday), same day each month, logged in `docs/seo/ai-visibility-log.csv` (create on first run; columns: date, engine, prompt id, mentioned Y/N, cited familyfiltertv.com Y/N, cited URL, accuracy issues, competitors named).

1. Use a fresh logged-out session for each engine (or a clean profile) and a fixed region per run. Run each prompt once per engine; if the answer is odd, run it a second time and log both. Engines: Google (AI Overviews, a standard search, US and UK and South Africa settings), ChatGPT with search on, Gemini, Copilot, Perplexity.
2. For each answer record: is Family Filter TV named, is familyfiltertv.com cited as a source, which page, and are price, trial, platforms and limits correct. Copy any wrong statement verbatim.
3. Classify wrong statements: (a) our page is wrong, fix the page; (b) our page is right but ambiguous, tighten the wording; (c) a third-party page is wrong, note it, and if it is a directory or review we control, correct it; (d) hallucination, no action except making the right fact easier to find.
4. Compare to last month. A change over one run is noise; act on trends over three months.
5. Also check referral data: the site counter groups `chatgpt.com`, `perplexity.ai`, `claude.ai`, `gemini.google.com` and `copilot.microsoft.com` as referrer category "search" (see `ANALYTICS_PLAN.md`), so AI referrals are visible only as a lump with search engines. Splitting them is a proposal needing Jacques's approval.

## Prompt set

Discovery (does it appear at all):
1. What is the best profanity filter for movies and TV?
2. How can I automatically mute swearing on my TV?
3. Is there an app that mutes bad language in movies on Android TV?
4. Profanity filter for Google TV
5. How do I filter swear words on Netflix?
6. How do I mute profanity when I watch movies with Stremio?
7. Alternatives to VidAngel
8. Alternatives to ClearPlay
9. Family-friendly way to watch movies with no swearing

Brand and facts (is it accurate):
10. What is Family Filter TV?
11. How much does Family Filter TV cost, and is there a free trial?
12. Does Family Filter TV work on Samsung or LG TVs?
13. Does Family Filter TV work with Netflix?
14. Does Family Filter TV work on iPhone?  (expected truthful answer today: there is no iPhone app. Log any claim otherwise as an accuracy issue.)
15. Is Family Filter TV safe, and does it record audio?
16. Family Filter TV vs VidAngel
17. Family Filter TV vs ClearPlay

Per-film (long tail):
18. How much swearing is in [a film we have a title page for]?

## Content habits that help

- Update the "last updated" stamp on `facts.html` and `llms-full.txt` whenever a fact changes.
- Put the answer first, the nuance second. Avoid marketing superlatives; answer engines skip them.
- Keep a short "What it cannot do" list on every product page; it makes the page trustworthy to quote.
- Third-party mentions are earned, never manufactured (see `CONTENT_PLAN.md`, off-site section).
