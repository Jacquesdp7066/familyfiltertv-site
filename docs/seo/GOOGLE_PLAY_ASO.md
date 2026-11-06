# Google Play listing: recommendations (for after 1.1.13 clears review)

**Nothing in this document has been applied.** The Play Console and the live store listing were not touched: any listing change resets the 1.1.13 review. Do these after 1.1.13 is published, in one Console edit.

Source of the "current" text: the public Play page for `com.familyfiltertv.app`, read without login on 6 Nov 2026 (listing updated 24 Oct 2026, category Video Players and Editors, data safety "no data shared with third parties"). The download-count band and the in-app-purchase flag exist on the page but are not used on the website and must not be quoted.

## Current listing (public)

- Title: `Family Filter TV` (16 characters; limit 30)
- Short description: `Mutes swear words on your Android TV while the picture keeps playing.` (69; limit 80)
- Full description: Android TV and Google TV focus; two ways to use it (follow along, Stremio external player); how it works; filter strength Mild, Family, Strict; what you need (Android TV or Google TV, Android phone, Android 7.0 or newer, account, 14-day free trial, subtitles); good-to-know limits; Windows early beta mention; setup link.

It is already accurate, honest and consistent with the website. The recommendations below are tuning, not corrections.

## Title (limit 30; Play rejects keyword stuffing and performance claims)

| Option | Length | Comment |
|---|---|---|
| `Family Filter TV` | 16 | Current. Brand-only, safest. |
| `Family Filter TV: Mute Swears` | 29 | Adds the function in plain words. Recommended if Jacques wants a keyword in the title. |

Avoid "Profanity Filter Movies Netflix" style titles (stuffing, and implies service support that is follow-along only).

## Short description (limit 80)

| Option | Length |
|---|---|
| `Mute swear words on Android TV and Google TV. 14 days free.` | 59 |
| `Mute swearing on Android TV while the picture plays. 14-day free trial.` | 71 |

Reason: puts the platform and the trial in the first line shown in search. "Free" must be true on day one, and it is a 14-day trial (billing disclosed in the full description).

## Full description

Keep the current structure (it is clear and honest). Edits to make:

1. First paragraph, one extra sentence: "Choose a 30-day or 1-year plan after your 14-day free trial — current prices are shown in Google Play." (the 30-day and 1-year plans arrive with 1.1.13). Do not put dollar amounts or launch-offer numbers in the listing text: Play shows the prices, and they change. Once 1.1.13 is live, check that the two plan names in the Console match the words "30-day plan" and "1-year plan" used on the website.
2. Add "Works with Stremio, and follows along with Netflix and other apps on Android TV or Google TV. Not affiliated with Netflix." Already present in some form; keep the disclaimer.
3. Keep "Muting is best effort", "English titles for now" and "needs subtitles" in the visible text above the fold of "Read more" if possible.
4. Leave out until verified: any other streaming service name, iPhone or iPad, any rating or count.
5. Use each natural keyword a few times at most: "mute swear words", "profanity", "Android TV", "Google TV", "Stremio", "subtitles". Play's ranking reads the full description, but repetition lowers conversion and risks a policy flag.

## Keyword strategy for the store

Primary: mute swear words, profanity filter, Android TV, Google TV. Secondary: Stremio external player, family movie night, language filter. The terms match `KEYWORD_STRATEGY.md`. Do not include competitor names in the listing (policy).

## Screenshot copy (one idea per screenshot; real screens only)

Use real captures from 1.1.13. Suggested captions, in order:

1. "Mutes the swearing. The picture keeps playing."
2. "Choose how strict: Mild, Family or Strict."  (the app shows Off as well; match the screen)
3. "One setting for every TV in the house."
4. "Pick the title on your phone. The TV follows."
5. "14 days free. Cancel any time in Google Play."
6. "Honest limits: English titles, needs subtitles, best effort."

Show a TV frame and a phone frame; do not show movie footage that is not licensed (the website demo uses "Tears of Steel", CC BY 3.0, with credit).

## Feature graphic

Current `assets/feature-graphic.png` is 1024 by 500, the required size. Recommend: the product line "Mute swear words on Android TV" in large type, the app icon, and the TV-plus-phone picture from the launch video, with no ratings, awards or download numbers.

## Trial messaging

Same words everywhere: "Choose a 30-day or 1-year plan after your 14-day free trial — current prices are shown in Google Play. Cancel any time in Google Play." The website homepage, `faq.html`, `how-it-works.html`, `demo.html`, `facts.html` and the llms files use this wording; `terms.html` still states the old single annual amount and must be rewritten by Jacques for the two plans. Any change must change all four in the same PR.

## Device compatibility

State: Android TV, Google TV and Android TV boxes; an Android phone, Android 7.0 or newer (app `minSdk` is 24, which is Android 7.0); Windows 10 or 11 early beta from the website only. Not supported: Samsung, LG, Roku and Fire TV built-in apps. Direct (APK) install exists for boxes without Play, but the listing should not link to it.

## Landing page to store consistency

| Claim | Play listing | Website |
|---|---|---|
| Free trial | 14 days | 14 days (home, faq, terms) |
| Android version | 7.0 or newer | 7.0 or newer (facts, which-tvs) |
| Filter levels | Mild, Family, Strict | Off, mild, family, strict |
| Follow-along | English titles | English titles |
| Plans and price | 30-day and 1-year plan after the trial (from 1.1.13); amounts shown by Google Play | 30-day or 1-year plan after the trial; "current prices are shown in Google Play"; no amounts |

The one visible difference is that the site lists "off" as a level and the listing does not. Both are true; mention "off" in the listing's strength paragraph for consistency.

## Check before publishing the edit

- 1.1.13 is live and the review has cleared.
- Every sentence is true for 1.1.13 (the working doc `FamilyFilterTV/docs/PLAY_STORE_LISTING.md` is older and describes a pre-follow-along app; do not reuse it).
- Data safety section agrees with the app's analytics and microphone use (Firebase Analytics and an on-device listening feature are described in the privacy policy).

## iOS App Store launch checklist (do not publish any iOS availability claim before approval)

The iOS work exists as branches in the app repo (`feature/ios-T*`), but iOS is not live and not confirmed. Nothing on the site mentions iOS, and nothing should until every line below is true.

- [ ] Apple review approved; the app is downloadable in the target storefronts.
- [ ] Jacques gives written approval to announce.
- [ ] iOS version number, minimum iOS, supported devices (iPhone only, or iPad too) decided and tested.
- [ ] Feature parity decided: say exactly what iOS does (for example, which of follow-along, Stremio and household settings it supports). Do not copy Android claims.
- [ ] Subscription: product IDs, price in each storefront, the 14-day trial configured and tested on App Store Connect; terms and privacy updated for Apple billing.
- [ ] App Store listing: name (30), subtitle (30), promotional text (170), keywords (100, comma separated, no competitor names), description, screenshots per required device size, privacy "nutrition label", age rating, support URL, marketing URL.
- [ ] Website: add the App Store badge and link to the home page, `download.html` and `install.html`; add an iOS entry to the compatibility table; add `iOS` to `operatingSystem` in SoftwareApplication JSON-LD only then; update `facts.html`, `faq.html`, `llms.txt`, `llms-full.txt`; update `hit.js` link-click targets (it recognises only the Play and direct download links today).
- [ ] Smart App Banner and Universal Links only after the above (needs an `apple-app-site-association` file served from the site; no change now).
- [ ] Re-run `tools/check_site.py`, `tools/seo_audit.py`, and the AI prompt set (prompt 14 in `AI_SEARCH_STRATEGY.md` should then say yes).
