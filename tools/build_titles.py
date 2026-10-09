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
import sys
import xml.sax.saxutils as sax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "titles", "data.json")
SITEMAP_PATH = os.path.join(ROOT, "sitemap.xml")
LLMS_PATH = os.path.join(ROOT, "llms.txt")
SITE = "https://familyfiltertv.com"

# Date the page template last changed. Sitemap lastmod is the later of this and a
# title's analysis date, so a wording change gets recrawled.
TEMPLATE_UPDATED = "2026-10-09"

CATEGORY_ORDER = [
    "strong_profanity", "mild_profanity", "religious", "crude",
    "sexual_explicit", "suggestive", "slurs",
]


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
        f'      <a href="{up}titles/">Titles</a>',
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
    """Flagged-word totals for every usable film in the subtitle-analysis export."""
    totals = sorted(sum(e["counts"].values()) for e in export if isinstance(e, dict) and usable(e))
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


def timeline_section(t):
    """When the language happens: first flagged word, first strong word, heaviest stretch."""
    timeline = t.get("timeline")
    if not timeline or not t["totalFlagged"] or not sum(timeline["words"]):
        return ""
    words, strong, bucket_ms = timeline["words"], timeline["strongProfanity"], timeline["bucketMs"]
    name = esc(t["title"])
    size = bucket_ms // 60000

    def first(slots):
        return next((i for i, n in enumerate(slots) if n), None)

    def when(i):
        return f"in the first {size} minutes" if i == 0 else f"between minute {minutes_label(i, bucket_ms).replace(' to ', ' and ')}"

    lines = [f"The first flagged word in {name} comes {when(first(words))}."]
    first_strong = first(strong)
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
        f"          <tr><td>{esc(minutes_label(i, bucket_ms))}</td><td>{esc(words[i])}</td><td>{esc(strong[i])}</td></tr>"
        for i in range(len(words))
    )
    return f'''  <section aria-labelledby="timeline-heading">
    <h2 id="timeline-heading">When the swearing happens in {name}</h2>
{body}
    <div class="table-scroll">
      <table>
        <thead><tr><th>Minutes</th><th>Flagged words</th><th>Strong profanity</th></tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
    </div>
  </section>'''


