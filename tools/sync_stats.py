#!/usr/bin/env python3
"""Keep the film-analysis numbers quoted in hand-written pages in step with titles/data.json.

The generated film pages read the benchmark straight from data.json. A few hand-written pages
(and the llms text files) quote the same figures: how many films were analysed, the median,
how many have none, which words are the most common. Each quoted figure is found by a pattern
below and rewritten from the benchmark, so a weekly refresh cannot leave them stale.

  tools/sync_stats.py            rewrite the files (build_titles.py does this on every build)
  tools/sync_stats.py --check    list what differs, change nothing (check_site.py does this)

A line that carries its own date ("... counted to 12 October 2026") is a dated snapshot and is
left alone by the count rule, and movies-with-no-swearing.html is not touched at all. A pattern that
no longer matches anything raises an error instead of silently doing nothing. Stdlib only.
"""
import json
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "titles", "data.json")

FILM_FILES = ("swearing-in-movies.html", "index.html", "guides.html", "llms.txt", "llms-full.txt")
WORD_FILES = ("how-many-swear-words-are-there.html", "llms-full.txt", "llms.txt")
DATE = r"\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) 20\d\d"
DATED = re.compile(DATE)
MONTHS = ("January February March April May June July August September October November December").split()
NUMBER_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def long_date(iso):
    y, m, d = iso.split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def stats(benchmark):
    totals = benchmark["totals"]
    n = len(totals)
    words = benchmark["words"]
    ge100 = sum(1 for x in totals if x >= 100)
    one_in = round(n / ge100)
    if one_in not in NUMBER_WORDS:
        raise SystemExit(f"sync_stats: 100-or-more share ({ge100}/{n}) is no longer 'one in N' for N 2-10; reword the pages")
    return {
        "films": f"{n:,}",
        "median": f"{statistics.median(totals):g}",
        "mean": f"{statistics.mean(totals):.0f}",
        "zero": str(sum(1 for x in totals if x == 0)),
        "zero_pct": f"{round(100 * sum(1 for x in totals if x == 0) / n)}",
        "le5": str(sum(1 for x in totals if x <= 5)),
        "ge100": str(ge100),
        "one_in": NUMBER_WORDS[one_in],
        "ge200": str(sum(1 for x in totals if x >= 200)),
        "max": str(max(totals)),
        "asof": long_date(benchmark["asOf"]),
        "wfilms": f"{words['films']:,}",
        "wflagged": f"{words['flagged']:,}",
        "wforms": str(words["forms"]),
        **{f"top{k}": str(v) for k, v in words["top"].items()},
    }


# (files, regex with named groups, skip dated lines). Every named group is replaced by stats[group name
# with any trailing digit-suffix removed]; use a "__x" suffix to repeat a group name.
RULES = [
    (FILM_FILES, r"(?<![\d,])(?P<films>\d,\d{3}) films", True),
    (FILM_FILES, r"[Hh]alf (?:the films )?have (?P<median>\d+) or fewer", False),
    (FILM_FILES, r"at about (?P<mean>\d+), because a few", False),
    (FILM_FILES, r"(?P<zero>\d+) films, about (?P<zero_pct>\d+)%, have none at all\.</strong> (?P<le5>\d+) have five or fewer", False),
    (FILM_FILES, r"(?P<ge100>\d+) films, about one in (?P<one_in>\w+), have 100 or more\.</strong> (?P<ge200>\d+) have 200 or more, and the heaviest has (?P<max>\d+)\.", False),
    (FILM_FILES, r"(?P<zero_pct>\d+)% have none, and about one in (?P<one_in>\w+) has 100 or more", False),
    (FILM_FILES, r"the heaviest has (?P<max>\d+) flagged words of all kinds", False),
    (FILM_FILES, r"Film counts from our subtitle analysis, (?P<asof>" + DATE + ")", False),
    (WORD_FILES, r"the (?P<wfilms>[\d,]+) films (?:we analysed|whose English subtitles we analysed) on (?P<asof>" + DATE + ")", False),
    (WORD_FILES, r"On (?P<asof>" + DATE + r") we counted every flagged word in the English subtitles of (?P<wfilms>[\d,]+) films, (?P<wflagged>[\d,]+) flagged words in all\. Only (?P<wforms>\d+) different", False),
    (WORD_FILES, r"The (?P<wflagged>[\d,]+) flagged words, (?P<wforms>\d+) word forms and top-N shares come from the English subtitles of (?P<wfilms>[\d,]+) films on (?P<asof>" + DATE + ")", False),
    (WORD_FILES, r"top 5 forms make up (?P<top5>\d+)% of all flagged words, the top 10 make up (?P<top10>\d+)% and the top 20 make up (?P<top20>\d+)%", False),
    (WORD_FILES, r"<td>Top 1</td><td>(?P<top1>\d+)%</td></tr>\s*<tr><td>Top 5</td><td>(?P<top5>\d+)%</td></tr>\s*<tr><td>Top 10</td><td>(?P<top10>\d+)%</td></tr>\s*<tr><td>Top 20</td><td>(?P<top20>\d+)%</td></tr>\s*<tr><td>Top 50</td><td>(?P<top50>\d+)%</td>", False),
    (WORD_FILES, r"the 10 most common flagged forms make up (?P<top10>\d+)%", False),
    (WORD_FILES, r"ten word forms make up (?P<top10>\d+)% of", False),
]


def rewrite(text, pattern, skip_dated, values):
    """text with every named group of every match replaced; returns (new text, matches seen)."""
    rx = re.compile(pattern)
    out, pos, seen = [], 0, 0
    for m in rx.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if skip_dated and DATED.search(text[line_start:line_end if line_end != -1 else len(text)]):
            continue
        seen += 1
        spans = sorted((m.start(g), m.end(g), values[g]) for g in rx.groupindex)
        for a, b, v in spans:
            out.append(text[pos:a])
            out.append(v)
            pos = b
    out.append(text[pos:])
    return "".join(out), seen


def run(write):
    with open(DATA, encoding="utf-8") as f:
        benchmark = json.load(f)["benchmark"]
    values = stats(benchmark)
    texts = {}
    for files, pattern, skip in RULES:
        seen_total = 0
        for name in files:
            if name not in texts:
                with open(os.path.join(ROOT, name), encoding="utf-8") as f:
                    texts[name] = f.read()
            texts[name], seen = rewrite(texts[name], pattern, skip, values)
            seen_total += seen
        if not seen_total and not skip:
            raise SystemExit(f"sync_stats: pattern matches nothing (page reworded?): {pattern[:80]}")
    drift = []
    for name, new in texts.items():
        path = os.path.join(ROOT, name)
        with open(path, encoding="utf-8") as f:
            old = f.read()
        if old != new:
            drift.append(name)
            if write:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
    return drift


def main():
    check = "--check" in sys.argv
    drift = run(write=not check)
    for name in drift:
        print(("out of step with titles/data.json: " if check else "updated ") + name)
    sys.exit(1 if (check and drift) else 0)


if __name__ == "__main__":
    main()
