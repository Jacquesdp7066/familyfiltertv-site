# Home page redesign: video hero, visual sections

Design specification for `index.html` and `style.css` of familyfiltertv.com.
Written 10 Oct 2026 for the BUILD agent. Implement it exactly; where it says
"fallback", ship the fallback and leave a `<!-- ASSET n -->` comment so the
media step can swap the asset in later.

Measured starting point (10 Oct 2026, `main` at a1e1610): home page 6,863 px
tall on desktop, 10,134 px on a phone, about 1,560 visible words, 8 headings,
2 images (both the app icon), no video.

Wireframes: `docs/design/home-redesign-wireframe.svg` (desktop and phone side
by side). ASCII versions are in section 2 of this document.

---

## 1. The idea in five lines

1. In the first five seconds a parent should feel: **the TV mutes the swearing
   by itself, and the film never stops.** Not "a filter app", but a thing they
   can see happening.
2. The hero is a television. On its screen a real film line plays, the
   subtitle reaches the muted word and shows a muted badge, the sound meter in
   the corner drops to a flat dashed line, and then the bars come back. Under
   the screen is a soundbar: the site's own cyan meter, which flattens on the
   page at the same moment as the one in the video.
3. That loop (`assets/media/hero-loop.mp4`, 6.75 s, no audio track) plays
   automatically, muted, looping, `playsinline`, with `hero-poster` as its
   poster. It is the only thing on the page that moves without being asked.
4. One quiet button on the TV, "Watch with sound (30 s)", swaps the same
   screen to `launch-video.mp4` with sound and captions. Nothing with sound
   ever autoplays. When it ends, the silent loop comes back.
5. Everything below the hero is short, visual and scannable in 30 seconds:
   three steps with pictures, one picture of the household, what it works
   with, the price, the questions, the guides, and one final install button.
   The long text stays on the guide pages that already exist.

---

## 2. Page structure, top to bottom

### 2.0 Global layout rules

- Keep the header, nav and footer markup as they are today (classes
  `site-head`, `brand`, `site-nav`, `site-foot`, `foot-nav`). Only the
  `<main>` changes, plus the one credit line added to the footer (2.10).
- `<main>` no longer carries `class="wrap"`. Each section wraps its own
  content: `.wrap-wide` (max-width 1120 px, padding-inline 24 px, 18 px under
  460 px) for visual sections, the existing `.wrap` (760 px) for text-only
  sections (FAQ, guides).
- Sections are `<section class="h-section">` with `padding-block:
  var(--section-gap)` where `--section-gap: clamp(56px, 8vw, 104px)`. No
  rules between sections; the gap and the visuals do the separating.
- Every section has exactly one `h2` (except the hero, which has the `h1`),
  set with `.h-section-head`: `font-size: clamp(1.6rem, 3.2vw, 2.25rem)`,
  weight 800, letter-spacing -0.03em, line-height 1.1, margin 0 0 12px,
  max-width 22ch. An optional one-sentence lead below it in `.lead`.
- Colour: page ground `--ground`; cards `--surface` with `1px solid --line`;
  "TV" frames and the price card `--field` with `1px solid --field-line`.
  Amber `--accent` is used only on the "Get it on Google Play" button (it
  appears three times on the page, but it is the same action). Cyan
  `--signal` appears only inside meter bars. No other colours.
- Type stays Manrope at the existing sizes. Body copy in sections is
  `--ink-soft`; headings `--ink`; notes `--muted`.
- Desktop means `min-width: 900px`. Phone means everything below that; there
  is no tablet layout, phone rules apply until 900 px.
- Target length: desktop (1280×800 viewport) at most 3,800 px; phone (390×844)
  at most 6,200 px. Visible words at most 850 including closed FAQ answers.

Desktop (1280 wide, scaled):

```
+---------------------------------------------------------------------------+
| [icon] Family Filter TV        Home Titles Download Get set up Support ..  |
+---------------------------------------------------------------------------+
|                                                                           |
|  PROFANITY FILTER FOR ANDROID TV AND GOOGLE TV   +----------------------+ |
|  Automatically mute                              |  [video: film line,  | |
|  profanity on your                               |   subtitle, meter]   | |
|  Android TV.                                     |      (play btn ▶)    | |
|  Family Filter TV mutes the swearing while the   +----------------------+ |
|  picture keeps playing. Nothing is cut ...       | ▮▮▯▮▮▮ soundbar  ON  | |
|  [Get it on Google Play] [▶ Watch with sound]    +----------------------+ |
|  The first 14 days are free. Then US$14.99/yr.    A real film line ... (CC)|
|                                                                           |
|  How it works                                                             |
|  Set up in about five minutes.                                            |
|  +-----------------+  +-----------------+  +-----------------+            |
|  | [TV + phone]    |  | [link code]     |  | [filter levels] |            |
|  | 1 Put it on the |  | 2 Link the TV   |  | 3 Pick how      |            |
|  |   TV and phone  |  |   from your ph. |  |   strict, watch |            |
|  +-----------------+  +-----------------+  +-----------------+            |
|  The full walkthrough →                                                   |
|                                                                           |
|  +-------------------------------------------------------------------+    |
|  |            [phone + three TVs, wide image]                        |    |
|  +-------------------------------------------------------------------+    |
|  One filter for the whole house.                                          |
|  The filter belongs to the household ...   • 3 devices, up to 6 • ...     |
|                                                                           |
|  What it works with                   |  Good to know                     |
|  [Stremio] [Android TV] [Google TV]   |  • speech only ...                |
|  [TV boxes] [Android phone] ...       |  • needs subtitles ...            |
|                                                                           |
|  What it costs                                                            |
|  +------------------+   Try it free for 14 days ...                       |
|  | US$14.99 a year  |   [Get it on Google Play]                           |
|  | (existing card)  |                                                     |
|  +------------------+                                                     |
|                                                                           |
|  Questions                 (11 collapsible rows, first open)              |
|  Guides                    (10 links, two columns)                        |
|  +-------------------------------------------------------------------+    |
|  |  [icon] Family Filter TV. The first 14 days are free.             |    |
|  |         [Get it on Google Play]  Other ways to install · Windows  |    |
|  +-------------------------------------------------------------------+    |
+---------------------------------------------------------------------------+
| footer (unchanged) + film credit line                                      |
+---------------------------------------------------------------------------+
```

Phone (390 wide): the same sections in the same order, every grid collapses to
one column. In the hero the order is kicker, h1, lead, TV frame, actions, price
line, caption. The TV frame must be fully visible within the first 844 px.

### 2.1 Hero

Purpose: show the product working within five seconds and offer the install.

Markup outline:

