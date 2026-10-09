#!/usr/bin/env python3
"""Weekly film-page refresh: export the analysis, refresh the pages, open a pull request.

  tools/weekly_refresh.py [--repo <checkout>] [--dry-run]

Reads rated titles from Firestore (read-only), runs `build_titles.py --refresh` in a throwaway
worktree of origin/main, and if any page changed pushes a `refresh/<date>` branch and opens a
pull request. It never merges and never passes --accept-changes: a change that would surprise a
parent is listed in the pull request (or an issue, when nothing else changed) for a human look.

Auth: `GOOGLE_OAUTH_ACCESS_TOKEN` if set, otherwise `gcloud auth print-access-token`. Needs `git`
and an authenticated `gh`. --dry-run does everything except push, pull request and issue.
Stdlib only.
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

FIRESTORE = "https://firestore.googleapis.com/v1/projects/familyfiltertv/databases/(default)"
SITE_REPO = "Jacquesdp7066/familyfiltertv-site"
HELD_ISSUE_TITLE = "Film page refresh: changes held for review"
# The only paths a refresh may publish.
PUBLISHED = ("titles", "sitemap.xml", "llms.txt")


def plain(v):
    """A Firestore REST value as a plain Python value."""
    if "mapValue" in v:
        return {k: plain(x) for k, x in v["mapValue"].get("fields", {}).items()}
    if "arrayValue" in v:
        return [plain(x) for x in v["arrayValue"].get("values", [])]
    kind, x = next(iter(v.items()))
    return int(x) if kind == "integerValue" else x


def rows_from_query(results):
    rows = []
    for r in results:
        doc = r.get("document")
        if not doc:
            continue
        row = {k: plain(v) for k, v in doc["fields"].items()}
        row["videoId"] = doc["name"].rsplit("/", 1)[1]
        rows.append(row)
    return rows


def access_token():
    token = os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN")
    if not token:
        token = subprocess.run(
            ["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True
        ).stdout.strip()
    return token


def export_ratings():
    query = {"structuredQuery": {
        "from": [{"collectionId": "ratings"}],
        "where": {"fieldFilter": {"field": {"fieldPath": "status"}, "op": "EQUAL", "value": {"stringValue": "rated"}}},
    }}
    request = urllib.request.Request(
        FIRESTORE + "/documents:runQuery",
        data=json.dumps(query).encode(),
        headers={
            "Authorization": "Bearer " + access_token(),
            "x-goog-user-project": "familyfiltertv",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return rows_from_query(json.load(response))


def run(args, cwd, check=True):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=check)


def report_body(log, changed):
    lines = [ln for ln in log.splitlines() if ln.startswith(("updated", "HELD", "REJECTED"))]
    detail = "\n".join(lines) if lines else "(the comparison data changed; no film's own numbers did)"
    return (
        "Weekly refresh of the film pages from the subtitle analysis, by `tools/weekly_refresh.py`.\n\n"
        f"Files changed: {changed}\n\n```\n{detail}\n```\n\n"
        "`HELD` lines changed a film's language level or moved its count sharply. They are **not** "
        "in this change. Check the film, then run `tools/build_titles.py --refresh <export> "
        "--accept-changes`. `REJECTED` lines were malformed in the export and are never applied.\n"
    )


def main():
    dry_run = "--dry-run" in sys.argv
    repo = os.path.abspath(sys.argv[sys.argv.index("--repo") + 1]) if "--repo" in sys.argv else os.getcwd()
    today = datetime.date.today().isoformat()
    branch = f"refresh/{today}"

    run(["git", "fetch", "--quiet", "origin"], repo)
    if run(["git", "ls-remote", "--heads", "origin", branch], repo).stdout.strip():
        sys.exit(f"{branch} already exists on origin; today's refresh has run")

    work = tempfile.mkdtemp(prefix="film-refresh-")
    tree = os.path.join(work, "site")
    export_path = os.path.join(work, "ratings-export.json")
    run(["git", "worktree", "add", "--quiet", "--detach", tree, "origin/main"], repo)
    try:
        rows = export_ratings()
        with open(export_path, "w") as f:
            json.dump(rows, f)
        print(f"exported {len(rows)} rated titles")

        refresh = run([sys.executable, "tools/build_titles.py", "--refresh", export_path], tree)
        print(refresh.stdout.strip())
        tests = run([sys.executable, "tools/test_build_titles.py"], tree, check=False)
        if tests.returncode != 0:
            sys.exit("generator tests failed after the refresh; nothing published\n" + tests.stderr[-2000:])

        status = run(["git", "status", "--porcelain", "--", *PUBLISHED], tree).stdout
        changed = [ln for ln in status.splitlines() if ln.strip()]
        held = [ln for ln in refresh.stdout.splitlines() if ln.startswith(("HELD", "REJECTED"))]
        body = report_body(refresh.stdout, len(changed))

        if not changed and not held:
            print("no changes")
            return
        if dry_run:
            print(f"dry run: {len(changed)} files changed, {len(held)} held; nothing pushed\n\n{body}")
            return
        if changed:
            run(["git", "checkout", "--quiet", "-b", branch], tree)
            run(["git", "add", "--", *PUBLISHED], tree)
            run(["git", "commit", "--quiet", "-m", f"Weekly film page refresh, {today}\n\nGenerated by tools/weekly_refresh.py from the subtitle analysis export."], tree)
            run(["git", "push", "--quiet", "-u", "origin", branch], tree)
            pr = run(["gh", "pr", "create", "-R", SITE_REPO, "--base", "main", "--head", branch,
                      "--title", f"Weekly film page refresh, {today}", "--body", body], tree)
            print(pr.stdout.strip())
        else:
            open_issue = run(["gh", "issue", "list", "-R", SITE_REPO, "--state", "open", "--search",
                              f'"{HELD_ISSUE_TITLE}" in:title', "--json", "number", "-q", ".[0].number"], tree).stdout.strip()
            if open_issue:
                run(["gh", "issue", "comment", open_issue, "-R", SITE_REPO, "--body", body], tree)
                print(f"commented on issue #{open_issue}")
            else:
                issue = run(["gh", "issue", "create", "-R", SITE_REPO, "--title", HELD_ISSUE_TITLE, "--body", body], tree)
                print(issue.stdout.strip())
    finally:
        run(["git", "worktree", "remove", "--force", tree], repo, check=False)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