def comparison_section(t, benchmark):
    """How this film's language compares with every film we have analysed."""
    if not benchmark:
        return ""
    totals = benchmark["totals"]
    n = benchmark["filmCount"]
    total = t["totalFlagged"]
    name = esc(t["title"])
    lines = []

    if total == 0:
        clean = bisect.bisect_right(totals, 0)
        lines.append(
            f"{name} is one of {clean} films with no flagged language, out of the {n} "
            f"films we have analysed."
        )
    else:
        below = 100 * bisect.bisect_left(totals, total) / n
        above = 100 * (n - bisect.bisect_right(totals, total)) / n
        if below >= above:
            lines.append(
                f"{name} has more flagged language than {min(99, round(below))}% of the {n} "
                f"films we have analysed."
            )
        else:
            lines.append(
                f"{name} has less flagged language than {min(99, round(above))}% of the {n} "
                f"films we have analysed."
            )
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

    body = "\n".join(f"    <p>{ln}</p>" for ln in lines)
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
        f'      <li>{esc(name.capitalize())} filter: {esc(muted)} of {esc(cue_count)} subtitle lines muted</li>'
        for name, muted in profiles.items()
    )

    return f'''  <section class="panel" aria-labelledby="ffa-heading">
    <h2 id="ffa-heading">How much swearing is in {esc(t["title"])}?</h2>
    <p>{esc(language_summary(t, category_labels))}</p>
    <p><strong>Language level:</strong> {esc(t["labelText"])}</p>
    <p><strong>Total flagged words:</strong> {esc(t["totalFlagged"])}</p>
{cat_block}
    <h3>Lines muted per filter profile</h3>
    <ul>
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


def title_page_html(t, by_id, category_labels, benchmark=None):
    slug = t["slug"]
    name = t["title"]
    year = t["year"]
    canonical = f"{SITE}/titles/{slug}/"
    page_title = f"{name} ({year}) Parents Guide: Swearing and Language | Family Filter TV"
    total = t["totalFlagged"]
    if total:
        top = ", ".join(
            f"{val} {label.lower()}"
            for label, val in sorted(category_rows(t["counts"], category_labels), key=lambda r: -r[1])[:2]
        )
        found = f"{total} flagged {'word' if total == 1 else 'words'} in the subtitles ({top})"
    else:
        found = "no flagged swearing found in the subtitles"
    description = (
        f"{name} ({year}) parents guide to swearing and language: {found}. "
        f"Full count by category."
    )

    genres_jsonld = t["genres"]
    runtime_iso = runtime_to_iso(t["runtime"])

    jsonld_work = {
        "@context": "https://schema.org",
        "@type": "Movie",
        "name": name,
        "datePublished": str(year),
        "genre": genres_jsonld,
        "sameAs": t["imdbUrl"],
    }
    if runtime_iso:
        jsonld_work["duration"] = runtime_iso

    jsonld_breadcrumb = breadcrumb_jsonld([
        ("Home", f"{SITE}/"),
        ("Titles", f"{SITE}/titles/"),
        (name, canonical),
    ])

    breadcrumb = breadcrumb_html(2, title=name)
    related = related_section(t, by_id, "../")
    detail = "\n\n".join(
        part for part in (timeline_section(t), comparison_section(t, benchmark)) if part
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&display=swap">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="../../style.css">
<script type="application/ld+json">
{jsonld(jsonld_work)}
</script>
<script type="application/ld+json">
{jsonld(jsonld_breadcrumb)}
</script>
</head>
<body>
{header("titles", 2)}

<main class="wrap">
  {breadcrumb}
  <h1 class="page-title">{esc(name)} ({year}) parents guide: swearing and language</h1>
  <p class="lead">{esc(t["intro"])}</p>
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

    rows = []
    for t in sorted(titles, key=lambda x: x["title"]):
        rows.append(
            f'      <li class="title-row" data-search="{esc(t["title"].lower())}">'
            f'<a href="{t["slug"]}/">{esc(t["title"])} ({t["year"]})</a> '
            f'<span class="muted">&mdash; {esc(t["labelText"])}, '
            f'{esc(t["totalFlagged"])} flagged {"word" if t["totalFlagged"] == 1 else "words"}</span></li>'
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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&display=swap">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="../style.css">
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

  <ul id="title-list" class="panel" style="list-style:none;padding:22px 24px;">
{chr(10).join(rows)}
  </ul>

  <p class="muted">This is a small, 20-title test set &mdash; not the full catalogue. See
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

    # last-known-good lastmod for the index = most recent analysis date in the cohort
    index_lastmod = max(TEMPLATE_UPDATED, max(t["computedAt"][:10] for t in titles))

    new_entries = [
        f'  <url><loc>{SITE}/titles/</loc><lastmod>{index_lastmod}</lastmod><priority>0.8</priority></url>'
    ]
    for t in sorted(titles, key=lambda x: x["slug"]):
        lastmod = max(TEMPLATE_UPDATED, t["computedAt"][:10])
        new_entries.append(
            f'  <url><loc>{SITE}/titles/{t["slug"]}/</loc><lastmod>{lastmod}</lastmod><priority>0.6</priority></url>'
        )

    # insert before closing </urlset>
    close_idx = next(i for i, ln in enumerate(kept) if "</urlset>" in ln)
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

    marker = f"{SITE}/titles/"
    if marker in content:
        return False

    line = f"- {SITE}/titles/ — title-by-title parents guides to swearing and language, from our own subtitle analysis\n"
    # insert after the stremio-profanity-filter.html line in the ## Pages section, else just before "## Not affiliated"
    anchor = f"- {SITE}/stremio-profanity-filter.html — muting swearing in Stremio, step-by-step\n"
    if anchor in content:
        out = content.replace(anchor, anchor + line, 1)
    else:
        out = content.rstrip("\n") + "\n\n" + line

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

    sitemap_changed = update_sitemap(titles)
    llms_changed = update_llms(titles)

    print(f"generated {len(titles)} title pages + index ({changed_pages} files changed this run)")
    print(f"sitemap.xml changed: {sitemap_changed}")
    print(f"llms.txt changed: {llms_changed}")


if __name__ == "__main__":
    main()
