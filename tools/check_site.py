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
import statistics
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


# Hand-written pages and text files that quote the size and spread of the film analysis. The
# numbers must follow titles/data.json (benchmark, refreshed weekly); a line that carries its own
# date ("... by 12 October 2026") is a dated snapshot and is left alone, and so is the
# movies-with-no-swearing.html snapshot page.
COUNT_FILES = ("swearing-in-movies.html", "index.html", "guides.html", "llms.txt", "llms-full.txt")
FILM_COUNT = re.compile(r"\b(\d,\d{3}) films\b|\bof (?:the )?(\d,\d{3})\b")
DATED = re.compile(r"\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) 20\d\d\b")


def stale_film_stats():
    """Problems where a quoted film count, median or heaviest film differs from data.json."""
    with open(os.path.join(ROOT, "titles", "data.json"), encoding="utf-8") as f:
        totals = json.load(f)["benchmark"]["totals"]
    want = {"film count": f"{len(totals):,}", "median": f"{statistics.median(totals):g}", "heaviest": str(max(totals))}
    problems = []
    for name in COUNT_FILES:
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if DATED.search(line):
                    continue
                for m in FILM_COUNT.finditer(line):
                    found = m.group(1) or m.group(2)
                    if found != want["film count"]:
                        problems.append(f"{name}:{n}: says {found} films, titles/data.json has {want['film count']}")
                for m in re.finditer(r"half (?:the films )?have (\d+) or fewer", line):
                    if m.group(1) != want["median"]:
                        problems.append(f"{name}:{n}: says median {m.group(1)}, titles/data.json has {want['median']}")
                for m in re.finditer(r"heaviest has (\d+)", line):
                    if m.group(1) != want["heaviest"]:
                        problems.append(f"{name}:{n}: says heaviest has {m.group(1)}, titles/data.json has {want['heaviest']}")
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

    print(f"{len(htmls)} HTML files, {n_ld} JSON-LD blocks, {n_links} internal links, {len(urls)} sitemap URLs checked")
    for f in fails:
        print("FAIL", f)
    print("OK" if not fails else f"{len(fails)} problem(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
