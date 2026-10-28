#!/usr/bin/env python3
"""Generate the /titles/ SEO index pages for Family Filter TV (issue #269).

Reads titles/data.json (20-title test cohort, built from our own subtitle
analysis export and Cinemeta metadata lookups) and emits:

  - titles/<slug>/index.html   for each title
  - titles/index.html          browse/search index page
  - sitemap.xml                updated with /titles/ + the 20 detail pages
  - llms.txt                   updated with a /titles/ entry

Refresh from the analysis export (see refresh_titles):

  tools/build_titles.py --refresh <ratings-export.json> [--accept-changes]

Stdlib only. Re-running this script with unchanged data.json must produce
no further changes (idempotent) — see tools/README or docs/SEO_TITLE_INDEX_TEST.md
in the app repo for the verification protocol.
"""
import bisect
import json
import os
import re
import statistics
import sys
import xml.sax.saxutils as sax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "titles", "data.json")
SITEMAP_PATH = os.path.join(ROOT, "sitemap.xml")
LLMS_PATH = os.path.join(ROOT, "llms.txt")
SITE = "https://familyfiltertv.com"

# Date the page template last changed. Sitemap lastmod is the later of this and a
# title's analysis date, so a wording change gets recrawled.
TEMPLATE_UPDATED = "2026-10-21"

CATEGORY_ORDER = [
    "strong_profanity", "mild_profanity", "religious", "crude",
    "sexual_explicit", "suggestive", "slurs",
]

METHODOLOGY_SLUG = "methodology"
TITLE_LIMIT = 60  # longest <title> that shows in full in search results
DESCRIPTION_LIMIT = 155

# Which categories each filter profile mutes. Mirrors addon/src/profile.ts (itself a port of the
# app's core Profile.kt), so the pages explain the same profiles the app applies.
_MILD = ("strong_profanity", "slurs", "sexual_explicit")
_FAMILY = _MILD + ("mild_profanity", "religious")
PROFILE_CATEGORIES = {"mild": _MILD, "family": _FAMILY, "strict": tuple(CATEGORY_ORDER)}

PUBLISHER = {
    "@type": "Organization",
    "name": "Family Filter TV",
    "url": f"{SITE}/",
    "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/icon-192.png"},
}


def esc(s):
    return sax.escape(str(s))


def jsonld(obj):
    """JSON for a <script type="application/ld+json"> block; "</" cannot end the element."""
    return json.dumps(obj, indent=2).replace("</", "<\\/")


def runtime_to_iso(runtime):
    if not runtime:
        return None
    m = re.search(r"(\d+)", str(runtime))
    if not m:
        return None
    return f"PT{m.group(1)}M"


def nav(active, depth):
    """depth: 0 = site root, 2 = titles/<slug>/index.html"""
    up = "../" * depth
    def item(href, label, key):
        current = ' aria-current="page"' if key == active else ""
        return f'      <a href="{up}{href}"{current}>{label}</a>'
    links = [
        item("index.html", "Home", "home"),
        item("titles/", "Titles", "titles"),
        item("download.html", "Download", "download"),
        item("setup.html", "Get set up", "setup"),
        item("support.html", "Support", "support"),
        item("privacy.html", "Privacy", "privacy"),
        item("terms.html", "Terms", "terms"),
    ]
    return "\n".join(links)


def foot_nav(depth):
    up = "../" * depth
    links = [
        '      <a href="https://www.youtube.com/@FamilyFilterTV" rel="me noopener">YouTube</a>',
        '      <a href="https://www.instagram.com/familyfiltertv/" rel="me noopener">Instagram</a>',
        '      <a href="https://www.tiktok.com/@familyfiltertvapp" rel="me noopener">TikTok</a>',
        f'      <a href="{up}titles/">Titles</a>',
        f'      <a href="{up}guides.html">Guides</a>',
        f'      <a href="{up}download.html">Download</a>',
        f'      <a href="{up}setup.html">Get set up</a>',
        f'      <a href="{up}support.html">Support</a>',
        f'      <a href="{up}privacy.html">Privacy</a>',
        f'      <a href="{up}terms.html">Terms</a>',
    ]
    return "\n".join(links)


def header(active, depth):
    up = "../" * depth
    return f'''<header class="site-head">
  <div class="wrap">
    <a class="brand" href="{up}index.html">
      <img src="{up}assets/icon-192.png" alt="" width="30" height="30">
      Family Filter TV
    </a>
    <nav class="site-nav" aria-label="Pages">
{nav(active, depth)}
    </nav>
    <a class="btn btn-sm head-cta" href="https://play.google.com/store/apps/details?id=com.familyfiltertv.app">Get the app</a>
  </div>
</header>'''


def footer(depth):
    up = "../" * depth
    return f'''<footer class="site-foot">
  <div class="wrap">
    <p>Family Filter TV is made by Jacques du Preez in South Africa.</p>
    <p><a href="mailto:jacquesjdupreez@gmail.com">jacquesjdupreez@gmail.com</a></p>
    <nav class="foot-nav" aria-label="Footer">
{foot_nav(depth)}
    </nav>
    <p class="fine">An independent app. Not affiliated with, or endorsed by, Stremio or Google.</p>
  </div>
</footer>'''


def breadcrumb_html(depth, title=None):
    up = "../" * depth
    parts = [f'<a href="{up}index.html">Home</a>']
    if title is None:
        parts.append('<span aria-current="page">Titles</span>')
    else:
        parts.append(f'<a href="{up}titles/">Titles</a>')
        parts.append(f'<span aria-current="page">{esc(title)}</span>')
    return '<nav class="breadcrumb muted" aria-label="Breadcrumb">' + ' &rsaquo; '.join(parts) + '</nav>'


def breadcrumb_jsonld(items):
    """items: list of (name, url-or-None)"""
    elements = []
    for i, (name, url) in enumerate(items, start=1):
        el = {"@type": "ListItem", "position": i, "name": name}
        if url:
            el["item"] = url
        elements.append(el)
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": elements,
    }


def category_keys(counts):
    return [k for k in CATEGORY_ORDER if k in counts] + [k for k in counts if k not in CATEGORY_ORDER]


def category_rows(counts, category_labels):
    return [(category_labels.get(key, key), counts[key]) for key in category_keys(counts)]


def language_summary(t, category_labels, limit=None):
    """One plain sentence answering "how much swearing is in this film?"."""
    name = t["title"]
    total = t["totalFlagged"]
    if not total:
        return f"We found no flagged swearing in the English subtitles of {name}."
    rows = category_rows(t["counts"], category_labels)
    if limit:
        rows = sorted(rows, key=lambda r: -r[1])[:limit]
    cats = ", ".join(f"{val} {label.lower()}" for label, val in rows)
    words = "word" if total == 1 else "words"
    return f"We counted {total} flagged {words} in the English subtitles of {name}: {cats}."


SKIP_RELEASE = re.compile(r"commentary|cd ?[12]\b|trailer|sample|\bextras?\b", re.I)

# Fields copied from an export record onto a title. computedAt is handled separately so a
# page's date only moves when one of these actually changed.
ANALYSIS_FIELDS = ("label", "counts", "profiles", "cueCount", "release", "terms", "timeline")


