# Bing Webmaster Tools setup for familyfiltertv.com

Why: Bing (and DuckDuckGo, Yahoo, Ecosia and the ChatGPT search index, which lean on Bing) is a free
second source of search traffic. Google Search Console is already set up; importing from it is the
fastest route and takes about five minutes. Free only: nothing here costs money.

You need: the Google account that owns the Search Console property for familyfiltertv.com (the
URL-prefix property), and a Microsoft account (any, a new free one is fine).

## 1. Add the site by importing from Google Search Console (fastest)

1. Go to https://www.bing.com/webmasters and sign in with the Microsoft account.
2. On the "Add a site" screen choose **Import your sites from GSC**.
3. Click **Continue**, sign in to the Google account that owns the Search Console property, and allow
   Bing access (read-only).
4. Tick **familyfiltertv.com** and click **Import**. Bing verifies ownership through Google, so there is
   nothing to upload. Leave "Import sitemaps" ticked.
5. Wait for the green "verified" state. If ownership shows as pending, give it up to a day, then use
   the manual fallback below.

Manual fallback (only if the import fails): choose **Add your site manually**, enter
`https://familyfiltertv.com/`, then verify with the **HTML Meta Tag** or **XML file** option. For the
XML file option, send the file to Claude (it goes in the site repo root, like the Google and IndexNow
files) and merge it before clicking Verify.

## 2. Submit sitemap.xml

If step 1 imported the sitemap, it is already listed; open it and make sure the status says Success.
Otherwise:

1. In the left menu open **Sitemaps**.
2. Click **Submit sitemap**, paste `https://familyfiltertv.com/sitemap.xml`, and click **Submit**.
3. Status goes Pending, then Success (a few minutes to a day). It lists 54 URLs at the time of
   writing; the film pages under `/titles/` are part of it.

## 3. Confirm IndexNow is recognised

IndexNow is already wired up on the site, so nothing needs installing:

- The key file is live at https://familyfiltertv.com/4ad2adafa64621f92399c85be15f01bb.txt (it contains
  the key `4ad2adafa64621f92399c85be15f01bb`) and is referenced from robots.txt.
- After every push to `main`, `.github/workflows/indexnow.yml` waits three minutes for GitHub Pages
  and then runs `python3 tools/indexnow.py`, which sends every URL in sitemap.xml to
  api.indexnow.org. Bing, Yandex, Seznam and Naver all receive it from that one call.

To confirm Bing has picked it up:

1. In Bing Webmaster Tools open **IndexNow** in the left menu (it sits with the other submission
   tools; if you cannot find it, use the search box at the top and type "IndexNow").
2. Look for the key `4ad2adafa64621f92399c85be15f01bb` and a count of recently submitted URLs. The
   first submissions show up within a day or two of the next push to `main`.
3. As a second check, open **URL Inspection**, paste
   `https://familyfiltertv.com/titles/moana-2016/` and click **Inspect**. After a few days it should
   show as discovered or indexed, with "Discovered via IndexNow" or "via Sitemap" in the details.

If IndexNow shows nothing after three or four days, check that the GitHub Actions run named
"IndexNow" succeeded on the last push to `main`. The Actions budget is capped at $0, so a run can
fail instantly with no log. In that case submit by hand from the site repo on the Mac:

    python3 tools/indexnow.py

It prints `IndexNow: HTTP 200` (or 202) when accepted. `--dry-run` shows the payload without sending.

## 4. After setup

- Come back in a week and open **Search Performance**. Bing reports impressions, clicks and queries
  just like Search Console; the film-page question titles ("Is Moana (2016) OK for kids?") are what
  to watch.
- Under **Configure My Site > Crawl Control** leave the defaults.
- Nothing else is needed: no paid features, no ads.
