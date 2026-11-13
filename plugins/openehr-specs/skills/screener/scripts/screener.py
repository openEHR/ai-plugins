#!/usr/bin/env python3
"""Screener: what can I close, and who is waiting on me, in the openEHR specification work.

Read-only. GitHub through the `gh` CLI (GraphQL), Jira through the public REST API
(anonymous). Standard library only, Python 3.8+.

    python3 screener.py [--login LOGIN] [--jira-name NAME] [--all] [--no-jira] [--out FILE]

Part 1, what can be closed: pull requests that have the approvals their level needs (and, for
a Minor change, the week of notice), and Jira tickets whose pull request is merged or whose
release is out. Part 2, who waits on me: review requests, unanswered questions, rework.
"""
import argparse
import fnmatch
import json
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CONFIG = json.loads((Path(__file__).resolve().parent.parent / "config.json").read_text(encoding="utf-8"))

PR_FIELDS = """
      number title url isDraft createdAt body mergeable
      repository { name }
      author { login ... on User { name } }
      labels(first: 20) { nodes { name } }
      reviewRequests(first: 20) { nodes { requestedReviewer { __typename ... on User { login } } } }
      latestOpinionatedReviews(first: 20) { nodes { author { login } state submittedAt } }
      commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
      comments(last: 50) { nodes { author { login } createdAt body } }
      reviews(last: 50) { nodes { author { login } state submittedAt body } }
"""
OPEN_QUERY = """
query($q: String!, $cursor: String) {
  search(query: $q, type: ISSUE, first: 25, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes { ... on PullRequest { %s } }
  }
}
""" % PR_FIELDS
MERGED_QUERY = """
query($q: String!, $cursor: String) {
  search(query: $q, type: ISSUE, first: 50, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes { ... on PullRequest { number title url body mergedAt repository { name } } }
  }
}
"""
TEAM_QUERY = """
query($org: String!, $team: String!) {
  organization(login: $org) { team(slug: $team) { members(first: 100) { nodes { login } } } }
}
"""
USER_QUERY = "query { viewer { login name } }"

TICKET = re.compile(r"\bSPEC[A-Z]*-\d+\b")
MENTION = re.compile(r"(?<![\w/@.])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))")
ASKING = re.compile(
    r"\?|\b(please|pls|review|thoughts?|opinion|objections?|wdyt|any idea|ok for you|let me know|check if|"
    r"still relevant|(is|are|do|does|did|should|would|can|could|will) (this|that|it|you|we|there))\b", re.I)


# ---------- pure helpers (unit tested) ----------

def ticket_keys(*texts):
    """Jira keys named in the given texts, in order of first appearance."""
    seen = []
    for text in texts:
        for key in TICKET.findall(text or ""):
            if key not in seen:
                seen.append(key)
    return seen


def level_of(labels, level_labels):
    """The change level a pull request is labelled with, or None."""
    names = {name.lower() for name in labels}
    found = [level for level in level_labels if level in names]
    return found[0] if len(found) == 1 else None


def readiness(level, approvals, changes_requested, draft, conflicting, checks, now, needs, wait_days):
    """(state, reason) for one pull request. state: READY, WAIT (only time is missing) or OPEN.

    approvals: datetimes of the approving reviews that count, one per reviewer.
    """
    if draft:
        return "OPEN", "draft"
    if changes_requested:
        return "OPEN", "changes requested by %s" % ", ".join(changes_requested)
    if conflicting:
        return "OPEN", "merge conflict"
    if checks in ("FAILURE", "ERROR"):
        return "OPEN", "checks failing"
    if level is None:
        return "OPEN", "no level label (fix, minor, change-request); %d approval(s)" % len(approvals)
    need = needs[level]
    if len(approvals) < need:
        return "OPEN", "%s: %d of %d approvals" % (level, len(approvals), need)
    if checks == "PENDING":
        return "OPEN", "checks still running"
    wait = wait_days.get(level, 0)
    if wait:
        complete = sorted(approvals)[need - 1]
        due = complete + timedelta(days=wait)
        if now < due:
            return "WAIT", "%s: approvals complete %s, week of notice ends %s" % (level, complete.date(), due.date())
        return "READY", "%s: %d approvals, complete %s, week of notice over since %s" % (
            level, len(approvals), complete.date(), due.date())
    return "READY", "%s: %d approval(s)" % (level, len(approvals))