```html
<section class="h-hero wrap-wide" aria-labelledby="h1">
  <div class="h-hero-copy">
    <p class="h-kicker">Profanity filter for Android TV and Google TV</p>
    <h1 id="h1">Automatically mute profanity on your Android TV.</h1>
    <p class="lead">Family Filter TV mutes the swearing while the picture keeps
      playing. Nothing is cut, blurred or skipped. Set how strict on your phone,
      and every TV in the house follows.</p>
    <div class="actions">
      <a class="btn" href="https://play.google.com/store/apps/details?id=com.familyfiltertv.app">Get it on Google Play</a>
      <button class="btn-quiet h-play" type="button" aria-controls="hero-video">Watch with sound (30 s)</button>
    </div>
    <p class="h-price-line">The first 14 days are free. Then US$14.99 a year.
      <a href="download.html">Other ways to install</a></p>
  </div>
  <figure class="h-tv">
    <div class="h-tv-screen">
      <video id="hero-video" class="h-video" width="1280" height="720"
        muted loop playsinline preload="none"
        poster="assets/media/hero-poster-1280.jpg"
        aria-label="A film line plays; the one swear word is muted and the picture keeps going.">
        <source src="assets/media/hero-loop.mp4" type="video/mp4">
      </video>
      <button class="h-tv-play" type="button" aria-controls="hero-video" hidden>
        <span class="visually-hidden">Play</span>
      </button>
    </div>
    <div class="h-soundbar" aria-hidden="true">
      <span class="h-soundbar-label">Sound</span>
      <div class="h-bars"><!-- 48 <b style="--h:..px"> as today --></div>
      <span class="h-soundbar-state" data-on="On" data-muted="Muted">On</span>
    </div>
    <figcaption class="h-caption">A real film line with the filter on Strict.
      Film clip: Tears of Steel (CC) Blender Foundation | mango.blender.org</figcaption>
  </figure>
  <details class="h-transcript"><summary>Transcript of the 30-second video</summary> … (text from 5.3) </details>
</section>
```

Copy, exact:

- Kicker: `Profanity filter for Android TV and Google TV` (uppercase via CSS,
  0.8125rem, weight 700, letter-spacing 0.08em, colour `--muted`).