LABELS = ("clean", "mild", "moderate", "strong")
PROFILE_KEYS = ("mild", "family", "strict")
COMPUTED_AT = re.compile(r"\d{4}-\d{2}-\d{2}T[\d:.]+Z")
SLUG = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def is_count(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def count_map(v, keys=None):
    return (
        isinstance(v, dict)
        and all(isinstance(k, str) and is_count(n) for k, n in v.items())
        and (keys is None or all(k in keys for k in v))
    )


def analysis_problems(r):
    """Why a record's analysis fields must not be published, or [] if they are well formed.

    The export is read from the database and these values are written into page HTML, so
    anything that is not exactly the expected shape is refused rather than escaped and hoped
    about. Messages name the field only; they never echo the offending value.
    """
    problems = []
    if r.get("label") not in LABELS:
        problems.append("label is not a known language level")
    if not count_map(r.get("counts"), CATEGORY_ORDER):
        problems.append("counts is not a map of known categories to whole numbers")
    profiles = r.get("profiles")
    if not count_map(profiles) or sorted(profiles) != sorted(PROFILE_KEYS):
        problems.append("profiles is not exactly mild/family/strict whole numbers")
    if not is_count(r.get("cueCount")) or r["cueCount"] == 0:
        problems.append("cueCount is not a positive whole number")
    if not isinstance(r.get("release", ""), str):
        problems.append("release is not text")
    if not isinstance(r.get("computedAt"), str) or not COMPUTED_AT.fullmatch(r["computedAt"]):
        problems.append("computedAt is not a timestamp")
    if "terms" in r:
        terms = r["terms"]
        if not isinstance(terms, dict) or not all(
            k in CATEGORY_ORDER and count_map(v) for k, v in terms.items()
        ):
            problems.append("terms is not known categories mapping words to whole numbers")
    if "timeline" in r:
        tl = r["timeline"]
        ok = (
            isinstance(tl, dict)
            and is_count(tl.get("bucketMs"))
            and tl["bucketMs"] > 0
            and tl["bucketMs"] % 60000 == 0
            and isinstance(tl.get("words"), list)
            and isinstance(tl.get("strongProfanity"), list)
            and len(tl["words"]) == len(tl["strongProfanity"])
            and all(is_count(n) for n in tl["words"] + tl["strongProfanity"])
        )
        if not ok:
            problems.append("timeline is not whole-minute slots of whole numbers")
    return problems


def check_titles(titles):
    """Stop the build if titles/data.json holds anything that is not safe to publish."""
    bad = []
    for t in titles:
        problems = analysis_problems(t)
        if not isinstance(t.get("slug"), str) or not SLUG.fullmatch(t["slug"]):
            problems.append("slug is not lowercase words joined by hyphens")
        elif t["slug"] == METHODOLOGY_SLUG:
            problems.append("slug is reserved for the methodology page")
        if not is_count(t.get("year")):
            problems.append("year is not a whole number")
        if not isinstance(t.get("title"), str) or not t["title"]:
            problems.append("title is missing")
        bad += [f'{t.get("videoId")}: {p}' for p in problems]
    if bad:
        sys.exit("titles/data.json is not safe to publish:\n  " + "\n  ".join(bad))


def usable(e):
    """The cohort's selection bar (site PR #20): a well-formed rated record with a good runtime
    fit, at least 400 subtitle lines, and no commentary/CD1/trailer/sample releases."""
    return (
        e.get("status") == "rated"
        and not analysis_problems(e)
        and (e.get("fit") or {}).get("classification") == "good"
        and e["cueCount"] >= 400
        and not SKIP_RELEASE.search(e.get("release") or "")
    )


def build_benchmark(export):
    """Flagged-word totals for every usable film in the subtitle-analysis export.

    Films only: the pages say "of the N films we have analysed", and the export also holds
    series episodes. A record with no type predates the field and was a film.
    """
    totals = sorted(
        sum(e["counts"].values())
        for e in export
        if isinstance(e, dict) and usable(e) and e.get("type", "movie") == "movie"
    )
    return {"filmCount": len(totals), "totals": totals}


def refresh_titles(titles, export, accept_changes=False):
    """Bring each title's analysis up to date with the export.

    A change that would surprise a parent is held back for a human look instead of being
    published: a different language level, or a total that moved by more than 10 words and
    more than half. Pass accept_changes=True (--accept-changes) once someone has checked.
    A malformed record is never applied, whatever the flag; its line starts with REJECTED.
    Returns (updated, held) lists of human-readable lines.
    """
    by_id = {e.get("videoId"): e for e in export if isinstance(e, dict)}
    updated, held = [], []
    for t in titles:
        e = by_id.get(t["videoId"])
        if not isinstance(e, dict) or e.get("status") != "rated":
            continue
        problems = analysis_problems(e)
        if problems:
            held.append(f'REJECTED {t["title"]}: {problems[0]}')
            continue
        if not usable(e):
            continue
        new = {k: e[k] for k in ANALYSIS_FIELDS if k in e}
        if all(t.get(k) == v for k, v in new.items()):
            continue
        old_total, new_total = t["totalFlagged"], sum(e["counts"].values())
        delta = abs(new_total - old_total)
        surprising = new["label"] != t["label"] or (delta > 10 and delta > 0.5 * max(old_total, 1))
        line = f'{t["title"]}: {t["label"]} {old_total} -> {new["label"]} {new_total}'
        if surprising and not accept_changes:
            held.append(line)
            continue
        t.update(new)
        t["labelText"] = new["label"].capitalize()
        t["totalFlagged"] = new_total
        t["computedAt"] = e["computedAt"]
        updated.append(line)
    return updated, held


def mask_term(term, category):
    """'f***' for display. Religious exclamations are ordinary words, so they stay readable."""
    if category == "religious":
        return term
    return " ".join(w if len(w) <= 2 else w[0] + "*" * (len(w) - 1) for w in term.split(" "))


def term_list(t, category):
    terms = (t.get("terms") or {}).get(category) or {}
    if not terms:
        return ""
    ordered = sorted(terms.items(), key=lambda kv: (-kv[1], kv[0]))
    return " (" + ", ".join(f"{esc(mask_term(term, category))} {esc(n)}" for term, n in ordered) + ")"


def minutes_label(index, bucket_ms):
    size = bucket_ms // 60000
    return f"{index * size} to {(index + 1) * size}"


def first_slot(slots):
    return next((i for i, n in enumerate(slots) if n), None)


def slot_when(i, bucket_ms):
    size = bucket_ms // 60000
    if i == 0:
        return f"in the first {size} minutes"
    return f"between minute {minutes_label(i, bucket_ms).replace(' to ', ' and ')}"


def label_pill(t):
    label = t["label"] if t.get("label") in LABELS else "mild"
    return f'<span class="pill pill-{label}"><span class="vh">Language level: </span>{esc(t["labelText"])}</span>'


def result_block(t, category_labels):
    """The answer at a glance: big total, language pill, one bar per category."""
    total = t["totalFlagged"]
    name = esc(t["title"])
    if not total:
        return f'''  <section class="result result-clean" aria-label="Result at a glance for {name}">
    <div class="result-head">
      <p class="result-calm">No flagged words</p>
      {label_pill(t)}
    </div>
    <div class="calm-line" aria-hidden="true"></div>
  </section>'''
    keys = category_keys(t["counts"])
    top = max(t["counts"][k] for k in keys) or 1
    bars = "\n".join(
        f'''      <li class="bar-row">
        <span class="bar-label">{esc(category_labels.get(k, k))}</span>
        <span class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:{100 * t["counts"][k] / top:.1f}%"></span></span>
        <span class="bar-num">{esc(t["counts"][k])}</span>
      </li>'''
        for k in keys
    )
    words = "flagged word" if total == 1 else "flagged words"
    return f'''  <section class="result" aria-label="Result at a glance for {name}">
    <div class="result-head">
      <p class="result-total"><span class="result-figure">{esc(total)}</span> <span class="result-unit">{words}</span></p>
      {label_pill(t)}
    </div>
    <ul class="bars" aria-label="Flagged words by category">
{bars}
    </ul>
  </section>'''


def stretch_word(n):
    return "stretch" if n == 1 else "stretches"


def chart_summary(t):
    """The chart in words, derived only from the timeline data."""
    tl = t["timeline"]
    words, strong, bucket_ms = tl["words"], tl["strongProfanity"], tl["bucketMs"]
    n = len(words)
    peak = max(range(n), key=lambda i: (words[i], -i))
    parts = [
        f"Bar chart of flagged words in each {span_word(bucket_ms)}-minute stretch of {t['title']}: "
        f"{n} stretches, from {min(words)} to {words[peak]} flagged words, busiest at minute "
        f"{minutes_label(peak, bucket_ms)}."
    ]
    strong_n = sum(1 for x in strong if x)
    if strong_n:
        parts.append(
            f"Strong profanity appears in {strong_n} {stretch_word(strong_n)}, first {slot_when(first_slot(strong), bucket_ms)}."
        )
    else:
        parts.append("No stretch has strong profanity.")
    return " ".join(parts)


CHART_W, CHART_H = 400, 190
CHART_LEFT, CHART_RIGHT, CHART_TOP, CHART_BOTTOM = 34, 8, 20, 26
AXIS_STEPS = (1, 2, 3, 4, 5, 6, 8, 10)


def timeline_chart(t):
    """Inline SVG: one bar per bucket, with the strong-profanity share drawn as a hushed, gapped top."""
    tl = t["timeline"]
    words, strong, bucket_ms = tl["words"], tl["strongProfanity"], tl["bucketMs"]
    n, top_word = len(words), max(words)
    size = bucket_ms // 60000
    plot_w = CHART_W - CHART_LEFT - CHART_RIGHT
    plot_h = CHART_H - CHART_TOP - CHART_BOTTOM
    base = CHART_TOP + plot_h
    slot = plot_w / n
    bw = min(slot * 0.66, 22)
    seg, gap = 9, 5
    summary = chart_summary(t)

    out = []
    for i in range(n):
        cx = CHART_LEFT + slot * (i + 0.5)
        x = cx - bw / 2
        tip = f"Minute {minutes_label(i, bucket_ms)}: {plural(words[i], 'flagged word')}"
        if strong[i]:
            tip += f", {strong[i]} strong profanity"
        h = max(words[i] / top_word * plot_h, 3) if words[i] else 2
        y = base - h
        body = ""
        if words[i]:
            # Stacked: the strong-profanity share sits on top as a hushed (gapped) stretch,
            # so a film with strong words everywhere still shows how much of each bar they are.
            sh = min(max(h * min(strong[i], words[i]) / words[i], 3), h) if strong[i] else 0
            if h - sh > 0.5:
                body += f'<rect class="bar" x="{x:.1f}" y="{y + sh:.1f}" width="{bw:.1f}" height="{h - sh:.1f}" rx="2"/>'
            bottom = y + sh
            while bottom - y > 0.5:
                seg_h = min(seg, bottom - y)
                if seg_h >= 2:
                    body += f'<rect class="hush" x="{x:.1f}" y="{bottom - seg_h:.1f}" width="{bw:.1f}" height="{seg_h:.1f}" rx="1"/>'
                bottom -= seg + gap
        else:
            body = f'<rect class="bar-q" x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="1"/>'
        out.append(f"<g><title>{esc(tip)}</title>{body}</g>")

    step = next(s for s in AXIS_STEPS if -(-n // s) <= 8)
    ticks = "".join(
        f'<text class="axis" x="{CHART_LEFT + slot * i:.1f}" y="{CHART_H - 7}" text-anchor="middle">{i * size}</text>'
        for i in range(0, n, step)
    )
    y_labels = (
        f'<text class="axis" x="{CHART_LEFT - 6}" y="{CHART_TOP + 4}" text-anchor="end">{top_word}</text>'
        f'<text class="axis" x="{CHART_LEFT - 6}" y="{base + 4}" text-anchor="end">0</text>'
    )
    grid = (
        f'<line class="grid" x1="{CHART_LEFT}" x2="{CHART_W - CHART_RIGHT}" y1="{CHART_TOP}" y2="{CHART_TOP}"/>'
        f'<line class="axis-line" x1="{CHART_LEFT}" x2="{CHART_W - CHART_RIGHT}" y1="{base}" y2="{base}"/>'
    )
    svg = (
        f'<svg class="chart-svg" viewBox="0 0 {CHART_W} {CHART_H}" role="img" aria-label="{esc(summary)}" '
        f'preserveAspectRatio="xMidYMid meet">'
        f"<title>Flagged words per {span_word(bucket_ms)}-minute stretch of {esc(t['title'])}</title>"
        f"<desc>{esc(summary)}</desc>{grid}{y_labels}{''.join(out)}{ticks}</svg>"
    )
    return f'''    <figure class="chart">
      {svg}
      <figcaption>
        <span class="key"><i class="sw sw-bar" aria-hidden="true"></i>Flagged words</span>
        <span class="key"><i class="sw sw-hush" aria-hidden="true"></i>Hushed top of a bar: the strong profanity in that stretch</span>
        <span class="chart-note">Each bar is one {esc(span_word(bucket_ms))}-minute stretch, scaled to this film's busiest stretch ({esc(top_word)} flagged words). Bottom axis: minutes into the film.</span>
      </figcaption>
    </figure>'''


def timeline_section(t):
    """When the language happens: first flagged word, first strong word, heaviest stretch."""
    timeline = t.get("timeline")
    if not timeline or not t["totalFlagged"] or not sum(timeline["words"]):
        return ""
    words, strong, bucket_ms = timeline["words"], timeline["strongProfanity"], timeline["bucketMs"]
    name = esc(t["title"])
    size = bucket_ms // 60000

    when = lambda i: slot_when(i, bucket_ms)  # noqa: E731
    lines = [f"The first flagged word in {name} comes {when(first_slot(words))}."]
    first_strong = first_slot(strong)
    if first_strong is None:
        lines.append("There is no strong profanity anywhere in the film.")
    else:
        lines.append(f"The first strong profanity comes {when(first_strong)}.")
    peak = max(range(len(words)), key=lambda i: (words[i], -i))
    peak_words = "word" if words[peak] == 1 else "words"
    lines.append(
        f"The heaviest stretch is minute {minutes_label(peak, bucket_ms)}, with {words[peak]} flagged {peak_words}."
    )
    quiet = sum(1 for n in words if not n)
    if quiet:
        span = "ten" if size == 10 else str(size)
        lines.append(f"{quiet} of the film's {len(words)} {span}-minute stretches have none at all.")

    body = "\n".join(f"    <p>{ln}</p>" for ln in lines)
    rows = "\n".join(
        f"            <tr><td>{esc(minutes_label(i, bucket_ms))}</td><td>{esc(words[i])}</td><td>{esc(strong[i])}</td></tr>"
        for i in range(len(words))
    )
    return f'''  <section aria-labelledby="timeline-heading">
    <h2 id="timeline-heading">When the swearing happens in {name}</h2>
{body}
{timeline_chart(t)}
    <details class="numbers">
      <summary>See the numbers</summary>
      <div class="table-scroll">
        <table>
          <thead><tr><th>Minutes</th><th>Flagged words</th><th>Strong profanity</th></tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
    </details>
  </section>'''


def rank_sentence(t, benchmark):
    """Where the film's total sits among every film we have analysed, in plain text."""
    totals = benchmark["totals"]
    n = benchmark["filmCount"]
    total = t["totalFlagged"]
    name = t["title"]
    if total == 0:
        clean = bisect.bisect_right(totals, 0)
        return (
            f"{name} is one of {clean} films with no flagged language, out of the {n} "
            f"films we have analysed."
        )
    below = 100 * bisect.bisect_left(totals, total) / n
    above = 100 * (n - bisect.bisect_right(totals, total)) / n
    if below >= above:
        return f"{name} has more flagged language than {min(99, round(below))}% of the {n} films we have analysed."
    return f"{name} has less flagged language than {min(99, round(above))}% of the {n} films we have analysed."


def typical_sentence(benchmark):
    """The middle and the average film's total, so a single count has something to sit against."""
    totals = benchmark["totals"]
    median = statistics.median(totals)
    mean = sum(totals) / len(totals)
    return (
        f"The middle film in our analysis has {median:g} flagged words and the average is "
        f"{mean:.0f} (a few very heavy films pull the average up)."
    )


def comparison_section(t, benchmark):
    """How this film's language compares with every film we have analysed."""
    if not benchmark:
        return ""
    total = t["totalFlagged"]
    name = esc(t["title"])
    lines = [rank_sentence(t, benchmark), typical_sentence(benchmark)]

    if total:
        m = re.search(r"(\d+)", str(t.get("runtime") or ""))
        if m:
            per_hour = total / (int(m.group(1)) / 60)
            rate = f"{per_hour:.0f}" if per_hour >= 10 else f"{per_hour:.1f}"
            lines.append(f"That works out to about {rate} flagged words an hour.")

    family = t["profiles"].get("family", 0)
    cues = t["cueCount"]
    if family:
        share = 100 * family / cues
        pct = f"{share:.0f}" if share >= 10 else f"{share:.1f}"
        lines.append(
            f"With the family filter on, {family} of {cues} subtitle lines are muted ({pct}%), "
            f"so the rest of the dialogue plays as normal."
        )

    body = "\n".join(f"    <p>{esc(ln)}</p>" for ln in lines)
    return f'''  <section aria-labelledby="compare-heading">
    <h2 id="compare-heading">How {name} compares</h2>
{body}
  </section>'''


def analysis_panel(t, category_labels):
    keys = category_keys(t["counts"])
    last_analysed = t["computedAt"][:10]
    if keys:
        cat_html = "\n".join(
            f'      <li>{esc(category_labels.get(key, key))}: {esc(t["counts"][key])}{term_list(t, key)}</li>'
            for key in keys
        )
        cat_block = f'''    <h3>Flagged by category</h3>
    <ul>
{cat_html}
    </ul>'''
    else:
        cat_block = '    <p>No flagged language was found in this release.</p>'

    profiles = t["profiles"]
    cue_count = t["cueCount"]
    profile_html = "\n".join(
        f'      <li class="tile"><span class="tile-name">{esc(name.capitalize())} filter:</span> '
        f'<span class="tile-num">{esc(muted)}</span> '
        f'<span class="tile-of">of {esc(cue_count)} subtitle lines muted</span></li>'
        for name, muted in profiles.items()
    )

    return f'''  <section class="panel" aria-labelledby="ffa-heading">
    <h2 id="ffa-heading">How much swearing is in {esc(t["title"])}?</h2>
    <p>{esc(language_summary(t, category_labels))}</p>
    <p><strong>Language level:</strong> {esc(t["labelText"])}</p>
    <p><strong>Total flagged words:</strong> {esc(t["totalFlagged"])}</p>
{cat_block}
    <h3>Lines muted per filter profile</h3>
    <ul class="tiles">
{profile_html}
    </ul>
    <p class="muted">Counted from English subtitles of a standard release; other cuts or versions
    may differ.</p>
    <p class="muted">Last analysed: {esc(last_analysed)}</p>
  </section>'''


def related_section(t, by_id, depth_up):
    items = []
    for rel_id in t["related"]:
        rel = by_id.get(rel_id)
        if not rel:
            continue
        items.append(
            f'      <li><a href="{depth_up}{rel["slug"]}/">{esc(rel["title"])} ({rel["year"]})</a> '
            f'&mdash; {esc(rel["labelText"])}</li>'
        )
    if not items:
        return ""
    return f'''  <section aria-labelledby="related-heading">
    <h2 id="related-heading">Related titles</h2>
    <ul>
{chr(10).join(items)}
    </ul>
  </section>'''


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def join_words(items):
    """'a', 'a and b', 'a, b and c'."""
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def span_word(bucket_ms):
    size = bucket_ms // 60000
    return "ten" if size == 10 else str(size)


SEVERITY = {"clean": "no swearing", "mild": "very mild language", "moderate": "moderate swearing",
            "strong": "heavy swearing"}


def severity_phrase(t):
    """The label in plain words, for a parent who has not seen our pill."""
    return SEVERITY.get(t.get("label"), SEVERITY["mild"])


def seo_style(t):
    """"question" (default): the page answers "does X have bad words". "guide": it answers
    "X parents guide". Set "seoStyle": "guide" on a title in titles/data.json for a film whose
    Search Console queries say "parents guide" (refreshes leave the field alone)."""
    return "guide" if t.get("seoStyle") == "guide" else "question"


def seo_title(t):
    """What the page is called in search results: the question parents type (or "parents guide"
    for a title set to that style) plus the real count. Longest form that fits TITLE_LIMIT."""
    name, year, total = t["title"], t["year"], t["totalFlagged"]
    count = plural(total, "swear word") if total else "no swearing"
    if seo_style(t) == "guide":
        base = f"{name} ({year}) parents guide"
        candidates = (f"{base}: {count} by type", f"{base}: {count}", base) if total else (f"{base}: {count}", base)
    else:
        q = f"Does {name} ({year}) have bad words?"
        candidates = (f"{q} {count}", q)
    return next((c for c in candidates if len(c) <= TITLE_LIMIT), f"Swear words in {name} ({year})")


def seo_h1(t):
    if seo_style(t) == "guide":
        return f"{t['title']} ({t['year']}) parents guide: swearing and language"
    return f"Does {t['title']} ({t['year']}) have bad words?"


def fword_forms(t):
    """[(masked term, count)] for every flagged term that contains the F-word, or None when the
    record carries no per-word detail to answer from."""
    terms = t.get("terms")
    if terms is None:
        return None if t["totalFlagged"] else []
    forms = {}
    for category, words in terms.items():
        for term, n in words.items():
            if "fuck" in term:
                masked = mask_term(term, category)
                forms[masked] = forms.get(masked, 0) + n  # masked forms of equal length merge
    return sorted(forms.items(), key=lambda f: (-f[1], f[0]))


def fword_count(t):
    forms = fword_forms(t)
    return None if forms is None else sum(n for _, n in forms)


def answer_lead(t, category_labels=None):
    """The answer first: (sentence, detail line). Everything comes from the record."""
    name, year, total, cues = t["title"], t["year"], t["totalFlagged"], t["cueCount"]
    if total:
        cats = ""
        if category_labels:
            rows = [(label.lower(), n) for label, n in category_rows(t["counts"], category_labels)]
            cats = " (" + ", ".join(f"{n} {label}" for label, n in rows) + ")"
        has = ("has bad words" if t["counts"].get("strong_profanity", 0)
               else "has some swearing but no strong profanity")
        sentence = (
            f"Yes, {name} ({year}) {has}: {plural(total, 'flagged word')} in its English "
            f"subtitles{cats}, counted across {cues:,} subtitle lines."
        )
    else:
        sentence = (
            f"No. {name} ({year}) has no flagged swearing in its English subtitles: "
            f"0 flagged words across {cues:,} subtitle lines."
        )
    strong = t["counts"].get("strong_profanity", 0)
    detail = f"Strong profanity: {strong}."
    fwords = fword_count(t)
    if fwords is not None:
        detail += f" F-word: {fwords}."
    timeline = t.get("timeline")
    if total > 1 and timeline and sum(timeline["words"]):
        words, bucket_ms = timeline["words"], timeline["bucketMs"]
        peak = max(range(len(words)), key=lambda i: (words[i], -i))
        first_strong = first_slot(timeline["strongProfanity"])
        if first_strong is not None:
            detail += f" First strong profanity: {slot_when(first_strong, bucket_ms)}."
        detail += f" Heaviest stretch: {slot_when(peak, bucket_ms)}."
    return sentence, detail


def seo_description(t):
    """At most DESCRIPTION_LIMIT characters: the answer and the real count, how bad it is in plain
    words, and that the TV app can mute it. Drops detail, never the count, when a long film name
    needs room."""
    name, year, total, cues = t["title"], t["year"], t["totalFlagged"], t["cueCount"]
    strong = t["counts"].get("strong_profanity", 0)
    sev = severity_phrase(t)
    guide = seo_style(t) == "guide"
    if total:
        who = "it" if total == 1 else "them"
        strong_bit = (f", {strong} of them strong profanity" if strong
                      else ", not strong profanity" if total == 1 else ", none of them strong profanity")
        count = plural(total, "flagged swear word")
        if guide:
            lead = f"{name} ({year}) parents guide to language: {count} ({sev}) in the English subtitles"
            mid = (strong_bit + ", listed by category.", strong_bit + ".", ".")
        else:
            lead = f"Yes: {name} ({year}) has {count} ({sev}) in its English subtitles"
            mid = (strong_bit + ".", ".")
        tails = (f" Family Filter TV can mute {who} on Android TV.", f" The TV app can mute {who}.", "")
    else:
        lead = (f"{name} ({year}) parents guide to language: " if guide else f"No: {name} ({year}) has no swearing, ") + \
            f"0 flagged words in {cues:,} English subtitle lines"
        mid = (".",)
        tails = (" Family Filter TV mutes swearing on Android TV.", " The TV app can mute it.", "")
    options = [lead + m + x for m in mid for x in tails]
    return next((h for h in options if len(h) <= DESCRIPTION_LIMIT), lead + mid[-1])


def faq_items(t, category_labels, benchmark=None):
    """[(question, answer)] as plain text. The visible FAQ and the FAQPage JSON-LD both come from
    here, so the two cannot drift apart."""
    name, total, cues = t["title"], t["totalFlagged"], t["cueCount"]
    items = []

    strong = t["counts"].get("strong_profanity", 0)
    answer = language_summary(t, category_labels)
    if not total:
        answer += f" That is 0 flagged words across {cues:,} subtitle lines."
    elif not strong:
        answer += " It is not strong profanity." if total == 1 else " None of them is strong profanity."
    items.append((f"How many swear words are in {name}?", answer))
    items.insert(0, (f"Does {name} have bad words?", " ".join(answer_lead(t, category_labels))))

    family = t["profiles"].get("family", 0)
    if total:
        kids = (
            f"That is a call for you, and it depends on how old your kids are. On language alone, {name} has "
            f"{severity_phrase(t)}: {plural(total, 'flagged word')} in {cues:,} subtitle lines"
            f"{', none of them strong profanity' if not strong else f', {strong} of them strong profanity'}. "
            f"With the family filter on, {family} lines would be muted."
        )
    else:
        kids = (
            f"On language, yes: we found no flagged swearing in the English subtitles of {name}, "
            f"across {cues:,} subtitle lines."
        )
    kids += " We only check spoken language, not violence, nudity or frightening scenes."
    items.append((f"Is {name} OK for kids?", kids))

    forms = fword_forms(t)
    if forms is not None:
        n = sum(c for _, c in forms)
        if n:
            detail = ", ".join(f"{term} {c}" for term, c in forms)
            answer = (
                f"Yes. We counted {plural(n, 'flagged word')} containing the F-word in the "
                f"English subtitles of {name}: {detail}."
            )
        elif total == 1:
            answer = f"No. The one flagged word in {name} is not the F-word."
        elif total:
            answer = f"No. None of the {total} flagged words in {name} is the F-word."
        else:
            answer = f"No. We found no flagged words at all in the English subtitles of {name}."
        if not n:
            answer += " Words that are bleeped or left out of the subtitles cannot be counted."
        items.append((f"Does {name} use the F-word?", answer))

    timeline = t.get("timeline")
    if total and timeline and sum(timeline["words"]):
        words, bucket_ms = timeline["words"], timeline["bucketMs"]
        peak = max(range(len(words)), key=lambda i: (words[i], -i))
        first_strong = first_slot(timeline["strongProfanity"])
        if first_strong is None:
            strong_line = "There is no strong profanity anywhere in the film."
        else:
            strong_line = f"The first strong profanity comes {slot_when(first_strong, bucket_ms)}."
        items.append((
            f"Where in {name} is the swearing heaviest?",
            f"The heaviest stretch is {slot_when(peak, bucket_ms)}, with "
            f"{plural(words[peak], 'flagged word')}. {strong_line} Our timeline uses "
            f"{span_word(bucket_ms)}-minute stretches, so that is as exact as we can be.",
        ))

    if benchmark:
        items.append((
            f"How does {name} compare with the average film?",
            f"{rank_sentence(t, benchmark)} {typical_sentence(benchmark)}",
        ))

    family, strict = t["profiles"].get("family", 0), t["profiles"].get("strict", 0)
    if family:
        muted = f"With the family filter on, {family} of the {cues:,} subtitle lines in {name} would be muted"
    else:
        muted = f"With the family filter on, none of the {cues:,} subtitle lines in {name} would be muted"
    muted += f"; with the strict filter, {strict} would be." if strict != family else "."
    items.append((
        f"Can I watch {name} without the swearing?",
        "Family Filter TV mutes matching language automatically while a title plays through a "
        "supported route such as Stremio, on Android TV and Android phones. The picture keeps "
        "playing and only the sound briefly drops. You choose a mild, family or strict filter. "
        f"{muted} Filtering availability varies by title, and the app tells you when it is unavailable.",
    ))

    items.append((
        f"Why might another site give a different swear word count for {name}?",
        "Our count comes from automated analysis of the English subtitles, and we count every time "
        "a flagged word appears. A word that is bleeped, mumbled or not written in the subtitles "
        "is not counted, a different subtitle release of the film can give a different number, "
        "and every site decides for itself what counts as a swear word.",
    ))
    return items


def faq_section(t, items):
    name = esc(t["title"])
    rows = "\n".join(
        f"      <div>\n        <h3>{esc(q)}</h3>\n        <p>{esc(a)}</p>\n      </div>" for q, a in items
    )
    return f'''  <section aria-labelledby="faq-heading">
    <h2 id="faq-heading">Questions about swearing in {name}</h2>
    <div class="faq">
{rows}
    </div>
  </section>'''


def faq_jsonld(items):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in items
        ],
    }


def methodology_box(depth_up):
    return f'''  <section class="panel" aria-labelledby="method-heading">
    <h2 id="method-heading">How we counted</h2>
    <p>The count comes from automated analysis of the film's English subtitles, not from a person
    listening to the film. Every time a flagged word appears it is counted, and each one is placed
    in a category. Other guides can give a different number for the same film: a word that is
    bleeped or not written in the subtitles cannot be counted, different subtitle releases of a
    film differ, and each site decides for itself what counts as a swear word.</p>
    <p><a href="{depth_up}{METHODOLOGY_SLUG}/">How we count swear words</a></p>
  </section>'''


def covering_profiles(category):
    names = [p for p in PROFILE_CATEGORIES if category in PROFILE_CATEGORIES[p]]
    if len(names) == 1:
        return f"only the {names[0]} filter"
    return f"the {join_words(names)} filters"


def low_count_section(t, by_id, category_labels):
    """Extra substance for a film with 0 to 3 flagged words: what was checked, what each filter
    level would do with it, and the other low-language films in the set."""
    if t["totalFlagged"] > 3:
        return ""
    name, total, cues = esc(t["title"]), t["totalFlagged"], t["cueCount"]
    profiles = t["profiles"]
    checked = f"We read all {cues:,} English subtitle lines of {name} and checked each one against our word list."
    if total:
        n = profiles.get("strict", 0)
        checked += f" {n} of them {'contains' if n == 1 else 'contain'} a flagged word."
    else:
        checked += " None of them contains a flagged word, so no filter level would mute anything."
    timeline = t.get("timeline")
    if not total and timeline and timeline["words"] and not sum(timeline["words"]):
        checked += (
            f" That holds across the whole film: all {len(timeline['words'])} {span_word(timeline['bucketMs'])}-minute "
            f"stretches of the subtitles have zero flagged words."
        )

    def labels(cats):
        return join_words(category_labels.get(c, c).lower() for c in CATEGORY_ORDER if c in cats)

    scopes = {
        "mild": labels(PROFILE_CATEGORIES["mild"]),
        "family": "the mild filter's categories plus "
        + labels(set(PROFILE_CATEGORIES["family"]) - set(PROFILE_CATEGORIES["mild"])),
        "strict": "every category",
    }
    profile_items = "\n".join(
        f"      <li><strong>{p.capitalize()} filter</strong> mutes {scopes[p]}. In {name}: "
        f"{profiles.get(p, 0)} of {cues:,} lines muted.</li>"
        for p in PROFILE_CATEGORIES
    )

    found = ""
    if t["counts"]:
        present = "\n".join(
            f"      <li>{esc(category_labels.get(c, c))} ({esc(t['counts'][c])}): muted by {covering_profiles(c)}.</li>"
            for c in category_keys(t["counts"])
        )
        found = f"\n    <p>What was flagged, and which filters cover it:</p>\n    <ul>\n{present}\n    </ul>"

    others = sorted(
        (o for o in by_id.values() if o is not t and o["totalFlagged"] <= 3),
        key=lambda o: (o["totalFlagged"], o["title"]),
    )
    other_html = ""
    if others:
        items = "\n".join(
            f'      <li><a href="../{o["slug"]}/">{esc(o["title"])} ({o["year"]})</a> &mdash; '
            f'{esc(plural(o["totalFlagged"], "flagged word"))} in {o["cueCount"]:,} subtitle lines</li>'
            for o in others
        )
        other_html = f'''
    <h3>Other films in our set with little or no flagged language</h3>
    <ul>
{items}
    </ul>'''

    return f'''  <section aria-labelledby="low-heading">
    <h2 id="low-heading">What we checked in {name}</h2>
    <p>{checked}</p>
    <h3>What each filter level would do</h3>
    <ul>
{profile_items}
    </ul>{found}{other_html}
  </section>'''


def title_page_html(t, by_id, category_labels, benchmark=None):
    slug = t["slug"]
    name = t["title"]
    year = t["year"]
    canonical = f"{SITE}/titles/{slug}/"
    page_title = seo_title(t)
    description = seo_description(t)
    lead, lead_detail = answer_lead(t, category_labels)
    faq = faq_items(t, category_labels, benchmark)

    runtime_iso = runtime_to_iso(t["runtime"])

    jsonld_work = {
        "@context": "https://schema.org",
        "@type": "Movie",
        "@id": f"{canonical}#film",
        "name": name,
        "datePublished": str(year),
        "genre": t["genres"],
        "sameAs": t["imdbUrl"],
    }
    if runtime_iso:
        jsonld_work["duration"] = runtime_iso

    jsonld_page = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "url": canonical,
        "name": page_title,
        "description": description,
        "inLanguage": "en",
        "dateModified": t["computedAt"],
        "about": {"@id": f"{canonical}#film"},
        "publisher": PUBLISHER,
        "isPartOf": {"@type": "WebSite", "name": "Family Filter TV", "url": f"{SITE}/"},
    }

    jsonld_breadcrumb = breadcrumb_jsonld([
        ("Home", f"{SITE}/"),
        ("Titles", f"{SITE}/titles/"),
        (name, canonical),
    ])

    breadcrumb = breadcrumb_html(2, title=name)
    related = related_section(t, by_id, "../")
    detail = "\n\n".join(
        part for part in (
            low_count_section(t, by_id, category_labels),
            timeline_section(t),
            comparison_section(t, benchmark),
            faq_section(t, faq),
            methodology_box("../"),
        ) if part
    )

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#0B0C0F">
<link rel="icon" href="../../assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="../../assets/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="../../assets/apple-touch-icon.png">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(page_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{SITE}/assets/feature-graphic.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="../../style.css">
<script src="../../hit.js" defer></script>
<link rel="stylesheet" href="../film.css">
<script type="application/ld+json">
{jsonld(jsonld_work)}
</script>
<script type="application/ld+json">
{jsonld(jsonld_page)}
</script>
<script type="application/ld+json">
{jsonld(jsonld_breadcrumb)}
</script>
<script type="application/ld+json">
{jsonld(faq_jsonld(faq))}
</script>
</head>
<body>
{header("titles", 2)}

<main class="wrap">
  {breadcrumb}
  <p class="muted">Parents guide: swearing and language</p>
  <h1 class="page-title">{esc(seo_h1(t))}</h1>
  <section class="panel answer-box" aria-label="Short answer">
    <p class="lead">{esc(lead)}</p>
    <p class="lead"><strong>{esc(lead_detail)}</strong></p>
  </section>

{result_block(t, category_labels)}

  <p>{esc(t["intro"])}</p>
  <p class="muted">This guide covers spoken language only. It does not rate violence, nudity or
  frightening scenes.</p>

{analysis_panel(t, category_labels)}

{detail}

  <section aria-labelledby="can-filter-heading">
    <h2 id="can-filter-heading">What Family Filter TV can filter</h2>
    <ul>
      <li>Profanity, matched against your chosen filter profile (mild, family or strict).</li>
      <li>Subtitle-driven mute events &mdash; the sound briefly drops on a matching line and
      returns right after.</li>
    </ul>
  </section>

  <section aria-labelledby="how-heading">
    <h2 id="how-heading">How filtering works</h2>
    <p>Open the title through a supported playback route such as Stremio. Family Filter TV
    analyses subtitle cues against your household filter settings and automatically mutes
    matching dialogue during playback. The picture keeps playing &mdash; only the sound briefly
    drops.</p>
  </section>

  <section aria-labelledby="supported-heading">
    <h2 id="supported-heading">Supported now</h2>
    <p>Playback handed from Stremio to Family Filter TV on Android TV and Android phones.</p>
  </section>

  <div class="actions">
    <a class="btn" href="../../download.html">Watch with Family Filter TV</a>
    <a class="btn-quiet" href="../../setup.html">Get set up</a>
    <a class="btn-quiet" href="../../stremio.html">About the Stremio add-on</a>
    <a class="btn-quiet" href="../../mute-swearing-on-tv.html">How muting swearing on TV works</a>
  </div>

{related}

  <p class="fine">Family Filter TV is an independent app. It is not affiliated with, endorsed by,
  or connected to Stremio, Google, or any streaming service.</p>
</main>
{footer(2)}
</body>
</html>
'''


def methodology_page_html(titles, category_labels):
    canonical = f"{SITE}/titles/{METHODOLOGY_SLUG}/"
    page_title = "How We Count Swear Words in Films | Family Filter TV"
    description = (
        "How Family Filter TV counts swear words: automated analysis of English subtitles, what "
        "each category means for the filter profiles, and why our number can differ from other "
        "parents guides."
    )
    jsonld_page = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "url": canonical,
        "name": "How we count swear words",
        "description": description,
        "inLanguage": "en",
        "dateModified": TEMPLATE_UPDATED,
        "publisher": PUBLISHER,
        "isPartOf": {"@type": "WebSite", "name": "Family Filter TV", "url": f"{SITE}/"},
    }
    jsonld_breadcrumb = breadcrumb_jsonld([
        ("Home", f"{SITE}/"),
        ("Titles", f"{SITE}/titles/"),
        ("How we count swear words", canonical),
    ])

    category_rows_html = "\n".join(
        f"          <tr><td>{esc(category_labels.get(c, c))}</td>"
        + "".join(f"<td>{'Yes' if c in PROFILE_CATEGORIES[p] else 'No'}</td>" for p in PROFILE_CATEGORIES)
        + "</tr>"
        for c in CATEGORY_ORDER
        if c in category_labels
    )
    example = next((t for t in sorted(titles, key=lambda x: -x["totalFlagged"])), None)
    example_link = (
        f' For a worked example, see <a href="../{example["slug"]}/">{esc(example["title"])} ({example["year"]})</a>.'
        if example else ""
    )

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#0B0C0F">
<link rel="icon" href="../../assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="../../assets/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="../../assets/apple-touch-icon.png">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(page_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{SITE}/assets/feature-graphic.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="../../style.css">
<script src="../../hit.js" defer></script>
<script type="application/ld+json">
{jsonld(jsonld_page)}
</script>
<script type="application/ld+json">
{jsonld(jsonld_breadcrumb)}
</script>
</head>
<body>
{header("titles", 2)}

<main class="wrap">
  {breadcrumb_html(2, title="How we count swear words")}
  <h1 class="page-title">How we count swear words</h1>
  <p class="lead">Every number on a film page comes from software reading the film's English
  subtitles. Nobody watches the film and tallies words by ear. This page explains what is counted,
  what is not, and why our figure can differ from other parents guides.</p>

  <section aria-labelledby="counted-heading">
    <h2 id="counted-heading">What is counted</h2>
    <ul>
      <li>The text of the film's English subtitle file. Formatting tags and styling codes are
      removed first, so only the words on screen are read.</li>
      <li>Each subtitle line is checked against a word list. A word matches as a whole word,
      ignoring capital letters, together with a fixed set of common endings such as -s, -ed and
      -ing. Some entries also match inside a longer compound word. A list of exceptions stops
      ordinary words that look similar from being flagged.</li>
      <li>Every appearance counts. If a word is said ten times, it adds ten to the total. Nothing
      is de-duplicated.</li>
      <li>Each flagged word is filed under a category, and we keep the count for each word. On
      the film pages the words are masked, for example f***, except for religious exclamations,
      which are ordinary words.</li>
      <li>The word list and the filter profiles are the same ones the Family Filter TV app uses
      to mute, so the page counts what the app would act on.</li>
    </ul>
  </section>

  <section aria-labelledby="categories-heading">
    <h2 id="categories-heading">The categories and the filter profiles</h2>
    <p>Flagged words fall into these categories. The table shows which categories each filter
    profile mutes.</p>
    <div class="table-scroll">
      <table>
        <thead><tr><th>Category</th><th>Mild filter</th><th>Family filter</th><th>Strict filter</th></tr></thead>
        <tbody>
{category_rows_html}
        </tbody>
      </table>
    </div>
    <p>Each film page also shows how many subtitle lines each profile would mute. That is a count
    of lines, not words: a line with three flagged words is one muted line but adds three to the
    word count, and a line is muted only if it holds a word in a category the profile covers.</p>
  </section>

  <section aria-labelledby="level-heading">
    <h2 id="level-heading">The language level</h2>
    <p>The level shown on each page (clean, mild, moderate or strong) comes from the number of
    lines the filter profiles would mute, checked in this order:</p>
    <ul>
      <li><strong>Clean:</strong> the strict filter would mute no lines.</li>
      <li><strong>Mild:</strong> the mild filter would mute no lines and the strict filter at most
      5.</li>
      <li><strong>Moderate:</strong> the mild filter would mute 1 to 9 lines, or the strict filter
      6 to 30.</li>
      <li><strong>Strong:</strong> anything above that.</li>
    </ul>
  </section>

  <section aria-labelledby="timeline-method-heading">
    <h2 id="timeline-method-heading">Where in the film</h2>
    <p>Each flagged word is placed in a ten-minute stretch of the film, by the start time of the
    subtitle line it is in. That is why the pages say &ldquo;between minute 20 and 30&rdquo; and
    never give an exact time for a word.</p>
  </section>

  <section aria-labelledby="source-heading">
    <h2 id="source-heading">Which subtitles we use</h2>
    <p>We look for English subtitle files for the film. Where there is more than one, we use the
    file whose last line best matches the film's running time, and a file that is clearly timed
    for a different cut of the film is not used. Each film page shows the date it was last
    analysed.</p>
    <p>The comparisons with &ldquo;films we have analysed&rdquo; use only films where the subtitle
    timing matched the running time closely and the subtitles have at least 400 lines.</p>
  </section>

  <section aria-labelledby="differ-heading">
    <h2 id="differ-heading">Why our number can differ from other sites</h2>
    <ul>
      <li><strong>Bleeped or partly spoken words.</strong> We count words written in the
      subtitles. A word that is bleeped, muffled or left out of the subtitle file cannot be
      counted, even if a viewer hears it or another guide lists it.</li>
      <li><strong>Different subtitle releases.</strong> Subtitle files for the same film are not
      identical. A different release, or a different cut of the film, can give a different
      number.</li>
      <li><strong>What counts as a swear word.</strong> Our list has {len(PROFILE_CATEGORIES["strict"])} categories, including
      religious exclamations and crude language alongside strong profanity. Other sites choose
      their own scope, so totals are not directly comparable. To compare like with like, look at
      the strong profanity figure, or at the F-word figure, which counts every flagged word that
      contains it.</li>
      <li><strong>Counting every appearance.</strong> We count each time a word appears, not
      each scene it appears in.</li>
    </ul>
  </section>

  <section aria-labelledby="not-heading">
    <h2 id="not-heading">What these numbers do not cover</h2>
    <p>They cover language only. They do not rate violence, nudity or frightening scenes, and we
    do not recommend an age for any film.{example_link}</p>
  </section>

  <div class="actions">
    <a class="btn-quiet" href="../">All titles</a>
    <a class="btn" href="../../download.html">Watch with Family Filter TV</a>
  </div>

  <p class="fine">Family Filter TV is an independent app. It is not affiliated with, endorsed by,
  or connected to Stremio, Google, or any streaming service.</p>
</main>
{footer(2)}
</body>
</html>
'''


def index_page_html(titles, category_labels):
    canonical = f"{SITE}/titles/"
    page_title = "Parents Guides to Swearing in Films | Family Filter TV"
    description = (
        "Parents guides to the swearing and language in specific films: exact flagged word "
        "counts by category, from Family Filter TV's own subtitle analysis."
    )

    jsonld_breadcrumb = breadcrumb_jsonld([
        ("Home", f"{SITE}/"),
        ("Titles", canonical),
    ])

    top = max((t["totalFlagged"] for t in titles), default=0) or 1
    rows = []
    for t in sorted(titles, key=lambda x: x["title"]):
        total = t["totalFlagged"]
        # square-root scale: one very heavy film would otherwise flatten every other bar
        pct = 100 * (total / top) ** 0.5 if total else 0
        words = "word" if total == 1 else "words"
        rows.append(
            f'      <li class="title-row" data-search="{esc(t["title"].lower())}">'
            f'<a class="title-link" href="{t["slug"]}/">{esc(t["title"])} ({t["year"]})</a>'
            f'<span class="title-meta">{label_pill(t)} '
            f'<span class="title-count">{esc(total)} flagged {words}</span></span>'
            f'<span class="title-bar" aria-hidden="true"><span style="width:{pct:.1f}%"></span></span></li>'
        )

    breadcrumb = breadcrumb_html(1, title=None)

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#0B0C0F">
<link rel="icon" href="../assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="../assets/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(page_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{SITE}/assets/feature-graphic.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="../style.css">
<script src="../hit.js" defer></script>
<link rel="stylesheet" href="film.css">
<script type="application/ld+json">
{jsonld(jsonld_breadcrumb)}
</script>
</head>
<body>
{header("titles", 1)}

<main class="wrap">
  {breadcrumb}
  <h1 class="page-title">Parents guides: swearing and language by film</h1>
  <p class="lead">How much swearing is in a film, counted word by word from Family Filter TV's
  own subtitle analysis. These guides cover spoken language only, not violence, nudity or
  frightening scenes.</p>

  <p>
    <label for="title-search" class="muted">Search titles</label><br>
    <input type="search" id="title-search" class="price-country" style="max-width:420px"
      placeholder="Search by title&hellip;" autocomplete="off"
      oninput="document.querySelectorAll('.title-row').forEach(function(li){{
        li.hidden = !li.dataset.search.includes(this.value.toLowerCase());
      }}, this)">
  </p>

  <ul id="title-list" class="title-grid">
{chr(10).join(rows)}
  </ul>

  <p class="muted">This is a small, 20-title test set &mdash; not the full catalogue. See
  <a href="{METHODOLOGY_SLUG}/">how we count swear words</a>,
  <a href="../stremio-profanity-filter.html">how Stremio filtering works</a> or
  <a href="../download.html">download Family Filter TV</a>.</p>

  <p class="fine">Family Filter TV is an independent app. It is not affiliated with, endorsed by,
  or connected to Stremio, Google, or any streaming service.</p>