def norm(name):
    plain = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    return " ".join(plain.lower().split())


def asks_something(text):
    bare = len(re.sub(r"@[\w-]+( [\w-]+)?", "", text).split()) < 4
    return bool(bare or ASKING.search(text))


# ---------- I/O ----------

def gh_graphql(query, fatal=True, **variables):
    cmd = ["gh", "api", "graphql", "-f", "query=" + query]
    for key, value in variables.items():
        if value is not None:
            cmd += ["-f", "%s=%s" % (key, value)]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        if fatal:
            sys.exit("gh failed: " + res.stderr.decode("utf-8", "replace").strip())
        return None
    return json.loads(res.stdout.decode("utf-8"))["data"]


def gh_search(query, q):
    nodes, cursor = [], None
    while True:
        data = gh_graphql(query, q=q, cursor=cursor)["search"]
        nodes += [n for n in data["nodes"] if n]
        if not data["pageInfo"]["hasNextPage"]:
            return nodes
        cursor = data["pageInfo"]["endCursor"]


def jira_get(path, params=None):
    url = CONFIG["jira_base"] + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "openehr-screener"})
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


def parse_dt(text):
    text = text.replace("Z", "+00:00")
    if re.search(r"[+-]\d{4}$", text):
        text = text[:-2] + ":" + text[-2:]
    return datetime.fromisoformat(text)


def strip_code(text):
    text = re.sub(r"```.*?```", " ", text or "", flags=re.S)
    return re.sub(r"`[^`\n]*`", " ", text)


def one_line(text, limit=90):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def md(text):
    return text.replace("|", "\\|").replace("[", "(").replace("]", ")").replace("<", "&lt;")


def repo_in_scope(name):
    return name in CONFIG["extra_repos"] or any(fnmatch.fnmatch(name, p) for p in CONFIG["repo_patterns"])


def pr_link(pr):
    label = "%s #%s" % (pr["repository"]["name"].replace("specifications-", ""), pr["number"])
    return "[%s](%s) %s" % (label, pr["url"], md(one_line(pr["title"], 70)))


def issue_link(key, title=""):
    return "[%s](%s/browse/%s) %s" % (key, CONFIG["jira_base"], key, md(one_line(title, 70)))


# ---------- GitHub ----------

def screen_github(me, sec, args, now):
    """Returns (ready, waiting_time, not_ready, waiting_on_me, open_keys)."""
    ready, wait, not_ready, on_me, open_keys = [], [], [], [], {}
    for pr in gh_search(OPEN_QUERY, "org:%s is:pr is:open archived:false" % CONFIG["org"]):
        if not repo_in_scope(pr["repository"]["name"]):
            continue
        author = (pr.get("author") or {}).get("login", "ghost")
        link = pr_link(pr)
        for key in ticket_keys(pr["title"], pr["body"]):
            open_keys.setdefault(key, []).append(link)
        mine = author.lower() == me.lower()

        opinions = [r for r in pr["latestOpinionatedReviews"]["nodes"] if r.get("author")]
        counts = lambda login: login.lower() != author.lower() and (sec is None or login.lower() in sec)
        approvals = [parse_dt(r["submittedAt"]) for r in opinions
                     if r["state"] == "APPROVED" and counts(r["author"]["login"])]
        changes = [r["author"]["login"] for r in opinions if r["state"] == "CHANGES_REQUESTED"]
        pending = [(n.get("requestedReviewer") or {}).get("login") for n in pr["reviewRequests"]["nodes"]]
        pending = [p for p in pending if p]

        if mine or args.all:
            commit = (pr["commits"]["nodes"] or [{}])[0].get("commit", {})
            checks = (commit.get("statusCheckRollup") or {}).get("state")
            level = level_of([l["name"] for l in pr["labels"]["nodes"]], CONFIG["approvals"])
            state, reason = readiness(level, approvals, changes, pr["isDraft"], pr["mergeable"] == "CONFLICTING",
                                      checks, now, CONFIG["approvals"], CONFIG["wait_days"])
            if state == "OPEN" and pending and not changes and not pr["isDraft"]:
                reason += "; review asked from %s" % ", ".join(pending)
            who = "" if mine else " (by %s)" % author
            {"READY": ready, "WAIT": wait, "OPEN": not_ready}[state].append("%s%s: %s" % (link, who, reason))

        # who waits on me
        if me.lower() in [p.lower() for p in pending]:
            on_me.append("Review: %s, asked by %s" % (link, author))
        if mine and changes:
            on_me.append("Rework: %s, changes requested by %s" % (link, ", ".join(changes)))
        events = [(parse_dt(pr["createdAt"]), author, pr.get("body") or "")]
        events += [(parse_dt(c["createdAt"]), c["author"]["login"], c.get("body") or "")
                   for c in pr["comments"]["nodes"] if c.get("author")]
        events += [(parse_dt(r["submittedAt"]), r["author"]["login"], r.get("body") or "")
                   for r in pr["reviews"]["nodes"] if r.get("author") and r.get("submittedAt")]
        asked = None
        for when, who_said, body in sorted(events, key=lambda e: e[0]):
            if who_said.lower() == me.lower():
                asked = None                      # speaking answers earlier mentions
            elif any(m.lower() == me.lower() for m in MENTION.findall(strip_code(body))) \
                    and asks_something(strip_code(body)):
                asked = asked or (when, who_said)
        if asked and me.lower() not in [p.lower() for p in pending]:
            on_me.append("Answer: %s, asked by %s %s" % (link, asked[1], asked[0].date()))
    return ready, wait, not_ready, on_me, open_keys


