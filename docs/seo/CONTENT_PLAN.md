# Content plan

## Principles

Improve existing pages before adding pages. Every new page needs a distinct search intent, original facts from the product, a "what it cannot do" section and links both ways to related pages. No mass-produced articles.

## Existing content (audited)

About 20 guides and comparisons, a facts page, install guides for Android TV, phone and Windows, a setup guide, a support page, and the generated title pages. Strong points: honest limits, dated competitor sources, nothing claimed that the app does not do. See `BASELINE_AUDIT.md` section 8.

## Done this mission

| Page | Purpose | Intent |
|---|---|---|
| `/how-it-works.html` | Mechanism, strengths, follow-along, limits | "how does automatic profanity filtering work" |
| `/faq.html` | One hub of 21 answers, with troubleshooting | Questions, AI answers |
| `/demo.html` | Video landing page: captions, transcript, VideoObject, trial CTA | Navigational and trust |
| Homepage | Rewritten per brief: what, how, devices, trial, price, install, why | Head terms |
| 404 page | Useful dead end | Usability |

## Backlog, in priority order

Each item has a trigger so it is built because of evidence, not for volume.

| # | Item | Trigger | Notes |
|---|---|---|---|
| 1 | Live demo section on `/demo.html` | The recording exists | Real television, real filtering, captions and transcript of what the video shows. Add a second VideoObject only for this video. Do not edit or imply an edited mute was done by the app. The source comment in `demo.html` marks the slot. |
| 2 | Disney+, YouTube or other service sections | Jacques confirms follow-along works on that service | Add to the Netflix page or a "which apps" section; separate page only if the steps differ. |
| 3 | Troubleshooting page (`/troubleshooting.html`) | Support emails show repeated issues | Start from the support page and the FAQ; do not create it just to match a keyword. |
| 4 | Split VidAngel and ClearPlay | Search Console shows separate impressions for each | Otherwise keep the combined page. |
| 5 | Region notes (US, UK, Canada, Australia, South Africa) | GSC shows impressions from those countries | Do not quote amounts until the plan prices are filled in; mention only what is true per country, such as which competitors operate there (competitor pages already cover the US-only limits). |
| 6 | Original research | After the title pages are re-counted with the "how many times it mutes" wording | One data page: how often the filter acts in popular family films. Real counts only. |
| 7 | Per-film pages | Continue the weekly generator (other PR) | Do not hand-write; they are generated from Firestore. |
| 8 | Screenshots with captions | Real app screenshots exist for 1.1.13 | The only app screenshots on the site are the TV settings screen and the launch-video stills. |

## Internal linking rules

- Home links to every primary page; `guides.html` links to all pages (now including the three new ones).
- Each guide ends with a "Next steps" block linking `setup.html`, `download.html` and one related guide.
- Run `python3 tools/internal_links.py` monthly; it lists mentions that should link to the primary page.

## Off-site authority plan (Phase 12; drafts only, nothing posted)

Legitimate channels, no purchased links, no fake reviews, no automated community promotion.

| Channel | Action | Owner | Notes |
|---|---|---|---|
| YouTube | Publish the demo video and the live-filtering recording on the channel with the site link and transcript | Gretchen | Jacques approves every video before upload (standing rule). |
| Product directories | Submit once each to AlternativeTo, Product Hunt (when 1.1.13 is live), Android TV and Stremio community add-on lists, and the Google Play listing website field | Jacques or Donna, with approval | Use the facts page text verbatim; honest category (Video Players and Editors). |
| Independent app reviews | Offer free access to a small list of Android TV and family-tech writers and creators. Ask for an honest review, with no payment and no required outcome. | Harvey drafts | Disclose any free access. Never write or buy reviews. |
| Communities | Answer questions in r/AndroidTV, r/Stremio, r/Parenting-type threads only when a real question matches, disclose that you made the app, follow each subreddit's self-promotion rule, and check the rules before posting | Jacques posts himself | See the draft below. |
| Editorial | One pitch to family-technology and Android outlets once 1.1.13 is live and the live demo exists. Angle: honest limits and how it works. | Rachel drafts | |
| Brand profiles | Same name, description (use `facts.html` sentence) and link on YouTube, Instagram, TikTok, Google Play developer page | Gretchen | Keep sameAs list in JSON-LD in sync. |

### Reddit draft (post nothing; adapt to each thread)

> I made an Android TV app for exactly this, so take this with that in mind. It reads the subtitles for what you're watching, and mutes the sound just for the lines that match, then brings it straight back. Nothing is cut or skipped. Works as Stremio's external player, and in follow-along mode with Netflix and other apps on Android TV or Google TV (English titles, needs subtitles for the title, best effort so some lines can slip). 14 days free. Doesn't work in Samsung/LG built-in apps. Happy to answer questions: familyfiltertv.com/how-it-works.html

Rules for the draft: only reply where a person asked this question; lead with the disclosure; no link spam; accept removal; never post it twice in the same community; if the thread rules ban product mentions, answer without naming it.
