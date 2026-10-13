#!/usr/bin/env python3
"""Sanity checks for the static site. Stdlib only. Exit 1 on any failure.

  - every HTML file parses
  - every JSON-LD block parses as JSON
  - every internal href/src resolves to a file in the repo
  - every sitemap URL maps to a file
  - no page lost JSON-LD types it had on the base ref (default origin/main)

  python3 tools/check_site.py [--base origin/main]
"""
import argparse
import json
import os
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
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
                fails.append(f"{rel}: lost JSON-LD types {sorted(lost)}")

    urls = [e.text.strip() for e in ET.parse(os.path.join(ROOT, "sitemap.xml")).getroot().iter()
            if e.tag.endswith("}loc") and e.text]
    for u in urls:
        t = resolve(u, os.path.join(ROOT, "sitemap.xml"))
        if t is None or not os.path.isfile(t):
            fails.append(f"sitemap.xml: {u} does not map to a file")

    print(f"{len(htmls)} HTML files, {n_ld} JSON-LD blocks, {n_links} internal links, {len(urls)} sitemap URLs checked")
    for f in fails:
        print("FAIL", f)
    print("OK" if not fails else f"{len(fails)} problem(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