def merged_keys(me, args, now):
    """Ticket key -> links of my pull requests merged in the window that name it."""
    since = (now - timedelta(days=args.days)).date()
    q = "org:%s is:pr is:merged author:%s merged:>=%s" % (CONFIG["org"], me, since)
    keys = {}
    for pr in gh_search(MERGED_QUERY, q):
        if repo_in_scope(pr["repository"]["name"]):
            in_title = ticket_keys(pr["title"])
            for key in ticket_keys(pr["title"], pr["body"]):
                note = "" if key in in_title else " (names the ticket in its description only)"
                keys.setdefault(key, []).append(pr_link(pr) + note)
    return keys


# ---------- Jira ----------

def adf_walk(node, mentions, texts):
    if isinstance(node, dict):
        if node.get("type") == "mention":
            text = (node.get("attrs", {}).get("text") or "")
            mentions.append(text.lstrip("@"))
            texts.append(text)
        elif node.get("type") == "text":
            texts.append(node.get("text", ""))
        for value in node.values():
            adf_walk(value, mentions, texts)
    elif isinstance(node, list):
        for value in node:
            adf_walk(value, mentions, texts)


def screen_jira(my_name, merged, open_keys, args, now):
    """Returns (to_close, on_me, unseen): ticket lines, question lines, keys Jira did not show."""
    to_close, on_me, unseen = [], [], []
    projects = ", ".join(CONFIG["jira_projects"])
    done_names = {s.lower() for s in CONFIG["resolved_statuses"]}

    # 1. tickets named by my merged pull requests that are still open
    for key, links in merged.items():
        try:
            f = jira_get("/rest/api/3/issue/%s" % key, {"fields": "summary,status"})["fields"]
        except urllib.error.HTTPError:
            unseen.append(key)
            continue
        status = f["status"]
        if status["statusCategory"]["key"] == "done" or status["name"].lower() in done_names:
            continue
        line = "Resolve: %s is %s, but %s merged" % (
            issue_link(key, f["summary"]), status["name"], " and ".join(links))
        if key in open_keys:
            line += "; still open for it: %s" % " and ".join(open_keys[key])
        to_close.append(line)

    # 2. my resolved tickets whose release is out
    jql = "project in (%s) AND assignee is not EMPTY AND status in (%s)" % (
        projects, ", ".join('"%s"' % s for s in CONFIG["resolved_statuses"]))
    for issue in jira_search(jql, "summary,assignee,fixVersions,status"):
        f = issue["fields"]
        if norm((f.get("assignee") or {}).get("displayName")) != norm(my_name):
            continue
        versions = f.get("fixVersions") or []
        if versions and all(v.get("released") for v in versions):
            to_close.append("Close: %s is %s and released in %s" % (
                issue_link(issue["key"], f["summary"]), f["status"]["name"], ", ".join(v["name"] for v in versions)))
        elif not versions:
            to_close.append("Fix Version missing: %s is %s without a release" % (
                issue_link(issue["key"], f["summary"]), f["status"]["name"]))

    # 3. questions put to me in open tickets, not answered since
    cutoff = now - timedelta(days=args.days)
    jql = ("project in (%s) AND resolution = Unresolved AND statusCategory != Done AND updated >= -%dd "
           "ORDER BY updated DESC" % (projects, args.days))
    for issue in jira_search(jql, "summary,comment"):
        block = issue["fields"].get("comment") or {}
        comments = block.get("comments", [])
        if block.get("total", 0) > len(comments):
            comments = jira_get("/rest/api/3/issue/%s/comment" % issue["key"], {"maxResults": 1000})["comments"]
        asked = None
        for c in comments:
            author = (c.get("author") or {}).get("displayName", "?")
            if norm(author) == norm(my_name):
                asked = None
                continue
            mentions, texts = [], []
            adf_walk(c.get("body"), mentions, texts)
            body = " ".join("".join(texts).split())
            when = parse_dt(c["created"])
            if when >= cutoff and any(norm(m) == norm(my_name) for m in mentions) and asks_something(body):
                asked = asked or (when, author, body)
        if asked:
            on_me.append("Answer: %s, asked by %s %s: \"%s\"" % (
                issue_link(issue["key"], issue["fields"]["summary"]), asked[1], asked[0].date(),
                md(one_line(asked[2], 140))))
    return to_close, on_me, unseen


