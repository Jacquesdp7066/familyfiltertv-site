#!/usr/bin/env python3
"""Generate the /titles/ SEO index pages for Family Filter TV (issue #269).

Reads titles/data.json (20-title test cohort, built from our own subtitle
analysis export and Cinemeta metadata lookups) and emits:

  - titles/<slug>/index.html   for each title
  - titles/index.html          browse/search index page
  - sitemap.xml                updated with /titles/ + the 20 detail pages
  - llms.txt                   updated with a /titles/ entry

Stdlib only. Re-running this script with unchanged data.json must produce
no further changes (idempotent) — see tools/README or docs/SEO_TITLE_INDEX_TEST.md
in the app repo for the verification protocol.
"""
import json
import os
import re
import xml.sax.saxutils as sax

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "titles", "data.json")
SITEMAP_PATH = os.path.join(ROOT, "sitemap.xml")
LLMS_PATH = os.path.join(ROOT, "llms.txt")
SITE = "https://familyfiltertv.com"

CATEGORY_ORDER = [
    "strong_profanity", "mild_profanity", "religious", "crude",
    "sexual_explicit", "suggestive", "slurs",
]


def esc(s):
    return sax.escape(str(s))


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
        item("titles/index.html", "Titles", "titles"),
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
        f'      <a href="{up}titles/index.html">Titles</a>',
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
        parts.append(f'<a href="{up}titles/index.html">Titles</a>')
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


def category_rows(counts, category_labels):
    rows = []
    for key in CATEGORY_ORDER:
        if key in counts:
            rows.append((category_labels.get(key, key), counts[key]))
    for key, val in counts.items():
        if key not in CATEGORY_ORDER:
            rows.append((category_labels.get(key, key), val))
    return rows


def analysis_panel(t, category_labels):
    rows = category_rows(t["counts"], category_labels)
    last_analysed = t["computedAt"][:10]
    if rows:
        cat_html = "\n".join(
            f'      <li>{esc(label)}: {val}</li>' for label, val in rows
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
        f'      <li>{name.capitalize()} filter: {muted} of {cue_count} subtitle lines muted</li>'
        for name, muted in profiles.items()
    )

    return f'''  <section class="panel" aria-labelledby="ffa-heading">
    <h2 id="ffa-heading">Family Filter TV analysis</h2>
    <p><strong>Language level:</strong> {esc(t["labelText"])}</p>
    <p><strong>Total flagged lines:</strong> {t["totalFlagged"]}</p>
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


def title_page_html(t, by_id, category_labels):
    slug = t["slug"]
    name = t["title"]
    year = t["year"]
    canonical = f"{SITE}/titles/{slug}/"
    page_title = f"Is {name} Safe for Kids? Profanity & Family Viewing Guide | Family Filter TV"
    description = (
        f"Family Filter TV's own subtitle analysis of {name} ({year}): language level, "
        f"flagged word counts and how much gets muted per filter profile."
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
{json.dumps(jsonld_work, indent=2)}
</script>
<script type="application/ld+json">
{json.dumps(jsonld_breadcrumb, indent=2)}
</script>
</head>
<body>
{header("titles", 2)}

<main class="wrap">
  {breadcrumb}
  <h1 class="page-title">Is {esc(name)} suitable for family viewing?</h1>
  <p class="lead">{esc(t["intro"])}</p>

{analysis_panel(t, category_labels)}

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
    page_title = "Family Viewing Guides by Title | Family Filter TV"
    description = (
        "Browse Family Filter TV's title-by-title family viewing guides: language level and "
        "flagged word counts from our own subtitle analysis, for films parents search for."
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
            f'<span class="muted">&mdash; {esc(t["labelText"])}</span></li>'
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
{json.dumps(jsonld_breadcrumb, indent=2)}
</script>
</head>
<body>
{header("titles", 1)}

<main class="wrap">
  {breadcrumb}
  <h1 class="page-title">Family viewing guides by title</h1>
  <p class="lead">Language level and flagged-word data for specific films, from Family Filter
  TV's own subtitle analysis &mdash; not a competitor's ratings or a generic parental guide.</p>

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
    index_lastmod = max(t["computedAt"][:10] for t in titles)

    new_entries = [
        f'  <url><loc>{SITE}/titles/</loc><lastmod>{index_lastmod}</lastmod><priority>0.8</priority></url>'
    ]
    for t in sorted(titles, key=lambda x: x["slug"]):
        lastmod = t["computedAt"][:10]
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

    line = f"- {SITE}/titles/ — title-by-title family viewing guides, from our own subtitle analysis\n"
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

    titles = data["titles"]
    category_labels = data["categoryLabels"]
    by_id = {t["videoId"]: t for t in titles}

    titles_dir = os.path.join(ROOT, "titles")
    changed_pages = 0
    for t in titles:
        page_dir = os.path.join(titles_dir, t["slug"])
        os.makedirs(page_dir, exist_ok=True)
        page_path = os.path.join(page_dir, "index.html")
        html = title_page_html(t, by_id, category_labels)
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
