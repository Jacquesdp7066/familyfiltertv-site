#!/usr/bin/env python3
"""Static SEO audit of every HTML page in the repo. Stdlib only.

  python3 tools/seo_audit.py            # table + findings, exit 0
  python3 tools/seo_audit.py --strict   # exit 1 on any finding (for CI / local gate)

Checks per page: <title>, meta description, canonical (must be https://familyfiltertv.com/<path>),
robots meta, exactly one <h1>, heading order, Open Graph + Twitter basics, images without alt/width/height,
JSON-LD types, sitemap membership, inbound internal links (orphans), visible word count.
"""
import argparse, json, os, re, sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urldefrag, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "https://familyfiltertv.com"
# Pages that are deliberately not indexable / not part of the public site
NOINDEX_OK = {"admin.html", "link.html", "join.html", "creator.html", "tiktok-callback.html", "tiktok-publisher.html"}
# Redirect stubs: old URLs kept alive with canonical + meta refresh to the real page
STUBS = {"android-tv-profanity-filter.html"}
SKIP = {"googlee3a0c7bd81717f36.html"}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""; self.meta = {}; self.canonical = None; self.h = []; self.imgs = []
        self.ld = []; self.links = []; self.words = 0
        self._t = self._ld = self._body = False; self._h = None; self._buf = []; self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title" and not self.title and not self._body: self._t = True
        elif tag == "body": self._body = True
        elif tag == "meta":
            k = a.get("name") or a.get("property")
            if k: self.meta[k.lower()] = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical": self.canonical = a.get("href")
        elif tag in ("h1", "h2", "h3", "h4"): self._h = tag; self._buf = []
        elif tag == "img": self.imgs.append(a)
        elif tag == "a" and a.get("href"): self.links.append(a["href"])
        elif tag == "script":
            if a.get("type") == "application/ld+json": self._ld = True; self._buf = []
            self._skip += 1
        elif tag == "style": self._skip += 1

    def handle_endtag(self, tag):
        if tag == "title": self._t = False
        elif tag == self._h: self.h.append((tag, " ".join("".join(self._buf).split()))); self._h = None
        elif tag == "script":
            if self._ld: self.ld.append("".join(self._buf)); self._ld = False
            self._skip = max(0, self._skip - 1)
        elif tag == "style": self._skip = max(0, self._skip - 1)

    def handle_data(self, d):
        if self._t: self.title += d
        if self._ld or self._h: self._buf.append(d)
        if not self._skip: self.words += len(d.split())


def types(blocks):
    out = set()
    def w(o):
        if isinstance(o, dict):
            t = o.get("@type")
            out.update([t] if isinstance(t, str) else (t or []))
            for v in o.values(): w(v)
        elif isinstance(o, list):
            for v in o: w(v)
    for b in blocks:
        try: w(json.loads(b))
        except ValueError: pass
    return out


