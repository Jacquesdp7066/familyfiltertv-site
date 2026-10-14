#!/usr/bin/env python3
"""Internal links: find pages that mention a keyword but never link to the page we want ranking for it,
and (with --apply) link the FIRST plain-text mention inside a <p> or <li>.

  python3 tools/internal_links.py          audit: print the gaps
  python3 tools/internal_links.py --apply  apply the EDITS list below

From Matt Diamante's reel (14 Oct 2026): search site:domain "keyword", open three pages that use it,
link the keyword to the page you want to rank. Three or so links per target, not every mention.
Generated pages under titles/ are left alone (change tools/build_titles.py instead).
"""
import glob, html, re, sys

TARGETS = {  # page -> keywords it should rank for
    "mute-swearing-on-tv.html": ["mute swearing", "mutes swearing", "mute swear words"],
    "android-tv-profanity-filter.html": ["profanity filter for android tv", "android tv profanity filter"],
    "does-netflix-have-a-profanity-filter.html": ["netflix profanity filter", "profanity filter on netflix"],
    "google-tv-profanity-filter.html": ["google tv"],
    "stremio-profanity-filter.html": ["stremio"],
    "windows-profanity-filter.html": ["on windows"],
    "family-movie-night-without-swearing.html": ["family movie night"],
    "movie-filtering-services-compared.html": ["vidangel", "clearplay", "tvguardian"],
    "parental-controls-vs-profanity-filter.html": ["parental controls"],
    "which-tvs.html": ["which tvs", "supported tvs"],
}
# (page, keyword, target): link the first plain mention of keyword on page to target.
EDITS = [
    ("stremio.html", "Stremio", "stremio-profanity-filter.html"),
    ("support.html", "Stremio", "stremio-profanity-filter.html"),
    ("parental-controls-vs-profanity-filter.html", "Stremio", "stremio-profanity-filter.html"),
    ("which-tvs.html", "Google TV", "google-tv-profanity-filter.html"),
    ("install-android-tv.html", "Google TV", "google-tv-profanity-filter.html"),
    ("tvguardian-alternative.html", "Google TV", "google-tv-profanity-filter.html"),
    ("does-netflix-have-a-profanity-filter.html", "mute swearing", "mute-swearing-on-tv.html"),
    ("stremio-profanity-filter.html", "mute swearing", "mute-swearing-on-tv.html"),
    ("setup.html", "mute swearing", "mute-swearing-on-tv.html"),
    ("parental-controls-vs-profanity-filter.html", "mutes swearing", "mute-swearing-on-tv.html"),
    ("facts.html", "profanity filter for Android TV", "android-tv-profanity-filter.html"),
    ("profanity-filter-android-tv.html", "Profanity filter for Android TV", "android-tv-profanity-filter.html"),
    ("movie-filtering-services-compared.html", "on Windows", "windows-profanity-filter.html"),
]
SKIP = ("google", "tiktok", "admin.html", "link.html", "titles/")


def body_text(s):
    b = re.split(r"<body[^>]*>", s, 1)[-1]
    b = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", "", b, flags=re.S | re.I)
    links = set(re.findall(r'href="([^"#?]+)', b))
    b = re.sub(r"<a [^>]*>.*?</a>", "", b, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", b)).lower(), links


def audit():
    pages = [p for p in glob.glob("*.html") if not p.startswith(SKIP)]
    n = 0
    for p in sorted(pages):
        text, links = body_text(open(p, encoding="utf-8").read())
        for t, kws in TARGETS.items():
            if p == t or any(l.endswith(t) for l in links):
                continue
            for k in kws:
                if k in text:
                    print(f"{p:50} mentions {k!r:36} x{text.count(k):<3} no link to {t}")
                    n += 1
                    break
    print(f"{n} gaps")


def apply_one(page, kw, target):
    s = open(page, encoding="utf-8").read()
    if re.search(r'href="' + re.escape(target) + '"', s):
        return "already linked"
    start = re.search(r"<body[^>]*>", s).end()
    # walk <p>/<li> elements in the body; link the first text node (not inside <a>) holding kw
    for m in re.finditer(r"<(p|li)\b[^>]*>(.*?)</\1>", s[start:], flags=re.S | re.I):
        inner = m.group(2)
        if "<a " in inner.lower() and re.search(re.escape(kw), re.sub(r"<a [^>]*>.*?</a>", "", inner, flags=re.S)) is None:
            continue
        # split into tags and text; find kw in a text segment that is not inside an <a>
        depth, out, done = 0, [], False
        for part in re.split(r"(<[^>]+>)", inner):
            if part.startswith("<"):
                if re.match(r"<a\b", part, re.I): depth += 1
                elif re.match(r"</a\b", part, re.I): depth -= 1
                out.append(part); continue
            if not done and depth == 0 and kw.lower() in part.lower():
                i = part.lower().index(kw.lower())
                part = part[:i] + f'<a href="{target}">' + part[i:i + len(kw)] + "</a>" + part[i + len(kw):]
                done = True
            out.append(part)
        if done:
            a, b = start + m.start(2), start + m.end(2)
            open(page, "w", encoding="utf-8").write(s[:a] + "".join(out) + s[b:])
            return "linked"
    return "keyword not found in a <p>/<li>"


if __name__ == "__main__":
    if "--apply" in sys.argv:
        for page, kw, target in EDITS:
            print(f"{page:50} {kw!r:36} -> {target}: {apply_one(page, kw, target)}")
    else:
        audit()
