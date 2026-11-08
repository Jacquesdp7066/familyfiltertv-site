#!/usr/bin/env python3
"""Sanity checks for the static site. Stdlib only. Exit 1 on any failure.

  - every HTML file parses
  - every JSON-LD block parses as JSON
  - every internal href/src resolves to a file in the repo
  - every sitemap URL maps to a file
  - no page lost JSON-LD types it had on the base ref (default origin/main)

  python3 tools/check_site.py [--base origin/main] [--allow-lost Offer]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote, urldefrag, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_HOST = "familyfiltertv.com"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ld, self.errors = [], [], []
        self.stack, self._in_ld, self._buf = [], False, []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("href", "src"):
            if a.get(k):
                self.links.append(a[k])
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld, self._buf = True, []
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "script" and self._in_ld:
            self.ld.append("".join(self._buf))
            self._in_ld = False
        if tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"unclosed <{self.stack.pop()}>")
            self.stack.pop()
        else:
            self.errors.append(f"stray </{tag}>")

    def handle_data(self, data):
        if self._in_ld:
            self._buf.append(data)

    def close(self):
        super().close()
        self.errors += [f"unclosed <{t}>" for t in self.stack if t not in ("html", "body")]


def parse(text):
    p = Page()
    p.feed(text)
    p.close()
    return p


def ld_types(blocks):
    types = set()

    def walk(o):
        if isinstance(o, dict):
            t = o.get("@type")
            if isinstance(t, str):
                types.add(t)
            elif isinstance(t, list):
                types.update(t)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for b in blocks:
        try:
            walk(json.loads(b))
        except ValueError:
            pass
    return types


def resolve(href, page_path):
    """Return a repo path for an internal link, or None if external / not a file link."""
    href, _ = urldefrag(href.strip())
    if not href:
        return None
    u = urlparse(href)
    if u.scheme in ("mailto", "tel", "stremio", "javascript", "data"):
        return None
    if u.scheme in ("http", "https"):
        if u.netloc != SITE_HOST:
            return None
        rel = u.path.lstrip("/")
    elif u.netloc:
        return None
    elif u.path.startswith("/"):
        rel = u.path.lstrip("/")
    else:
        rel = os.path.normpath(os.path.join(os.path.dirname(page_path), u.path))
        rel = os.path.relpath(os.path.join(ROOT, rel), ROOT) if not os.path.isabs(rel) else rel
    rel = unquote(rel)
    path = os.path.join(ROOT, rel)
    if rel == "" or rel.endswith("/") or os.path.isdir(path):
        path = os.path.join(path, "index.html")
    return path


def stale_film_stats():
    """Hand-written pages that quote the film analysis (count, median, most common words ...)
    must match titles/data.json; tools/sync_stats.py rewrites them and build_titles.py runs it."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import sync_stats
    return [f"{name} is out of step with titles/data.json (run tools/build_titles.py)" for name in sync_stats.run(write=False)]