- H1: `Automatically mute profanity on your Android TV.` (unchanged; it
  carries the page's search phrase). Existing `h1` rule applies; override
  `max-width: 14ch` inside `.h-hero`.
- Lead: `Family Filter TV mutes the swearing while the picture keeps playing.
  Nothing is cut, blurred or skipped. Set how strict on your phone, and every
  TV in the house follows.`
- Primary action: `Get it on Google Play` (the existing `.btn`, a link).
- Secondary action: `Watch with sound (30 s)` (a `<button>`; it changes the
  page, so it is not a link). A play triangle before the text, drawn as an
  inline SVG 14 px, `currentColor`.
- Price line: `The first 14 days are free. Then US$14.99 a year.` followed by
  the link `Other ways to install` to `download.html`. Class `.h-price-line`:
  0.9375rem, `--muted`, margin-top 14 px.
- Caption under the TV: `A real film line with the filter on Strict. Film clip:
  Tears of Steel (CC) Blender Foundation | mango.blender.org`. The credit text
  is required on this page (CC BY 3.0) and must stay visible, 0.8125rem,
  `--muted`, not hidden on any width.

Visual: the TV frame (`.h-tv`).

- `.h-tv`: background `--field`, border `1px solid --field-line`,
  border-radius 18 px, padding 10 px, margin 0, box-shadow
  `0 30px 80px -30px rgba(53,207,232,0.18), 0 1px 0 rgba(255,255,255,0.04) inset`.
- `.h-tv-screen`: `position: relative; aspect-ratio: 16 / 9; border-radius: 10px;
  overflow: hidden; background: #000`.
- `.h-video`: `display: block; width: 100%; height: 100%; object-fit: cover`.
  The `width`/`height` attributes plus `aspect-ratio` on the screen mean zero
  layout shift whichever state it is in.
- `.h-tv-play`: a 72 px circle centred on the screen, background `--ink`,
  colour `--ground`, a 26 px triangle (inline SVG), no border; shown only when
  the loop is not playing (reduced motion, Save-Data, autoplay refused, or no
  JS). `hidden` is removed by JS when needed; without JS the build adds a
  `<noscript>` style that shows it and gives the video `controls`.
- `.h-soundbar`: height 44 px, `display: grid; grid-template-columns: auto 1fr
  auto; align-items: center; gap: 12px; padding: 0 14px; margin-top: 8px;
  border-top: 1px solid --field-line`. Labels: 0.6875rem, uppercase,
  letter-spacing 0.1em, `--muted`, monospace stack (same as `code`).
- `.h-bars`: the existing `.meter-bars` look at 28 px tall, 2 px gap, bars
  `max-width: 5px`, `--signal`. 48 bars with the same heights pattern as the
  old hero meter, scaled: `height: calc(var(--h) * 0.34)`.
- Muted state (class `is-muted` on `.h-soundbar`, set by JS, see 3.2): every
  bar transitions to `height: 3px; background: #2C4463`, the state label
  reads `Muted`. On state: label `On`.

Layout:

- Desktop: `.h-hero { display: grid; grid-template-columns: minmax(0, 5fr)
  minmax(0, 7fr); gap: 48px; align-items: center; padding-block: 48px 24px }`.
  Copy left, TV right. The TV is 620 px wide at 1120 px container, so the
  whole screen plus the soundbar sits inside an 800 px tall viewport under the
  64 px header.
- Phone: one column, `gap: 22px`, order: `.h-hero-copy` first but its
  `.actions` and `.h-price-line` move below the TV. Do this with CSS order on
  the grid children, not by duplicating markup: make `.h-hero-copy` a
  `display: contents` wrapper on phone and give `.h-tv` `order: 3`, `.actions`
  `order: 4`, `.h-price-line` `order: 5`. Padding-block 28 px 8 px.
- Transcript: a `<details>` with the full text from 5.3, placed under the hero
  grid, spanning both columns, 0.9375rem, `--muted`.

Call to action: Get it on Google Play.

### 2.2 How it works

Purpose: make setup feel like five minutes, with pictures, not a wall of text.

- H2: `How it works`. Lead: `Set up in about five minutes.`
- Three cards in `.h-steps` (an `<ol>`): desktop three equal columns, gap
  24 px; phone one column, gap 16 px.
- Each card (`<li>`): `background: --surface; border: 1px solid --line;
  border-radius: 16px; overflow: hidden`. Top: `.h-visual` (a 16:9 box,
  `aspect-ratio: 16 / 9`, `background: --field`, image `object-fit: cover`,
  `loading="lazy" decoding="async" width="1200" height="675"`). Below: padding
  20 px 22px 24px, the step number (counter, 0.8125rem, `--muted`, tabular
  numerals, as `.steps li::before` today), `h3` and one short paragraph in
  `--ink-soft`.

Steps, exact copy:

1. `Put it on the TV and your phone` — `Install Family Filter TV on your
   Android TV or TV box, and on your phone as well, then sign in with Google or
   an email address.`
   Visual: ASSET REQUEST 3 (`assets/media/step-install.jpg`). Fallback until it
   exists: the 16:9 box in `--field` with `assets/icon-192.png` centred at
   96×96 px (`alt=""`) and the words `TV + phone` under it in the kicker style.
2. `Link the TV from your phone` — `The TV shows a short code. On the phone,
   tap Account, then Link a device, and type the code.`
   Visual: ASSET REQUEST 4 (`assets/media/step-link.mp4` + `step-link.jpg`),
   a silent loop in a `<video muted loop playsinline preload="none"
   poster="…step-link.jpg">`, played by the same observer as the hero (3.2).
   Fallback: the 16:9 box in `--field` showing the text `7KD-M4Q` in the
   existing `.code-display` style at `font-size: clamp(1.6rem, 4vw, 2.4rem)`,
   with `TV shows` above it in the kicker style. (`7KD-M4Q` is the format
   `link.html` displays; it is not a real code.)
3. `Pick how strict, then watch` — `Off, mild, family or strict. Start a title
   in Stremio and choose Family Filter TV for playback, or follow along with
   Netflix and other apps on Android TV.`
   Visual: ASSET REQUEST 5 (`assets/media/step-levels.jpg`), a crop of the
   real TV settings screen. Fallback: `assets/media/app-tv-settings.png` with
   `object-fit: cover; object-position: 0% 40%`, alt text from 5.4.

Under the list, one line, `--muted`, 0.9375rem: `Follow-along needs version
0.2.21 or newer. Family Filter TV is not affiliated with Netflix.` then the
link `The full walkthrough` to `setup.html#quick-start`.

### 2.3 One filter for the whole house

Purpose: the household idea, which the app's competitors do not have, in one
picture.

- Visual first, full container width: `.h-house` is a 16:9 frame on desktop
  (`aspect-ratio: 16 / 9` when ASSET REQUEST 6 exists) with
  `assets/media/household-clean.jpg` (`width="1600" height="900"`,
  `loading="lazy"`), rounded 18 px, `1px solid --field-line`. Phone: the
  portrait crop `household-tall.jpg` (900×1200) via `<picture>` with
  `media="(max-width: 899px)"`.
  Fallback until the assets exist: `assets/media/household.jpg` in a frame
  with `aspect-ratio: 16 / 6.75; object-fit: cover; object-position: 50% 100%`
  on all widths. That crop hides the headline baked into the top of that
  image, so the page never shows the same sentence twice.
- H2 under the picture: `One filter for the whole house.`
- Paragraph: `The filter belongs to the household, not to the device. Set it
  once on your phone and every television linked to your account follows: the
  one in the lounge, the one in the spare room, the one the children are
  watching while you are in the kitchen.`
- Three facts in `.h-facts` (a `<ul>` without bullets; desktop three columns,
  gap 24 px; phone stacked, gap 10 px), each a `strong` line then a muted
  line:
  - `Three devices included.` / `Add up to six.`
  - `Nothing to change on the TV.` / `Choose off, mild, family or strict on
    your phone; the televisions pick it up.`
  - `Link a TV by typing its code.` / `The TV shows a short code. That is the
    whole setup.`
- No button in this section.

### 2.4 What it works with, and what it does not

Purpose: the honest list, kept short, both halves at once.

- `.h-split`: desktop two columns `1fr 1fr`, gap 48 px; phone stacked, gap
  32 px. Each column has an `h2` in the section-head style at the smaller end
  (`font-size: 1.5rem`).
- Left, H2 `What it works with`, then `.h-chips` (a `<ul>`; each `li` is a
  chip: `--surface`, `1px solid --line`, radius 999 px, padding 8 px 14px,
  0.9375rem, weight 600, flex-wrap gap 8 px). Chips, text only, no logos:
  `Android TV`, `Google TV`, `TV boxes`, `Android phone`, `Stremio`, `Netflix
  and other apps on Android TV`, `Windows PC (early beta)`.
  Under the chips, 0.9375rem `--ink-soft`: `It works with titles you start in
  Stremio, and follows along while you watch Netflix and other apps on your
  Android TV or Google TV. Needs version 0.2.21 or newer. Family Filter TV is
  not affiliated with Netflix.` Then the link `Will it work on my TV?` to
  `which-tvs.html`.
- Right, H2 `Good to know`, a plain `<ul>` in `--ink-soft`:
  - `It mutes swearing in speech. Violence and nudity are not filtered.`
  - `It needs subtitles. The app tells you on screen when a title cannot be
    filtered.`
  - `Nothing is cut, blurred or skipped. Only the sound drops, for the length
    of that line.`
  - `It is not a streaming library and does not provide films, series or
    subscription access.`
  - `It does not work with the built-in apps of Samsung, LG and other
    non-Android TVs. English titles only for follow-along.`
- No visual in this section. The chips and the two short lists are the
  visual.

### 2.5 What it costs

Purpose: price, trial and the install, side by side.

- H2: `What it costs`.
- `.h-price-grid`: desktop `minmax(0, 420px) minmax(0, 1fr)`, gap 48 px,
  align-items start; phone stacked, gap 24 px.
- Left: the existing price card. **Keep the `.price` markup and every id
  exactly as it is today** (`price-country`, `price-country-input`,
  `price-country-list`, `price-annual`, `price-launch`, `price-launch-pct`,
  `price-launch-seats`, `price-launch-price`, `price-launch-next`,
  `price-launch-end`, `price-devices`, `price-note`, `price-note-country`);
  `price.js` writes into them. Keep the seven list items as they are.
- Right, `.h-price-copy`: `h3` `Try it free for 14 days.` then one paragraph
  `Google Play shows and charges the price in your own currency. One account
  covers three devices, and up to six if you need them.` then the `.btn`
  `Get it on Google Play`, then one muted line: `Have an invite from a friend?
  Enter it when you sign in.` linking `How inviting works` to
  `setup.html#invite`.

### 2.6 Questions

Purpose: keep every FAQ the structured data lists on the page, visibly, at a
fraction of the height.

- `.wrap` width. H2: `Questions`.
- `.h-faq`: eleven `<details>` elements, each `<summary>` holding an `h3` with
  the question, the answer paragraph inside. First one `open`. No JS.
- Questions and answers: the eleven already on the page, in the same order,
  same wording (the nine from the FAQPage JSON-LD plus `Will it work on my
  TV?` and `Something isn't working.`). Do not shorten the nine that are in the
  JSON-LD; search engines compare them to the page.
- Style: `border-top: 1px solid --line` on each, `summary` padding-block
  16 px, cursor pointer, `list-style: none` with a custom plus/minus drawn
  with CSS (a 12 px `+` that rotates 45° when open, 200 ms). Answer
  `--ink-soft`, padding-bottom 18 px.

### 2.7 Guides

Purpose: keep the internal links to the guide pages (they matter for search),
in a tenth of the space.

- `.wrap` width. H2: `Guides`. Lead: `Start with the guide that matches what
  you want to do.`
- `.h-guides`: a `<ul>` list, desktop two columns (`columns: 2; column-gap:
  32px` or a grid), phone one; each `li` is the link in `strong` followed by
  its short description from today's page, in `--muted`, 0.9375rem. Keep all
  ten links and their current `href`s and description text unchanged.

### 2.8 Install band

Purpose: the last thing on the page is the install.

- `.h-install`: `wrap-wide`, a `--field` card, `1px solid --field-line`,
  radius 18 px, padding 40 px 32px, text centred, background-image the same
  cyan radial the old `.meter` had.
- Content, top to bottom: `assets/icon-192.png` at 72×72, radius 16 px,
  `alt=""`; `h2` `Family Filter TV` (section-head style); `p` `The first 14
  days are free.` in `.lead`; the `.btn` `Get it on Google Play`; a
  `.foot-nav`-style row of quiet links: `Other ways to install`
  (`download.html`), `Windows PC (early beta)` (`download.html#windows`),
  `Watch the 30-second video on YouTube` (`https://youtu.be/4Mra6u1hmuI`).

### 2.9 Removed from the home page

The following leave `index.html` (their content lives on the pages linked):
the icon in the hero, the boxed meter block, the "Looking for a TV profanity
filter?" panel (becomes 2.7), the "Watching on a Windows PC?" section (one chip
and two links remain), the "Invite a friend" section (one line in 2.5 remains;
the full text is on `setup.html#invite`), and the long "What it works with"
and "One filter" bullet panels (replaced by 2.3 and 2.4).

