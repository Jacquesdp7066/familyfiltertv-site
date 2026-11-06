# DRAFT: terms of use rewrite for the 30-day and 1-year plans

**Status: draft for Jacques to approve. Not published. `terms.html` on the live site is unchanged** (last updated 20 September 2026). This is not legal advice; have it read by whoever reviews the terms before it goes live. Square brackets are facts only Jacques or the Play and RevenueCat setup can confirm. Publish only after version 1.1.13 is approved and live, since until then the app on Google Play still sells one annual plan.

## What is wrong in the live terms once two plans exist

| Where | Live wording | Problem |
|---|---|---|
| Meta description | "the US$14.99 a year subscription, the 14-day free trial, device limits and cancellation" | Names one annual amount. |
| Subscription and free trial | "costs US$14.99 a year, with the first 14 days free" | One plan, one amount. |
| Devices | "a 4th device for US$3.09/year, a 5th for US$5.99/year, and a 6th for US$8.99/year" | Amounts per year; the 30-day plan's device pricing is not stated anywhere I could verify. |
| What the app is | "an Android TV profanity-filtering player designed to work with supported Stremio playback" | Out of date: the app also follows along with Netflix and other Android TV apps, and there is a Windows early beta. |
| Acceptable use | "alongside Stremio and lawfully obtained streams" | Same. |
| Last updated | 20 September 2026 | Must change with the edit. |

## Replacement text

### Meta description

Terms of use for Family Filter TV: the 14-day free trial, the 30-day and 1-year plans, device limits and cancellation.

### What the app is

Family Filter TV is an Android TV and Android phone profanity filter. It mutes unwanted language according to the filter strength you choose, in supported Stremio playback and by following along with the title you start in Netflix and other apps on your Android TV or Google TV. There is also an early-beta companion for Windows. It does not host, index, source or redistribute video content. Family Filter TV is an independent app and is not affiliated with, or endorsed by, Stremio, Netflix, Google or OpenSubtitles.

### Subscription, plans and free trial

The first 14 days are free. After the free trial you choose a 30-day plan or a 1-year plan. The price of each plan is shown in Google Play, in your own currency, at the price Google sets for your country, and the amount you see at checkout is the amount you pay. Payment is handled by Google Play Billing and your subscription is managed through RevenueCat, our subscription-management provider.

[Confirm each of these before publishing: (a) both plans renew automatically until cancelled; (b) the free trial is offered once per account / per Google account; (c) whether you can change plan, and when the change takes effect; (d) whether Google Play asks for a payment method to start the trial.]

You can cancel at any time from Google Play. Your account keeps filtering until the end of the period you have already paid for. Refunds are handled under Google Play's refund policy. If you cancel during the free trial, [state what happens: the trial ends at once or runs to its end, as set by Google Play].

[If the launch discount stays on the 1-year plan: "A launch discount may apply to the first year of the 1-year plan for the first subscribers in each group, as described on the home page while the offer is open. The discount applies to the first year only; after that the 1-year plan renews at the price shown in Google Play."]

### Devices

Your account includes 3 devices (any mix of TVs, phones and, in beta, Windows computers). You can link up to 6 devices per account. The price of the 4th, 5th and 6th device is shown in Google Play, in your own currency [and states whether it follows the plan period: per 30 days or per year]. TVs are linked from your phone using a short code shown on the TV.

### What happens if your subscription lapses

Family Filter TV never plays a stream unfiltered. If your free trial ends without a plan or your plan lapses, the app stops filtering, and stops playback, until you subscribe again. If your device goes offline, a previously active subscription keeps working for up to 7 days (the offline grace period) before the app requires a fresh check. [Confirm the offline grace period is the same for the 30-day plan.]

### Acceptable use (one-line change)

Use the app only for its intended purpose, alongside Stremio or the apps you follow along with, and lawfully obtained streams. [Rest unchanged.]

### Last updated

[Date of publication.]

## Questions for Jacques

1. Do the two plans share the same device allowance and add-on pricing?
2. Is the trial one per account, per Google account, or per device?
3. Does the launch discount stay on the 1-year plan only (the desk says yes)? Then keep the bracketed paragraph.
4. Does a refund policy beyond Google Play's apply?
5. Should the privacy page and the terms be republished on the same day as the Play listing change?

## Other pages to keep in step on the day this is published

`index.html`, `faq.html`, `how-it-works.html`, `demo.html`, `facts.html`, `llms.txt`, `llms-full.txt` and `docs/seo/GOOGLE_PLAY_ASO.md` already use the sentence "Choose a 30-day or 1-year plan after your 14-day free trial: current prices are shown in Google Play". The privacy policy needs the analytics wording in `IMPLEMENTATION_REPORT.md` section 9 before GA4 is switched on.