def expected_canonicals(rel):
    """Both the .html form and the extensionless form are served by GitHub Pages; we canonicalise to the form used in the sitemap."""
    if rel == "index.html": return {HOST + "/"}
    if rel.endswith("/index.html"): return {HOST + "/" + rel[:-10]}
    return {HOST + "/" + rel, HOST + "/" + rel[:-5]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--strict", action="store_true"); ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    pages = {}
    for d, ds, fs in os.walk(ROOT):
        ds[:] = [x for x in ds if x not in (".git", "node_modules", "docs")]
        for f in fs:
            if f.endswith(".html"):
                rel = os.path.relpath(os.path.join(d, f), ROOT)
                if rel in SKIP: continue
                p = P(); p.feed(open(os.path.join(d, f), encoding="utf-8").read()); pages[rel] = p
    sm = ET.parse(os.path.join(ROOT, "sitemap.xml"))
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    smurls = {e.text.strip() for e in sm.getroot().findall(".//s:loc", ns)}
    inbound = {r: 0 for r in pages}
    def url_to_rel(u):
        path = urlparse(u).path
        if path in ("", "/"): return "index.html"
        c = path.lstrip("/")
        for cand in (c, c + ".html", c.rstrip("/") + "/index.html"):
            if cand in pages: return cand
    for rel, p in pages.items():
        for h in p.links:
            h, _ = urldefrag(h)
            u = urlparse(h)
            if u.scheme in ("mailto", "tel", "javascript", "stremio") or not h: continue
            if u.netloc and u.netloc != "familyfiltertv.com": continue
            if not u.netloc and not u.path.startswith("/"):
                tgt = os.path.normpath(os.path.join(os.path.dirname(rel), u.path)); full = "/" + tgt
            else: full = u.path
            t = url_to_rel(full)
            if t and t != rel: inbound[t] += 1
    findings, rows = [], []
    for rel in sorted(pages):
        p = pages[rel]; f = []
        noindex = "noindex" in p.meta.get("robots", "").lower()
        if rel in STUBS:
            rows.append((rel, len(p.title.strip()), 0, len([1 for tg, _ in p.h if tg == "h1"]), p.words, inbound[rel], [], "redirect-stub"))
            continue
        title = p.title.strip(); desc = p.meta.get("description", "").strip()
        if not title: f.append("no <title>")
        elif len(title) > 65: f.append(f"title {len(title)} chars (>65)")
        if not noindex:
            if not desc: f.append("no meta description")
            elif len(desc) > 165: f.append(f"description {len(desc)} chars (>165)")
            elif len(desc) < 70: f.append(f"description short ({len(desc)})")
            if not p.canonical: f.append("no canonical")
            elif p.canonical not in expected_canonicals(rel): f.append(f"canonical mismatch: {p.canonical}")
            if rel not in NOINDEX_OK and not any(u in smurls for u in expected_canonicals(rel)): f.append("indexable but not in sitemap")
            for k in ("og:title", "og:description", "og:image", "og:url"):
                if not p.meta.get(k): f.append(f"missing {k}")
            if not p.meta.get("twitter:card"): f.append("missing twitter:card")
            if inbound[rel] == 0 and rel != "index.html": f.append("orphan (no inbound internal links)")
            if p.words < 250 and not rel.startswith("titles/"): f.append(f"thin ({p.words} words)")
        h1 = [t for tag, t in p.h if tag == "h1"]
        if len(h1) != 1 and not noindex: f.append(f"{len(h1)} <h1>")
        lv = [int(tag[1]) for tag, _ in p.h]
        if any(b - a > 1 for a, b in zip(lv, lv[1:])): f.append("heading level skipped")
        noalt = sum(1 for i in p.imgs if i.get("alt") is None)
        nodim = sum(1 for i in p.imgs if not (i.get("width") and i.get("height")))
        if noalt: f.append(f"{noalt} img without alt")
        if nodim: f.append(f"{nodim}/{len(p.imgs)} img without width+height")
        for u in smurls:
            pass
        rows.append((rel, len(title), len(desc), len(h1), p.words, inbound[rel], sorted(types(p.ld)), "noindex" if noindex else ""))
        for x in f: findings.append((rel, x))
    stray = [u for u in smurls if not url_to_rel(u)]
    for u in stray: findings.append(("sitemap.xml", f"URL does not map to a file: {u}"))
    for u in smurls:
        r = url_to_rel(u)
        if r and "noindex" in pages[r].meta.get("robots", "").lower(): findings.append(("sitemap.xml", f"noindex page in sitemap: {u}"))
    if args.json:
        print(json.dumps({"pages": rows, "findings": findings, "sitemap": len(smurls)}, indent=1)); return
    print(f"{len(pages)} pages, {len(smurls)} sitemap URLs")
    print(f"{'page':58} ttl dsc h1 words inb  ld-types")
    for r in rows: print(f"{r[0][:58]:58} {r[1]:3} {r[2]:3} {r[3]:2} {r[4]:5} {r[5]:3}  {','.join(r[6])} {r[7]}")
    print(f"\n{len(findings)} findings")
    for rel, x in findings: print(f"  {rel}: {x}")
    sys.exit(1 if (args.strict and findings) else 0)


main()