### 2.10 Footer

Unchanged, plus one `p.fine` line after the existing not-affiliated line:
`The film clip in our videos is from Tears of Steel, (CC) Blender Foundation |
mango.blender.org, CC BY 3.0.`

---

## 3. Motion rules

All motion is CSS plus one inline vanilla script (3.2), no framework, no
library, no external script. Everything respects reduced motion (3.5).

### 3.1 Durations and easing

| Token | Value | Used for |
|---|---|---|
| `--ease-out` | `cubic-bezier(0.2, 0, 0, 1)` | reveals, hovers |
| `--ease-hush` | `cubic-bezier(0.32, 0, 0.24, 1)` | meter bars dropping (existing) |
| `--dur-fast` | `160ms` | hover, focus, play button |
| `--dur-reveal` | `480ms` | scroll reveals |
| `--dur-hush` | `360ms` | bars dropping; bars return in `240ms` |

### 3.2 The one script

Inline `<script>` at the end of `<body>`, under 2 KB, wrapped in an IIFE. It
does only this:

1. `document.documentElement.classList.add('js')` so CSS can hide reveal
   elements only when JS is there to show them.
2. Hero loop: if `matchMedia('(prefers-reduced-motion: reduce)').matches` or
   `navigator.connection && navigator.connection.saveData`, do not play; show
   `.h-tv-play` (remove `hidden`) and stop. Otherwise, when the hero screen is
   at least 25% in view (IntersectionObserver), call `video.play()`; the
   returned promise rejecting means autoplay was refused, so show
   `.h-tv-play`. Pause when it leaves the viewport. Clicking `.h-tv-play`
   plays the loop (still muted) and hides the button.
3. Soundbar sync: on the loop's `timeupdate`, add `is-muted` to `.h-soundbar`
   while `currentTime` is between 3.7 and 4.4 s, remove it otherwise, and set
   the state label text from its `data-on`/`data-muted`. (Measured in the
   loop: the "Muted" label is on screen from 3.8 to 4.3 s.)
4. "Watch with sound": on click of `.h-play`, replace the `<source>` with
   `assets/media/launch-video.mp4`, add a `<track kind="captions"
   srclang="en" label="English" default src="assets/media/launch-video.en.vtt">`,
   set `muted = false`, `loop = false`, `controls = true`, call `load()` then
   `play()`, remove `is-muted`, set the soundbar label to `On` and freeze the
   bars (class `is-film` on `.h-soundbar`: no transitions), scroll the TV into
   view if it is not fully visible (`scrollIntoView({block: 'nearest',
   behavior: reduced-motion ? 'auto' : 'smooth'})`), and move focus to the
   video. The button text becomes `Playing with sound…` and it is `disabled`
   until the film ends.
5. On `ended` (or if `play()` rejects): restore the loop source, `muted = true`,
   `loop = true`, `controls = false`, remove the track, `load()`, play if
   allowed, re-enable the button with its original text.
6. Reveals: an IntersectionObserver with threshold 0.15 and `rootMargin:
   '0px 0px -8% 0px'` adds `is-in` to every `.reveal` once, then unobserves.
7. Step 2 loop video (if ASSET REQUEST 4 exists): the same observer as 2,
   same rules (no play under reduced motion or Save-Data).

Nothing else. No scroll listeners, no parallax, no cursor effects.

### 3.3 Scroll reveals

- Elements with `.reveal`: each section's head block, each step card, the
  household picture, the two split columns, the price card, the install band.
  Not the hero (it is already in view) and not the FAQ or guides (text that
  must not pop in while reading).
- CSS: `.js .reveal { opacity: 0; transform: translateY(14px); transition:
  opacity var(--dur-reveal) var(--ease-out), transform var(--dur-reveal)
  var(--ease-out); transition-delay: calc(var(--i, 0) * 70ms) }` and
  `.js .reveal.is-in { opacity: 1; transform: none }`. Step cards get
  `--i: 0/1/2`, split columns `0/1`. Nothing else is staggered.
- Without JS, `.reveal` is fully visible (the `.js` prefix guarantees it).

### 3.4 Hover and focus

- `.btn:hover`: background `#FAC77F` (existing) plus `transform:
  translateY(-1px)`; `:active` `translateY(0)`. Transition `--dur-fast`.
- `.btn-quiet:hover` unchanged (existing). Cards (`.h-steps li`, chips):
  `border-color: var(--field-line)` on hover, `--dur-fast`. No lift, no
  shadow.
- `.h-tv-play:hover` `transform: scale(1.05)`, `--dur-fast`.
- Focus: the existing `:focus-visible` rule (2 px amber outline, 3 px offset)
  applies to every link, button, `summary` and the `<video>` when it has
  controls. Do not remove outlines anywhere. On the dark `--field` ground the
  amber outline measures 9.3:1, so no special case is needed.

### 3.5 Reduced motion and no JS

`@media (prefers-reduced-motion: reduce)`: `.reveal` has no transition and is
visible; the soundbar bars have no transition; the hero loop does not play
(3.2), the poster shows with the play button, and a user who presses it gets
the loop anyway because that is an explicit request. "Watch with sound" works
the same. Without JS: the poster shows, `<noscript><style>` gives the hero
video `controls` (via `.h-video { pointer-events: auto }` and a sibling rule
that unhides `.h-tv-play`), the "Watch with sound" button is hidden
(`<noscript>` style `.h-play { display: none }`), and the YouTube link in the
install band remains the way to the film with sound.

### 3.6 Video and image loading attributes

