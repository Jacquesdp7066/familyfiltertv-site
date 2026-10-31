#!/usr/bin/env python3
"""Fails if retired free-trial wording is back in public copy (issue #611).

New message: "Your first week is free, no card needed." / "Got a code from someone? You get 30 days free instead."
Scans every public file, including titles/ (generated film pages), except docs/, .git and
admin.html (noindex internal dashboard whose data fields are named "trial").
  python3 tools/check_copy.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD = re.compile(r"free trial|14[- ]day|usual 14|14 days|\btrials?\b", re.I)
SKIP_DIRS = {".git", "docs", "assets", "app", "node_modules", "__pycache__"}
SKIP_FILES = {"admin.html", "check_copy.py", "sitemap.xml"}
EXT = (".html", ".txt", ".js", ".md", ".py", ".json", ".css")

hits = []
for d, dirs, files in os.walk(ROOT):
    dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
    for f in files:
        if f in SKIP_FILES or not f.endswith(EXT):
            continue
        p = os.path.join(d, f)
        for n, line in enumerate(open(p, encoding="utf-8", errors="ignore"), 1):
            m = BAD.search(line)
            if m:
                hits.append(f"{os.path.relpath(p, ROOT)}:{n}: {m.group(0)}")
print("\n".join(hits) if hits else "copy OK: no 14-day / usual 14 / free trial wording")
sys.exit(1 if hits else 0)