# ---------- report ----------

def section(title, lines, empty="nothing"):
    return ["### %s" % title, ""] + (["- %s" % l for l in lines] or [empty]) + [""]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--login", help="GitHub login to screen for (default: the logged-in gh user)")
    ap.add_argument("--jira-name", help="display name in Jira (default: the GitHub profile name)")
    ap.add_argument("--all", action="store_true", help="every open pull request in scope, not only mine")
    ap.add_argument("--days", type=int, default=90, help="window for merged pull requests and Jira questions")
    ap.add_argument("--no-jira", action="store_true", help="GitHub only")
    ap.add_argument("--out", help="write the Markdown report to this file instead of stdout")
    args = ap.parse_args()
    now = datetime.now(timezone.utc)

    viewer = gh_graphql(USER_QUERY)["viewer"]
    me = args.login or viewer["login"]
    my_name = args.jira_name or (viewer.get("name") if me == viewer["login"] else None) or me

    team = gh_graphql(TEAM_QUERY, fatal=False, org=CONFIG["org"], team=CONFIG["sec_team"])
    members = ((team or {}).get("organization") or {}).get("team") or {}
    sec = {m["login"].lower() for m in members.get("members", {}).get("nodes", [])} or None

    ready, wait, not_ready, on_me, open_keys = screen_github(me, sec, args, now)
    to_close, unseen = [], []
    if not args.no_jira:
        to_close, jira_on_me, unseen = screen_jira(my_name, merged_keys(me, args, now), open_keys, args, now)
        on_me += jira_on_me

    out = ["# Screener for %s (%s)" % (my_name, now.date()), ""]
    out += ["## 1. What can be closed", ""]
    out += section("Pull requests ready to merge", ready)
    out += section("Tickets to resolve or close", to_close, "nothing" if not args.no_jira else "Jira not checked")
    out += ["## 2. Who is waiting on you", ""]
    order = {"Review": 0, "Answer": 1, "Rework": 2}
    out += section("Reviews, answers, rework", sorted(on_me, key=lambda l: order.get(l.split(":")[0], 9)))
    out += ["## 3. Not closable yet", ""]
    out += section("Approved, in the week of notice", wait)
    out += section("Open pull requests and what each needs", not_ready)
    notes = []
    if sec is None:
        notes.append("The SEC team could not be read, so every approval was counted, not only those of SEC members.")
    if unseen:
        notes.append("Not visible in Jira without a login: %s." % ", ".join(unseen))
    notes.append("Candidates only: nothing was merged, resolved or closed.")
    out += ["Notes: " + " ".join(notes)]
    report = "\n".join(out) + "\n"
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8", newline="\n")
        print("written: %s" % args.out)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(report)


if __name__ == "__main__":
    main()