- Hero loop `<video>`: `muted loop playsinline preload="none"`, no `autoplay`
  attribute (the script decides), `poster` set. The poster is the LCP element
  and is preloaded (4.1).
- Step 2 loop: `muted loop playsinline preload="none"`, poster set, below the
  fold.
- Every `<img>` below the hero: `loading="lazy" decoding="async"` and explicit
  `width`/`height`. The hero poster is on the `<video>`; there is no `<img>`
  above the fold except the 30 px brand icon in the header.

---

## 4. Performance budget

The page is judged on Core Web Vitals. Targets, measured on a throttled mobile
run (Lighthouse "mobile" preset): LCP under 2.5 s, CLS 0.00, INP under 200 ms,
Performance 90 or better.

### 4.1 LCP

- The LCP element is the hero poster, `assets/media/hero-poster-1280.jpg`
  (ASSET REQUEST 1, 1280×720, at most 90 KB). Until it exists the build agent
  makes it with the command in 9.1, which produces the same thing.
- `<head>` gets `<link rel="preload" as="image"
  href="assets/media/hero-poster-1280.jpg" fetchpriority="high">` directly
  after the stylesheet link. Nothing else is preloaded.
- The `<video>` has `preload="none"`: the 433 KB loop is fetched only when the
  script calls `play()`, after first paint, so it never competes with the
  poster, the CSS or the font.
- Fonts: keep the existing Google Fonts link (Manrope 500/600/700/800,
  `display=swap`) and the two preconnects.

### 4.2 Layout shift

- Every `<img>` and `<video>` has `width` and `height` attributes, and its box
  has `aspect-ratio` in CSS, so swapping assets or states never moves the
  page.
- Reveals animate `opacity` and `transform` only. The FAQ `details` open and
  close by user action only, so they do not count.
- `price.js` unhides the country row and the launch panel after load; that is
  existing behaviour inside a card and is unchanged, but the card gets
  `min-height: 300px` on desktop so the shift stays inside it.

### 4.3 Weight

Everything fetched before the user scrolls or clicks, on a 1280 px desktop
and a 390 px phone, excluding the hero loop video:

| Resource | Budget |
|---|---|
| `index.html` | ≤ 30 KB |
| `style.css` | ≤ 22 KB |
| `price.js` + `data/prices.json` | ≤ 20 KB (existing) |
| Manrope, 4 weights (woff2) | ≤ 90 KB (existing) |
| Hero poster | ≤ 90 KB |
| Brand icon in header (`icon-192.png`) | 50 KB (existing); ASSET REQUEST 8 brings it to ≤ 12 KB |
| Inline script | ≤ 2 KB |
| **Total before interaction** | **≤ 320 KB**, hard limit 600 KB |

Deferred (lazy, fetched on scroll): step visuals (≤ 70 KB each), the
household picture (≤ 90 KB), the step 2 loop (≤ 300 KB), the install band
icon (shared with the header, cached). Fetched on click only:
`launch-video.mp4` (1.8 MB) and its captions. Never referenced from the home
page: `hero-loop.webm` (it is 1.6 MB, four times the mp4; every browser that
plays VP9 plays the H.264 mp4), `app-icon-800.png` (563 KB), `icon-512.png`,
`launch-poster.jpg`, `mute-moment.jpg`, `works-with.jpg`, `short-vertical.mp4`.

### 4.4 Render blocking

Only `style.css` and the Google Fonts stylesheet block rendering, as today.
The hero video, its poster preload, `price.js` (`defer`) and the inline
script at the end of `<body>` do not. No `@import`.

---

## 5. Accessibility

### 5.1 Contrast (all on `--ground #0B0C0F` or `--field #0B1E3A`)

| Text | Colour | Ratio on ground | Ratio on field |
|---|---|---|---|
| Headings, body | `--ink #F2F1EC` | 17.3:1 | 14.7:1 |
| Section copy | `--ink-soft #C8C7C1` | 11.5:1 | 9.8:1 |
| Notes, kicker, captions | `--muted #9A9DA8` | 7.2:1 | 6.2:1 |
| Button text on amber | `#16181D` on `#F4B65C` | 9.9:1 | – |
| Soundbar labels | `--muted` on field | – | 6.2:1 |
| Focus outline | `--accent` on ground / field | 10.9:1 | 9.3:1 |

On `--surface #15171C` the same three text colours measure 15.9:1, 10.6:1 and
6.6:1. All pass AA (and AAA) for normal text; nothing below 0.8125rem uses
`--muted`. The cyan bars are not text.

### 5.2 Structure and controls

- One `h1`; one `h2` per section; `h3` only inside steps, FAQ summaries and
  the price copy. The heading outline reads as a table of contents.
- Actions that change the page are `<button type="button">`: "Watch with
  sound", the TV play button, FAQ summaries (native). Navigation is `<a>`.
- The hero `<video>` has `aria-label`. With `controls` on (film state, or no
  JS) the native controls are keyboard-operable; focus moves to the video when
  the film starts so the keyboard user lands on the controls. The silent loop
  has no controls because it carries no information the caption and
  transcript do not; it stays in the accessibility tree with the label above.
- The soundbar is decorative (`aria-hidden="true"`); the muted moment is
  described in the caption and transcript.
- The step 2 loop is decorative too (`aria-hidden="true"`) with the step text
  as its equivalent.
- `details`/`summary` for the FAQ are native and keyboard-operable; the
  `summary` keeps the visible focus outline.
- Scroll reveals never hide content from assistive tech: `opacity: 0` content
  is still in the accessibility tree, and the `.js` gate means no JS, no
  hiding.
- Skip link: add `<a class="skip" href="#main">Skip to content</a>` as the
  first child of `<body>` and `id="main"` on `<main>`; `.skip` is visually
  hidden until focused (position absolute, top 8 px, left 8 px, `--accent`
  background, 10 px 14px padding).
- `.visually-hidden` utility: the standard clip pattern.

### 5.3 Captions for the 30-second video

File `assets/media/launch-video.en.vtt`, attached as the default `<track>`
in film state. Also shown as plain text in the hero `<details>` transcript.
The dialogue is the film's; the bracketed cues describe what is on screen and
heard. Timings come from frame analysis; the build agent must play the file
once, confirm the audio contains no narration beyond the film line and the
music, and nudge cue times to match by ear. If there is a narrator, transcribe
it into the cues as spoken.

```
WEBVTT

00:00.000 --> 00:00.600
[Music. A film plays on a television.]

00:00.600 --> 00:03.700
Listen Celia, I was young…

00:03.700 --> 00:04.400
…and a [swear word muted]

00:04.400 --> 00:07.400
But that's no reason to destroy the world.

00:07.400 --> 00:10.000
[On screen: Automatically mute profanity on your Android TV.]

00:10.000 --> 00:13.600
[On screen: Nothing is cut, blurred or skipped. The sound comes straight back.]

00:13.600 --> 00:17.600
[On screen: You choose how strict. Off, mild, family or strict.]

00:17.600 --> 00:23.600
[On screen: One filter for the whole house. Set it on your phone. Every TV follows.]

00:23.600 --> 00:26.000
[On screen: Works with Stremio, Android TV, Google TV, TV boxes.]

00:26.000 --> 00:30.000
[On screen: Family Filter TV. The first 14 days are free. Get it on Google Play. familyfiltertv.com]
```