</main>
{footer(1)}
</body>
</html>
'''


def update_sitemap(titles):
    with open(SITEMAP_PATH, "r") as f:
        content = f.read()

    lines = content.splitlines()
    kept = [ln for ln in lines if "/titles/" not in ln]
    # keep the entries where they already sit, so a rerun does not shuffle the file
    first_titles = next((i for i, ln in enumerate(lines) if "/titles/" in ln), None)
    insert_idx = None if first_titles is None else sum(1 for ln in lines[:first_titles] if "/titles/" not in ln)

    # last-known-good lastmod for the index = most recent analysis date in the cohort
    index_lastmod = max(TEMPLATE_UPDATED, max(t["computedAt"][:10] for t in titles))

    new_entries = [
        f'  <url><loc>{SITE}/titles/</loc><lastmod>{index_lastmod}</lastmod><priority>0.8</priority></url>',
        f'  <url><loc>{SITE}/titles/{METHODOLOGY_SLUG}/</loc><lastmod>{TEMPLATE_UPDATED}</lastmod><priority>0.5</priority></url>',
    ]
    for t in sorted(titles, key=lambda x: x["slug"]):
        lastmod = max(TEMPLATE_UPDATED, t["computedAt"][:10])
        new_entries.append(
            f'  <url><loc>{SITE}/titles/{t["slug"]}/</loc><lastmod>{lastmod}</lastmod><priority>0.6</priority></url>'
        )

    # first run: before the closing </urlset>
    close_idx = insert_idx if insert_idx is not None else next(i for i, ln in enumerate(kept) if "</urlset>" in ln)
    out_lines = kept[:close_idx] + new_entries + kept[close_idx:]
    out = "\n".join(out_lines) + "\n"

    if out != content:
        with open(SITEMAP_PATH, "w") as f:
            f.write(out)
        return True
    return False


def update_llms(titles):
    with open(LLMS_PATH, "r") as f:
        content = f.read()
    out = content

    titles_line = f"- {SITE}/titles/ — title-by-title parents guides to swearing and language, from our own subtitle analysis\n"
    if f"{SITE}/titles/ " not in out:
        # insert after the stremio-profanity-filter.html line in the ## Pages section, else at the end
        anchor = f"- {SITE}/stremio-profanity-filter.html — muting swearing in Stremio, step-by-step\n"
        if anchor in out:
            out = out.replace(anchor, anchor + titles_line, 1)
        else:
            out = out.rstrip("\n") + "\n\n" + titles_line

    method_line = (
        f"- {SITE}/titles/{METHODOLOGY_SLUG}/ — how we count swear words: automated analysis of English "
        f"subtitles, the categories, and why our numbers can differ from other guides\n"
    )
    if f"{SITE}/titles/{METHODOLOGY_SLUG}/" not in out and titles_line in out:
        out = out.replace(titles_line, titles_line + method_line, 1)

    if out == content:
        return False
    with open(LLMS_PATH, "w") as f:
        f.write(out)
    return True


def main():
    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    # --refresh <ratings-export.json>: update each title's analysis and the all-films
    # comparison data from the export. --benchmark is the older name for the same thing.
    flag = next((a for a in ("--refresh", "--benchmark") if a in sys.argv), None)
    if flag:
        with open(sys.argv[sys.argv.index(flag) + 1], "r") as f:
            export = json.load(f)
        updated, held = refresh_titles(data["titles"], export, "--accept-changes" in sys.argv)
        data["benchmark"] = build_benchmark(export)
        with open(DATA_PATH, "w") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False))
        for line in updated:
            print(f"updated  {line}")
        for line in held:
            if line.startswith("REJECTED"):
                print(f"{line}  (malformed in the export; not applied)")
            else:
                print(f"HELD     {line}  (check it, then rerun with --accept-changes)")

    titles = data["titles"]
    check_titles(titles)
    category_labels = data["categoryLabels"]
    benchmark = data.get("benchmark")
    by_id = {t["videoId"]: t for t in titles}

    titles_dir = os.path.join(ROOT, "titles")
    changed_pages = 0
    for t in titles:
        page_dir = os.path.join(titles_dir, t["slug"])
        os.makedirs(page_dir, exist_ok=True)
        page_path = os.path.join(page_dir, "index.html")
        html = title_page_html(t, by_id, category_labels, benchmark)
        if not os.path.exists(page_path) or open(page_path).read() != html:
            with open(page_path, "w") as f:
                f.write(html)
            changed_pages += 1

    index_path = os.path.join(titles_dir, "index.html")
    index_html = index_page_html(titles, category_labels)
    if not os.path.exists(index_path) or open(index_path).read() != index_html:
        with open(index_path, "w") as f:
            f.write(index_html)
        changed_pages += 1

    method_dir = os.path.join(titles_dir, METHODOLOGY_SLUG)
    os.makedirs(method_dir, exist_ok=True)
    method_path = os.path.join(method_dir, "index.html")
    method_html = methodology_page_html(titles, category_labels)
    if not os.path.exists(method_path) or open(method_path).read() != method_html:
        with open(method_path, "w") as f:
            f.write(method_html)
        changed_pages += 1

    sitemap_changed = update_sitemap(titles)
    llms_changed = update_llms(titles)

    print(f"generated {len(titles)} title pages + index ({changed_pages} files changed this run)")
    print(f"sitemap.xml changed: {sitemap_changed}")
    print(f"llms.txt changed: {llms_changed}")


if __name__ == "__main__":
    main()