def title_page_problems(sitemap_urls):
    """Film pages (titles/*/) and the pages under them need a TL;DR under the H1, links in from at
    least two other film pages, a unique title, H1 and description, a
    canonical link equal to their own URL, a sitemap entry, no age or kid-safe wording, no outbound
    follow-links to ClearPlay or VidAngel, and no poster or still images."""
    banned = re.compile(r"kid-safe|family-friendly|for (?:kids|children)|age-appropriate|child-friendly", re.I)
    seen = {"title": {}, "h1": {}, "description": {}}
    problems = []
    inbound, film_slugs = {}, []
    tdir = os.path.join(ROOT, "titles")
    for slug in sorted(os.listdir(tdir)):
        path = os.path.join(tdir, slug, "index.html")
        if not os.path.isfile(path):
            continue
        rel = f"titles/{slug}/index.html"
        text = open(path, encoding="utf-8").read()
        if slug != "methodology":
            film_slugs.append(slug)
        got = {
            "title": re.search(r"<title>(.*?)</title>", text, re.S),
            "h1": re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S),
            "description": re.search(r'<meta name="description" content="([^"]*)"', text),
        }
        for k, m in got.items():
            if not m:
                problems.append(f"{rel}: no {k}")
            elif m.group(1) in seen[k]:
                problems.append(f"{rel}: {k} duplicates {seen[k][m.group(1)]}")
            else:
                seen[k][m.group(1)] = rel
        url = f"https://{SITE_HOST}/titles/{slug}/"
        if f'<link rel="canonical" href="{url}">' not in text:
            problems.append(f"{rel}: canonical link is missing or not {url}")
        if url not in sitemap_urls:
            problems.append(f"{rel}: not in sitemap.xml")
        visible = re.sub(r"<script.*?</script>|<style.*?</style>", "", text, flags=re.S)
        if m := banned.search(visible):
            problems.append(f"{rel}: wording not allowed: {m.group(0)!r}")
        if re.search(r"<img[^>]+(?:poster|still|metahub)", text, re.I):
            problems.append(f"{rel}: poster or still image")
        if slug != "methodology" and not re.search(r'</h1>\s*<p class="lead tldr"><strong>TL;DR:</strong> [^<]{40,}</p>', text):
            problems.append(f"{rel}: no TL;DR directly under the H1")
        for other in re.findall(r'href="\.\./([a-z0-9-]+)/"', text):
            if other != slug:
                inbound.setdefault(other, set()).add(slug)
        if "film studio" not in text:
            problems.append(f"{rel}: missing the not-affiliated-with-studios line")
        for tag in re.findall(r"<a [^>]*href=\"https?://[^\"]*(?:clearplay|vidangel)\.com[^>]*>", text):
            if "nofollow" not in tag:
                problems.append(f"{rel}: ClearPlay/VidAngel link without rel=nofollow")
    for slug in sorted(film_slugs):
        if len(inbound.get(slug, ())) < 2:
            problems.append(f"titles/{slug}/index.html: linked from {len(inbound.get(slug, ()))} other film pages, needs 2")
    for name in ("how-many-swear-words-are-there.html", "swearing-in-movies.html"):
        if not re.search(r'</h1>\s*<p class="lead tldr"><strong>TL;DR:</strong>', open(os.path.join(ROOT, name), encoding="utf-8").read()):
            problems.append(f"{name}: no TL;DR directly under the H1")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--allow-lost", action="append", default=[], metavar="TYPE", help="JSON-LD type removed on purpose (e.g. Offer)")
    args = ap.parse_args()
    fails = []

    htmls = []
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules")]
        htmls += [os.path.join(d, f) for f in files if f.endswith(".html")]
    htmls.sort()

    n_ld = n_links = 0
    for path in htmls:
        rel = os.path.relpath(path, ROOT)
        text = open(path, encoding="utf-8").read()
        p = parse(text)
        for e in p.errors:
            fails.append(f"{rel}: HTML: {e}")
        for i, b in enumerate(p.ld, 1):
            n_ld += 1
            try:
                json.loads(b)
            except ValueError as e:
                fails.append(f"{rel}: JSON-LD block {i} is not valid JSON: {e}")
        for href in p.links:
            target = resolve(href, path)
            if target is None:
                continue
            n_links += 1
            if not os.path.isfile(target):
                fails.append(f"{rel}: broken link {href!r}")
        # JSON-LD types must not be lost versus the base ref
        try:
            old = subprocess.run(["git", "show", f"{args.base}:{rel}"], cwd=ROOT, capture_output=True,
                                 text=True, check=True).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            old = None
        if old is not None:
            lost = ld_types(parse(old).ld) - ld_types(p.ld)
            if lost:
                lost = {x for x in lost if x not in args.allow_lost}
                if lost:
                    fails.append(f"{rel}: lost JSON-LD types {sorted(lost)}")

    urls = [e.text.strip() for e in ET.parse(os.path.join(ROOT, "sitemap.xml")).getroot().iter()
            if e.tag.endswith("}loc") and e.text]
    for u in urls:
        t = resolve(u, os.path.join(ROOT, "sitemap.xml"))
        if t is None or not os.path.isfile(t):
            fails.append(f"sitemap.xml: {u} does not map to a file")

    fails += [f"stale film stat: {x}" for x in stale_film_stats()]
    fails += [f"film pages: {x}" for x in title_page_problems(set(urls))]

    print(f"{len(htmls)} HTML files, {n_ld} JSON-LD blocks, {n_links} internal links, {len(urls)} sitemap URLs checked")
    for f in fails:
        print("FAIL", f)
    print("OK" if not fails else f"{len(fails)} problem(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
