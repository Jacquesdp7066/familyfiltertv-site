#!/usr/bin/env python3
"""Tell IndexNow search engines (Bing, Yandex, Seznam, Naver) which URLs to recrawl.

Reads the key from the 32-hex-character .txt file at the repo root, reads every
<loc> from sitemap.xml and POSTs them to https://api.indexnow.org/indexnow.

  python3 tools/indexnow.py --dry-run   print the payload, send nothing

Stdlib only.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = "familyfiltertv.com"
ENDPOINT = "https://api.indexnow.org/indexnow"
KEY_FILE = re.compile(r"^([0-9a-fA-F]{32})\.txt$")
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def find_key():
    keys = [m.group(1) for n in sorted(os.listdir(ROOT)) if (m := KEY_FILE.match(n))]
    if len(keys) != 1:
        sys.exit(f"expected exactly one 32-hex .txt key file in {ROOT}, found {len(keys)}")
    return keys[0]


def sitemap_urls():
    tree = ET.parse(os.path.join(ROOT, "sitemap.xml"))
    return [e.text.strip() for e in tree.getroot().findall("sm:url/sm:loc", NS) if e.text]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="print the payload and send nothing")
    args = ap.parse_args()

    key = find_key()
    urls = sitemap_urls()
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/{key}.txt",
        "urlList": urls,
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        print(f"{len(urls)} URLs (dry run, nothing sent)", file=sys.stderr)
        return

    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow: HTTP {resp.status} for {len(urls)} URLs")
    except urllib.error.HTTPError as e:
        # 200/202 are success; anything else (403 key not found yet, 422, 429) is reported
        sys.exit(f"IndexNow: HTTP {e.code} {e.reason}: {e.read().decode('utf-8', 'replace')[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"IndexNow: request failed: {e.reason}")


if __name__ == "__main__":
    main()