### 5.4 Alt text

| Image | `alt` |
|---|---|
| Header brand icon | `""` (the text next to it is the name) |
| Hero loop poster (via the video's `aria-label`) | `A film line plays; the one swear word is muted and the picture keeps going.` |
| Step 1 (`step-install.jpg`) | `A television and a phone, both showing the Family Filter TV app.` |
| Step 1 fallback icon | `""` |
| Step 2 poster (`step-link.jpg`) | `The TV shows a short code and the phone has it typed in.` |
| Step 3 (`step-levels.jpg` or `app-tv-settings.png`) | `The filter level screen on the TV: Off, Mild, Family and Strict, with Family selected.` |
| Household (`household-clean.jpg` / fallback) | `A phone set to Family, linked to three televisions labelled Lounge, Spare room and Kids' room, all showing Family.` |
| Install band icon | `""` |

---

## 6. CSS plan

### 6.1 Rule for shared pages

`style.css` is loaded by 47 pages. **No existing selector changes or is
removed.** All new rules go in one block appended at the end of the file
under the comment `/* ---------- home page (Oct 2026) ---------- */`, and
every new class is prefixed `h-` (or is one of `wrap-wide`, `reveal`, `skip`,
`visually-hidden`). The existing `.hero`, `.hero-mark`, `.meter`,
`.meter-bars`, `.meter-note` rules stay because
`android-tv-profanity-filter.html`, `mute-swearing-on-netflix.html` and
`mute-swearing-on-tv.html` use them. Acceptance: screenshots of those three
pages plus `setup.html`, `download.html` and `which-tvs.html` are
pixel-identical before and after (9.3).

### 6.2 New tokens (added to `:root`, additive)

```
--wrap-wide: 1120px;
--section-gap: clamp(56px, 8vw, 104px);
--radius-l: 18px;
--radius-m: 16px;
--ease-out: cubic-bezier(0.2, 0, 0, 1);
--ease-hush: cubic-bezier(0.32, 0, 0.24, 1);
--dur-fast: 160ms;
--dur-reveal: 480ms;
--dur-hush: 360ms;
--glow: rgba(53, 207, 232, 0.10);
--bar-off: #2C4463;
```

### 6.3 New components, in outline

| Selector | Rules in outline |
|---|---|
| `.wrap-wide` | `max-width: var(--wrap-wide); margin-inline: auto; padding-inline: 24px` (18 px ≤ 460 px) |
| `.h-section` | `padding-block: var(--section-gap)`; `.h-section + .h-section { padding-top: 0 }` so the gap is not doubled |
| `.h-section-head` | h2 sizing from 2.0; `.h-section-head + .lead { margin-bottom: 28px }` |
| `.h-kicker` | uppercase, 0.8125rem, 700, letter-spacing 0.08em, `--muted`, margin 0 0 14px |
| `.h-hero`, `.h-hero-copy` | grid from 2.1; phone order rules |
| `.h-price-line` | 0.9375rem `--muted`, margin-top 14px |
| `.h-tv`, `.h-tv-screen`, `.h-video`, `.h-tv-play` | from 2.1 |
| `.h-soundbar`, `.h-bars`, `.h-bars b`, `.h-soundbar.is-muted b`, `.h-soundbar-state` | from 2.1 and 3.1; bars `transition: height var(--dur-hush) var(--ease-hush), background var(--dur-hush)`, stagger `transition-delay: calc(var(--i) * 8ms)` on the way down and 0 on the way up (`.is-muted b` carries the delay, the base rule does not) |
| `.h-caption` | 0.8125rem `--muted`, margin 12px 4px 0, max-width none |
| `.h-transcript` | grid-column 1 / -1, 0.9375rem, `--muted`; `summary` 600 weight |
| `.h-steps`, `.h-steps li`, `.h-visual`, `.h-visual img`, `.h-visual video` | from 2.2 |
| `.h-house`, `.h-house img` | from 2.3 |
| `.h-facts` | three columns desktop, no bullets, `strong` on its own line |
| `.h-split`, `.h-chips`, `.h-chips li` | from 2.4 |
| `.h-price-grid`, `.h-price-copy` | from 2.5; `.price` unchanged, gets `min-height: 300px` only inside `.h-price-grid` |
| `.h-faq details`, `summary`, `summary::after` | from 2.6 |
| `.h-guides` | two columns desktop |
| `.h-install` | from 2.8 |
| `.reveal`, `.js .reveal`, `.js .reveal.is-in` | from 3.3 |
| `.skip`, `.visually-hidden` | from 5.2 |
| `@media (prefers-reduced-motion: reduce)` block | from 3.5 |
| `@media (min-width: 900px)` block | every desktop layout above; mobile-first, so phone rules are the defaults |

### 6.4 What is deleted

Nothing from `style.css`. From `index.html`: every element listed in 2.9 and
the inline `style="--h:…"` meter block in its old position (the heights move
to the soundbar). The old `.meter` block's `meter-note` text is reused in the
hero lead.

### 6.5 Fonts and icons

No new font. The only icons are two inline SVGs (play triangle, 14 px and
26 px) and the CSS plus sign on FAQ rows. No icon font, no emoji.

---

## 7. Other pages (second step; specify only)

The same system extends to the rest of the site with three shared pieces:
`.h-page-hero` (kicker + `h1.page-title` + `.lead` + one visual beside it on
desktop, under it on phone), `.h-visual` (the 16:9 frame from 2.2) and
`.h-install` (the closing band from 2.8). One visual per page, never more.

| Page | Headline treatment | The one visual | Shared components |
|---|---|---|---|
| `download.html` | Keep the `h1`; add kicker `Android TV, TV boxes, Android phone, Windows` | `short-vertical.mp4` (14 s, with sound) in a phone-shaped `.h-phone` frame (`aspect-ratio: 9 / 16`, max-width 300 px), click to play, `preload="none"`, poster ASSET REQUEST 9, captions file `short-vertical.en.vtt` written from the same cue text as 5.3 shortened to the short's on-screen lines | `.h-page-hero`, two `.h-steps`-style cards for "Google Play" and "Install directly", `.h-install` without the Google Play button (this page is the alternative) |
| `setup.html` | Keep the `h1`; kicker `About five minutes` | ASSET REQUEST 4 (the link-code loop) beside the quick start, silent, observer-played | `.h-page-hero`, the existing `.steps` list unchanged, `.h-faq` for "If it is not in sync" |
| `which-tvs.html` | Keep the `h1`; kicker `It depends on the system, not the brand` | ASSET REQUEST 10 (the 10-second home-screen test as a still) | `.h-page-hero`, existing table, `.h-install` |
| Guide pages (`android-tv-profanity-filter`, `google-tv-…`, `mute-swearing-on-tv`, `mute-swearing-on-netflix`, `profanity-filter-android-tv`, `stremio-profanity-filter`, `windows-profanity-filter`, the comparison pages, `family-movie-night-without-swearing`) | Keep each `h1`; kicker is the page's topic in four words | One still each from the existing set, re-encoded per ASSET REQUEST 7: the mute moment (`mute-moment.jpg`) for the "mute swearing" pages, the household picture for the family pages, the settings crop (ASSET 5) for "how the filtering works", the hero poster for the platform pages | `.h-page-hero`, `.h-install` |
| `titles/` pages | Unchanged in this step | – | – |

Pages that use `.hero`/`.meter` today (`android-tv-profanity-filter.html`,
`mute-swearing-on-netflix.html`, `mute-swearing-on-tv.html`) move to
`.h-page-hero` in this second step; until then they keep their current look.

---

## 8. ASSET REQUESTS

For the media step. Source is the launch-video render (`FamilyFilter/brag-output/work/`, per `assets/media/README.md`). Nothing may be photographed; everything is rendered from code or cropped from the launch video. Every file goes in `assets/media/`. Every raster also gets a `.webp` sibling at the same size where the budget says so.

1. **`hero-poster-1280.jpg`** (+ `.webp`). Purpose: LCP image and the first frame the visitor sees. 1280×720. ≤ 90 KB jpg, ≤ 60 KB webp. Must be the hero loop's frame at 1.0 s (the "ON" state, subtitle `Listen Celia, I was young…` visible, meter live). Until this exists the build agent produces it with the command in 9.1.
2. **`hero-loop-v2.mp4`**. Purpose: a seamless loop. 1280×720, 30 fps, 6.75 s, H.264, no audio track, ≤ 450 KB. Same content as `hero-loop.mp4` but without the fade from black at 0–0.6 s and the fade out at 6.6–6.75 s, so the first and last frames match the poster and the loop point is invisible. Keep the muted window at 3.8–4.3 s (the script's 3.7–4.4 window depends on it).
3. **`step-install.jpg`** (+ `.webp`). Purpose: step 1 visual. 1200×675. ≤ 70 KB. A television and a phone side by side, drawn in the same style as `household.jpg` (dark field ground, navy screens), both screens showing only the app icon and the name `Family Filter TV`. No headline text in the image.
4. **`step-link.mp4` + `step-link.jpg`**. Purpose: step 2 visual, a silent loop. 1200×675, 5 s, H.264, no audio, ≤ 300 KB; poster ≤ 60 KB. Content: TV on the left shows a code in the `7KD-M4Q` format (any made-up code in that alphabet, never a real one); phone on the right shows the `Link a device` field; the six characters appear one by one over 2 s; the phone shows `Lounge TV linked` for 1.5 s; hold 1 s; loop. No other text.
5. **`step-levels.jpg`** (+ `.webp`). Purpose: step 3 visual, the real settings screen. 1200×675. ≤ 60 KB. Crop of `app-tv-settings.png` starting at x 20, y 45 (so it runs from the `FamilyFilter` title through the `Strict` row), then scaled to 1200 wide. No retouching; it is the real screen.
6. **`household-clean.jpg`** (+ `.webp`) and **`household-tall.jpg`** (+ `.webp`). Purpose: section 2.3 visual without text in the picture. Wide: 1600×900, ≤ 90 KB. Tall: 900×1200, ≤ 70 KB, the same scene re-composed with the phone above the three TVs. Same render as `household.jpg` with the headline, subhead and the `familyfiltertv.com` footer removed; the phone set to `Family`, `3 TVS LINKED`, TVs labelled Lounge, Spare room, Kids' room.
7. **Re-encoded stills for the guide pages**: `mute-moment-1280.jpg`, `launch-poster-1280.jpg`, each 1280×720, ≤ 90 KB, plus `.webp` ≤ 60 KB. Purpose: section 7, one visual per guide page.
8. **`icon-192.webp`** (and keep the png). Purpose: the header and install band icon at ≤ 12 KB instead of 50 KB. 192×192.
9. **`short-vertical-poster.jpg`**. Purpose: poster for the vertical short on `download.html`. 720×1280, ≤ 60 KB, the short's frame at 1.0 s.
10. **`home-screen-test.jpg`** (+ `.webp`). Purpose: `which-tvs.html` visual. 1200×675, ≤ 60 KB. A TV home screen drawn from code: a row of plain app tiles, one labelled `Play Store` in text only and outlined in cyan, caption text in the image `If you see this, it works.` No Google or Android logos, no brand marks of any kind.
11. **`og-home.jpg`**. Purpose: a future social image (not wired in this build; the meta tags stay as they are). 1200×630, ≤ 200 KB. The mute moment with the meter in the corner and the line `Mutes the swearing. Keeps the show.` The Blender credit in small text at the bottom.

---

## 9. Build plan

### 9.1 Ordered checklist

Each task is one commit on a branch `build/home-redesign` from `main`. Do not
touch `titles/`, `tools/`, `data/`, `admin.html`, `price.js`.

1. Branch, then produce the poster if ASSET 1 has not landed:
   `ffmpeg -y -ss 1.0 -i assets/media/hero-loop.mp4 -frames:v 1 -vf scale=1280:720 -q:v 5 assets/media/hero-poster-1280.jpg`
   which measures about 57 KB (raise `-q:v` by 1 if it ever exceeds 90 KB). Commit.
2. Write `assets/media/launch-video.en.vtt` from 5.3. Play the video once
   with `ffplay` or in Chromium and adjust times by ear. Commit.
3. Append the token block (6.2) and the component block (6.3) to
   `style.css`. Run the before/after screenshot test (9.3 item 7) on the six
   other pages: they must be identical. Commit.
4. Rewrite `<main>` of `index.html` in this order: hero (2.1), how it works
   (2.2), household (2.3), works with (2.4), price (2.5), questions (2.6),
   guides (2.7), install band (2.8). Keep `<head>` byte-for-byte except for
   the one added preload link (4.1). Keep both JSON-LD blocks untouched. Add
   the skip link and `id="main"`. Add the footer credit line (2.10). Use the
   fallbacks for ASSETS 3–6 and mark each with `<!-- ASSET n -->`. Commit.
5. Add the inline script (3.2). Test each path by hand in Chromium: loop
   autoplays; soundbar flattens at the muted word and the label reads
   `Muted`; "Watch with sound" plays the film with captions and focus on the
   video; `ended` restores the loop; reduced motion shows the poster with the
   play button; `javascript.enabled=false` shows the poster with native
   controls and no "Watch with sound" button. Commit.
6. Run the acceptance list (9.3). Fix until everything passes. Commit.
7. Open a draft pull request into `main` with the measurements from 9.3 in
   the body.

### 9.2 Tools available in the build container

Chromium is pre-installed at `/opt/pw-browsers/chromium` with Playwright;
Node 22 and Python 3 are present; `ffmpeg`/`ffprobe` are present. Serve the
site with `python3 -m http.server 8000` from the repo root for every test.

### 9.3 Acceptance tests

Write them as `tools/check_home.py` (Python, stdlib plus Playwright) or
`tools/check-home.mjs`; either is fine. Each prints PASS/FAIL with the
measured value.

1. **Page height.** Playwright, `http://localhost:8000/`, after `networkidle`
   and with all `details` closed except the first: `document.documentElement
   .scrollHeight` ≤ 3,800 at 1280×800 and ≤ 6,200 at 390×844 (device scale 2).
2. **Fold.** At 390×844 the bottom of `.h-tv-screen` is above 844 px
   (`getBoundingClientRect().bottom <= 844`). At 1280×800 the whole `.h-tv`
   and the primary button are inside the viewport.
3. **Counts.** `img` elements: between 3 and 6 (header icon, three step
   visuals or fallbacks, household, install band icon; the step 2 loop is a
   `video`). `video` elements: 1 or 2. Visible words: strip tags, count
   whitespace-separated tokens inside `<main>` with `details` content
   included: ≤ 850.
4. **HTML validity.** `npx --yes html-validate@8 index.html` reports no
   errors (add a minimal `.htmlvalidate.json` with the `html-validate:
   recommended` preset if the defaults complain about the inline JSON-LD
   scripts, but do not disable rules to pass).
5. **JSON-LD.** Extract every `<script type="application/ld+json">`, parse
   with `json.loads`; both parse; the FAQPage `mainEntity` has 9 items and
   each `name` appears verbatim inside a `summary` on the page; the
   SoftwareApplication block is byte-identical to `main`.
6. **Links.** Every `href` on the page that is not `http(s):` or `mailto:`
   resolves to a file in the repo (strip `#fragment`; `titles/` resolves to
   `titles/index.html`). Every `#fragment` on an internal link exists as an
   `id` in the target file.
7. **Other pages unchanged.** Playwright full-page screenshots at 1280 and
   390 of `setup.html`, `download.html`, `which-tvs.html`,
   `android-tv-profanity-filter.html`, `mute-swearing-on-tv.html`,
   `mute-swearing-on-netflix.html` taken on `main` and on the branch (same
   fonts cached, animations disabled with `reducedMotion: 'reduce'`): zero
   differing pixels.
8. **Layout shift.** Playwright with a `PerformanceObserver` for
   `layout-shift` entries from navigation to `networkidle` plus 3 s, at both
   sizes: cumulative value 0.00 (allow ≤ 0.01).
9. **Weight.** Playwright request log until `networkidle`, no scroll, no
   click, mp4 requests excluded: total ≤ 600 KB; the hero poster response
   ≤ 90 KB; no request for `hero-loop.webm`, `app-icon-800.png`,
   `launch-video.mp4`, `household.jpg` (unless it is the fallback and only
   after scrolling).
10. **Lighthouse.** `CHROME_PATH=/opt/pw-browsers/chromium npx --yes
    lighthouse http://localhost:8000/ --preset=perf --form-factor=mobile
    --screenEmulation.mobile --chrome-flags="--headless --no-sandbox"
    --output=json --output-path=lh.json`: Performance ≥ 90, Accessibility
    ≥ 95, Best Practices ≥ 90, SEO ≥ 95, LCP ≤ 2.5 s, CLS ≤ 0.01. If Lighthouse
    cannot run in the container, record that and rely on tests 8 and 9.
11. **Contrast.** For every text colour pair in 5.1, compute the WCAG ratio in
    the script and assert ≥ 4.5.
12. **Reduced motion.** Playwright with `reducedMotion: 'reduce'`: the hero
    video `paused === true` after 3 s, `.h-tv-play` visible, every `.reveal`
    has `opacity` 1.
13. **No-JS.** Playwright with `javaScriptEnabled: false`: every `.reveal` is
    visible, the video has `controls`, `.h-play` is not displayed, the Blender
    credit text is present.
14. **Facts.** Grep the built page for the strings `US$14.99`, `14 days`,
    `Off, mild, family or strict` (case-insensitive), `three devices`, `up to
    six`, `0.2.21`, `not affiliated with Netflix`, `Blender Foundation`; all
    present. Grep for `★`, `rating`, `installs`, `users`, `testimonial`,
    `reviews`: none present.

---

## 10. Risks and what not to do

- **No invented numbers or voices.** No testimonials, star ratings, install
  counts, "trusted by", "as seen in", statistics, awards or quotes. The page
  has 12 installs today; it earns the rest by showing the product.
- **No claims beyond the facts in the brief.** It mutes spoken profanity; it
  needs subtitles; nothing is cut, blurred or skipped; no violence or nudity
  filtering; Android TV and Google TV sets and boxes plus an Android phone;
  Windows is an early beta; Stremio; follow-along with Netflix and other apps
  on Android TV needs 0.2.21 or newer; Off, Mild, Family, Strict; one household
  filter; three devices included, up to six; 14-day free trial then US$14.99 a
  year. Do not write "any app", "every TV", "100%", "never misses" or
  "blocks".
- **No brand marks.** No Netflix, Stremio, Google Play, Android, Samsung or LG
  logos, wordmarks, colours or badges anywhere on the page, including inside
  assets. Names appear as plain text only. The Google Play button stays a
  plain amber button with the words `Get it on Google Play`, as today.
- **Netflix wording.** Only the phrasing the live site already uses ("follows
  along while you watch Netflix and other apps on your Android TV"), always
  within sight of "Family Filter TV is not affiliated with Netflix." The
  footer line stays.
- **Keep the `<head>`.** Title, description, robots, canonical, Open Graph,
  Twitter card, icons, theme colour, font links, both JSON-LD blocks: byte-
  identical, plus the single preload link. Do not change `og:image` in this
  build (ASSET 11 is for a later change).
- **Keep `price.js` working.** Every id in 2.5 stays; test by loading the page
  with a South African time zone (`timezoneId: 'Africa/Johannesburg'` in
  Playwright) and seeing the launch panel appear without errors in the
  console.
- **Never autoplay sound.** The film state only ever starts from a click.
- **Credit.** The Blender credit must be visible wherever Tears of Steel
  footage shows: the hero caption and the footer line on the home page, and
  on every page from section 7 that uses a still from it.
- **No layout shift, no framework.** No CSS or JS from a CDN, no icon font,
  no animation library, no lazy-loading library. If a thing in this spec
  cannot be done with CSS and the script in 3.2, leave it out and say so in
  the pull request.
- **Do not touch the other pages' appearance.** Test 9.3 item 7 is the gate.
- **Do not fake assets.** Where an ASSET REQUEST is missing, ship the stated
  fallback and the `<!-- ASSET n -->` marker. Never draw a TV screenshot by
  hand or use a stock photo.
