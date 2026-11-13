#!/usr/bin/env python3
"""Numbers for a specification update deck. Read-only.

GitHub through the `gh` CLI, Jira through the public REST API (anonymous). Standard library
only, Python 3.8+. Prints JSON: the Problem Report backlog, and per month merged pull requests,
resolved Problem Reports, Jira comments and the number of distinct people commenting.

    python3 activity.py [--since YYYY-MM-DD] [--months 13] [--until YYYY-MM-DD]

The window ends today (or --until) and covers --months calendar months, the current one
included. "--since" is the start of the reporting period for the backlog figures (resolved,
newly raised, by resolution); default: 30 days before the end.
"""
import argparse
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

ORG = "openEHR"
JIRA = "https://openehr.atlassian.net"
SPEC_PROJECTS = ["SPECPR", "SPECAM", "SPECBASE", "SPECCDS", "SPECCNF", "SPECINTG", "SPECITS", "SPECLANG",
                 "SPECPROC", "SPECPUB", "SPECQUERY", "SPECRM", "SPECTERM", "SPEC"]


def jira_get(path, params=None):
    url = JIRA + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "openehr-update-slides"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def jira_search(jql, fields):
    issues, token = [], None
    while True:
        params = {"jql": jql, "fields": fields, "maxResults": 100}
        if token:
            params["nextPageToken"] = token
        data = jira_get("/rest/api/3/search/jql", params)
        issues += data.get("issues", [])
        token = data.get("nextPageToken")
        if not token:
            return issues


def month_starts(end, count):
    first = end.replace(day=1)
    months = []
    for _ in range(count):
        months.append(first)
        first = (first - timedelta(days=1)).replace(day=1)
    return list(reversed(months))


def merged_prs(start, end):
    """Merged pull requests in the specifications-* repositories, per YYYY-MM."""
    counts = Counter()
    res = subprocess.run(["gh", "search", "prs", "--owner", ORG, "--merged", "--merged-at", "%s..%s" % (start, end),
                          "--limit", "1000", "--json", "repository,closedAt"], capture_output=True)
    if res.returncode != 0:
        sys.exit("gh failed: " + res.stderr.decode("utf-8", "replace").strip())
    for pr in json.loads(res.stdout.decode("utf-8")):
        if pr["repository"]["name"].startswith("specifications-"):
            counts[pr["closedAt"][:7]] += 1
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--until", help="end of the window, default today")
    ap.add_argument("--months", type=int, default=13)
    ap.add_argument("--since", help="start of the reporting period for the backlog figures")
    args = ap.parse_args()

    end = date.fromisoformat(args.until) if args.until else date.today()
    months = month_starts(end, args.months)
    start = months[0]
    since = date.fromisoformat(args.since) if args.since else end - timedelta(days=30)
    keys = [m.strftime("%Y-%m") for m in months]
    projects = ", ".join(SPEC_PROJECTS)

    # backlog
    open_now = len(jira_search("project = SPECPR AND resolution = Unresolved AND statusCategory != Done", "created"))
    resolved = jira_search('project = SPECPR AND resolved >= "%s" AND resolved <= "%s"' % (since, end), "resolution")
    by_resolution = Counter((i["fields"].get("resolution") or {}).get("name", "none") for i in resolved)
    raised = len(jira_search('project = SPECPR AND created >= "%s" AND created <= "%s"' % (since, end), "created"))
    oldest = jira_search("project = SPECPR AND resolution = Unresolved AND statusCategory != Done "
                         "ORDER BY created ASC", "created")[:1]

    # per month
    resolved_month = Counter(i["fields"]["resolutiondate"][:7] for i in jira_search(
        'project = SPECPR AND resolved >= "%s" AND resolved <= "%s"' % (start, end), "resolutiondate"))
    comments, people = Counter(), defaultdict(set)
    for issue in jira_search('project in (%s) AND updated >= "%s"' % (projects, start), "comment"):
        block = issue["fields"].get("comment") or {}
        items = block.get("comments", [])
        if block.get("total", 0) > len(items):
            items = jira_get("/rest/api/3/issue/%s/comment" % issue["key"], {"maxResults": 1000})["comments"]
        for c in items:
            month = c["created"][:7]
            if keys[0] <= month <= keys[-1]:
                comments[month] += 1
                people[month].add((c.get("author") or {}).get("accountId"))
    prs = merged_prs(start, end)

    out = {
        "window": {"from": str(start), "to": str(end), "months": keys,
                   "note": "the last month is partial when the window ends before its last day"},
        "backlog": {"period": {"from": str(since), "to": str(end)}, "open_problem_reports": open_now,
                    "resolved_in_period": len(resolved), "by_resolution": dict(by_resolution),
                    "raised_in_period": raised,
                    "oldest_open_created": oldest[0]["fields"]["created"][:10] if oldest else None},
        "per_month": {
            "merged_pull_requests_spec_repos": [prs[k] for k in keys],
            "problem_reports_resolved": [resolved_month[k] for k in keys],
            "jira_comments_spec_projects": [comments[k] for k in keys],
            "people_commenting": [len(people[k]) for k in keys],
        },
        "sources": {"github": "gh search prs, org %s, repositories specifications-*" % ORG,
                    "jira": "public REST API, projects %s; restricted tickets are not counted" % projects},
    }
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
