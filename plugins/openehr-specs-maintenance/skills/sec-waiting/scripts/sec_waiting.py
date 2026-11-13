#!/usr/bin/env python3
"""SEC waiting list: who are we waiting on, for which PR review or Jira answer.

Read-only. GitHub through the `gh` CLI (GraphQL), Jira through the public REST API
(anonymous). Standard library only, Python 3.8+.

    python3 sec_waiting.py [--days 180] [--stale 14] [--person NAME] [--no-jira] [--out FILE]

Settings come from config.json next to the skill. Personal settings (name maps, pinned
tickets) go in a file of the same shape that is merged over it: the path in the environment
variable SEC_WAITING_CONFIG, or config.local.json next to config.json.
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

def load_config():
    """config.json, with the personal file merged over it (dicts merge, other values replace)."""
    base = Path(__file__).resolve().parent.parent
    config = json.loads((base / "config.json").read_text(encoding="utf-8"))
    local = Path(os.environ.get("SEC_WAITING_CONFIG") or base / "config.local.json")
    if local.is_file():
        for key, value in json.loads(local.read_text(encoding="utf-8")).items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
    return config


CONFIG = load_config()
NOW = datetime.now(timezone.utc)

PR_QUERY = """
query($q: String!, $cursor: String) {
  search(query: $q, type: ISSUE, first: 25, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes { ... on PullRequest {
      number title url isDraft createdAt body
      repository { name isArchived }
      author { __typename login ... on User { name } }
      reviewRequests(first: 20) { nodes { requestedReviewer {
        __typename ... on User { login name } ... on Team { slug name } } } }
      latestOpinionatedReviews(first: 20) { nodes { author { login ... on User { name } } state submittedAt } }
      timelineItems(itemTypes: [REVIEW_REQUESTED_EVENT], last: 40) { nodes {
        ... on ReviewRequestedEvent { createdAt requestedReviewer {
          __typename ... on User { login } ... on Team { slug } } } } }
      comments(last: 50) { nodes { author { login ... on User { name } } createdAt body } }
      reviews(last: 50) { nodes { author { login ... on User { name } } state submittedAt body } }
    } }
  }
}
"""
TEAM_QUERY = """
query($org: String!, $team: String!) {
  organization(login: $org) { team(slug: $team) { members(first: 100) { nodes { login name } } } }
}
"""


# ---------- helpers ----------

def gh_graphql(query, **variables):
    cmd = ["gh", "api", "graphql", "-f", "query=" + query]
    for key, value in variables.items():
        if value is not None:
            cmd += ["-f", "%s=%s" % (key, value)]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        sys.exit("gh failed: " + res.stderr.decode("utf-8", "replace").strip())
    return json.loads(res.stdout.decode("utf-8"))["data"]


def jira_get(path, params=None):
    url = CONFIG["jira_base"] + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "sec-waiting"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_dt(text):
    text = text.replace("Z", "+00:00")
    if re.search(r"[+-]\d{4}$", text):
        text = text[:-2] + ":" + text[-2:]
    return datetime.fromisoformat(text)


def norm(name):
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return " ".join(plain.lower().split())


def age(since):
    return max((NOW - since).days, 0)


def one_line(text, limit=110):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


ASKING = re.compile(
    r"\?|\b(please|pls|review|thoughts?|opinion|objections?|wdyt|any idea|ok for you|let me know|check if|"
    r"still relevant|(is|are|do|does|did|should|would|can|could|will) (this|that|it|you|we|there))\b", re.I)


def mention_kind(text):
    """Answer = the comment asks something (or is a bare ping); Mention = named only."""
    bare = len(re.sub(r"@[\w-]+( [\w-]+)?", "", text).split()) < 4
    return "Answer" if bare or ASKING.search(text) else "Mention"


def excerpt_at(text, name, limit=110):
    """Excerpt of a comment, starting at the mention when it sits far into the text."""
    text = " ".join(text.split())
    at = text.find("@" + name)
    if at > 60:
        text = "…" + text[at:]
    return one_line(text, limit)


def md(text):
    return text.replace("|", "\\|").replace("[", "(").replace("]", ")").replace("<", "&lt;")


class People:
    """One identity per person across GitHub logins and Jira display names."""

    def __init__(self):
        self.display = {}   # norm name -> display name
        self.login = {}     # norm name -> github login
        self.gh = {}        # github login -> display name

    def add_github(self, login, name=None):
        name = CONFIG["github_names"].get(login) or self.gh.get(login) or (name or "").strip() or login
        self.gh[login] = name
        self.display.setdefault(norm(name), name)
        self.login[norm(name)] = login
        return norm(name)

    def add_jira(self, display_name):
        name = CONFIG["jira_names"].get(display_name, display_name)
        self.display.setdefault(norm(name), name)
        return norm(name)

    def heading(self, key):
        login = self.login.get(key)
        return "%s (@%s)" % (self.display[key], login) if login and login != self.display[key] else self.display[key]


# ---------- GitHub ----------

def repo_in_scope(name):
    return name in CONFIG["extra_repos"] or any(fnmatch.fnmatch(name, p) for p in CONFIG["repo_patterns"])


def fetch_prs():
    prs, cursor = [], None
    while True:
        data = gh_graphql(PR_QUERY, q="org:%s is:pr is:open archived:false" % CONFIG["org"], cursor=cursor)["search"]
        prs += [n for n in data["nodes"] if n]
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]
    keep = []
    for pr in prs:
        author = pr.get("author") or {}
        if not repo_in_scope(pr["repository"]["name"]):
            continue
        if author.get("__typename") == "Bot" or author.get("login", "").endswith("[bot]"):
            continue
        keep.append(pr)
    return keep


def strip_code(text):
    text = re.sub(r"```.*?```", " ", text or "", flags=re.S)
    return re.sub(r"`[^`\n]*`", " ", text)


MENTION = re.compile(r"(?<![\w/@.])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))")


def pr_label(pr):
    return "%s #%s" % (pr["repository"]["name"].replace("specifications-", ""), pr["number"])


def pr_link(pr):
    return "[%s](%s) %s" % (pr_label(pr), pr["url"], md(one_line(pr["title"], 80)))


def scan_github(people, sec_logins, waiting, sections):
    for pr in fetch_prs():
        author = (pr.get("author") or {}).get("login", "ghost")
        author_key = people.add_github(author, (pr.get("author") or {}).get("name"))
        created = parse_dt(pr["createdAt"])
        link = pr_link(pr)

        # everything said on the PR, oldest first
        events = [(created, author, pr.get("body") or "")]
        for c in pr["comments"]["nodes"]:
            if c.get("author"):
                people.add_github(c["author"]["login"], c["author"].get("name"))
                events.append((parse_dt(c["createdAt"]), c["author"]["login"], c.get("body") or ""))
        for r in pr["reviews"]["nodes"]:
            if r.get("author") and r.get("submittedAt"):
                people.add_github(r["author"]["login"], r["author"].get("name"))
                events.append((parse_dt(r["submittedAt"]), r["author"]["login"], r.get("body") or ""))
        events.sort(key=lambda e: e[0])
        last_when, last_who, _ = events[-1]

        if pr["isDraft"]:
            sections["drafts"].append((created, "%s, by %s, opened %s" % (link, people.gh[author], created.date())))
            continue

        requested_at = {}
        for t in pr["timelineItems"]["nodes"]:
            rr = (t or {}).get("requestedReviewer") or {}
            who = rr.get("login") or rr.get("slug")
            if who:
                requested_at[who] = parse_dt(t["createdAt"])

        pending = set()
        for node in pr["reviewRequests"]["nodes"]:
            rr = node.get("requestedReviewer") or {}
            if rr.get("__typename") == "Team":
                key = people.add_jira("Team " + (rr.get("name") or rr["slug"]))
                who = rr["slug"]
            elif rr.get("login"):
                key = people.add_github(rr["login"], rr.get("name"))
                who = rr["login"]
            else:
                continue
            pending.add(who)
            since = requested_at.get(who, created)
            waiting[key].append((since, "Review", "%s, asked by %s %s" % (link, people.gh[author], since.date()),
                                 "github", "[%s](%s)" % (pr_label(pr), pr["url"])))

        opinions = [r for r in pr["latestOpinionatedReviews"]["nodes"] if r.get("author")]
        changes = [r for r in opinions if r["state"] == "CHANGES_REQUESTED" and r["author"]["login"] not in pending]
        approvals = [r for r in opinions if r["state"] == "APPROVED"]
        for r in changes:
            since = parse_dt(r["submittedAt"])
            reviewer = people.gh.get(r["author"]["login"], r["author"]["login"])
            waiting[author_key].append((since, "Rework", "%s, changes requested by %s %s" % (link, reviewer, since.date())))
        if approvals and not changes and not pending:
            since = max(parse_dt(r["submittedAt"]) for r in approvals)
            names = ", ".join(people.gh.get(r["author"]["login"], r["author"]["login"]) for r in approvals)
            waiting[author_key].append((since, "Merge", "%s, approved by %s %s" % (link, names, since.date())))

        # @mentions of SEC members with no reaction from them afterwards
        open_mentions = {}
        for when, who, body in events:
            open_mentions.pop(who, None)            # speaking answers earlier mentions
            for login in set(MENTION.findall(strip_code(body))):
                match = next((s for s in sec_logins if s.lower() == login.lower()), None)
                if match and match != who and match not in pending:
                    open_mentions.setdefault(match, (when, who, mention_kind(strip_code(body))))
        for login, (when, who, kind) in open_mentions.items():
            key = people.add_github(login)
            waiting[key].append((when, kind, "%s, mentioned by %s %s" % (link, people.gh[who], when.date())))

        if not pending and not opinions:
            note = "opened %s by %s" % (created.date(), people.gh[author])
            if last_when > created:
                note += ", last comment %s by %s" % (last_when.date(), people.gh.get(last_who, last_who))
            sections["no_reviewer"].append((created, "%s, %s" % (link, note)))


# ---------- Jira ----------

def adf_walk(node, mentions, texts):
    if isinstance(node, dict):
        if node.get("type") == "mention":
            attrs = node.get("attrs", {})
            mentions.append((attrs.get("id"), (attrs.get("text") or "").lstrip("@")))
            texts.append(attrs.get("text") or "")
        elif node.get("type") == "text":
            texts.append(node.get("text", ""))
        for value in node.values():
            adf_walk(value, mentions, texts)
    elif isinstance(node, list):
        for value in node:
            adf_walk(value, mentions, texts)


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


def all_comments(issue):
    block = issue["fields"].get("comment") or {}
    comments = block.get("comments", [])
    if block.get("total", 0) <= len(comments):
        return comments
    comments, start = [], 0
    while True:
        data = jira_get("/rest/api/3/issue/%s/comment" % issue["key"], {"startAt": start, "maxResults": 100})
        comments += data["comments"]
        start += len(data["comments"])
        if start >= data["total"] or not data["comments"]:
            return comments


def scan_jira(people, waiting, sections, days):
    base = CONFIG["jira_base"]
    projects = ", ".join(CONFIG["jira_projects"])
    cutoff = NOW - timedelta(days=days)
    jql = "project in (%s) AND resolution = Unresolved AND statusCategory != Done AND updated >= -%dd ORDER BY updated DESC" % (projects, days)
    for issue in jira_search(jql, "summary,comment,status"):
        open_mentions = {}                       # accountId -> (when, asker, name, kind, excerpt, index)
        said = []                                # (when, author, text) of every comment, in order
        for c in all_comments(issue):
            author = c.get("author") or {}
            when = parse_dt(c["created"])
            # commenting answers earlier mentions; matched by name, since some people
            # have two Jira accounts (mentioned on one, answering from the other)
            author_name = norm(author.get("displayName", "?"))
            open_mentions.pop(author_name, None)
            mentions, texts = [], []
            adf_walk(c.get("body"), mentions, texts)
            body = " ".join("".join(texts).split())
            said.append((when, author.get("displayName", "?"), body))
            for account_id, name in mentions:
                if name and norm(name) != author_name and when >= cutoff:
                    open_mentions.setdefault(
                        norm(name), (when, author.get("displayName", "?"), name, mention_kind(body),
                                     excerpt_at(body, name), len(said) - 1))
        link = "[%s](%s/browse/%s) %s" % (issue["key"], base, issue["key"], md(one_line(issue["fields"]["summary"], 80)))
        for when, asker, name, kind, excerpt, index in open_mentions.values():
            key = people.add_jira(name)
            detail = {"title": issue["fields"]["summary"], "status": issue["fields"]["status"]["name"],
                      "asked": said[index], "later": said[index + 1:]}
            waiting[key].append((when, kind, "%s, by %s %s: \"%s\"" % (link, asker, when.date(), md(excerpt)),
                                 "jira", "[%s](%s/browse/%s)" % (issue["key"], base, issue["key"]), detail))

    assigned = defaultdict(int)
    ids = {}
    for issue in jira_search("project in (%s) AND resolution = Unresolved AND statusCategory != Done AND assignee is not EMPTY" % projects, "assignee"):
        who = issue["fields"]["assignee"]
        assigned[who["displayName"]] += 1
        ids[who["displayName"]] = who["accountId"]
    for name, count in sorted(assigned.items(), key=lambda kv: -kv[1]):
        q = 'project in (%s) AND resolution = Unresolved AND statusCategory != Done AND assignee = "%s" ORDER BY updated DESC' % (projects, ids[name])
        sections["assigned"].append("[%s: %d](%s/issues/?jql=%s)" % (name, count, base, urllib.parse.quote(q)))


# ---------- report ----------

def mine_link(jql):
    """Link to a search that uses currentUser(): goes through the login page, since Jira shows
    an empty list to visitors who are not logged in."""
    dest = "/issues/?jql=" + urllib.parse.quote(jql, safe="")
    return "%s/login.jsp?os_destination=%s" % (CONFIG["jira_base"], urllib.parse.quote(dest, safe=""))


def render(people, waiting, sections, args):
    stale = args.stale

    def days_text(since):
        d = age(since)
        return "**%d d**" % d if d >= stale else "%d d" % d

    if args.person:
        wanted = norm(args.person)
        waiting = {k: v for k, v in waiting.items()
                   if wanted in k or wanted in norm(people.login.get(k, ""))}

    items = [i for v in waiting.values() for i in v]
    counts = defaultdict(int)
    for kind in (i[1] for i in items):
        counts[kind] += 1
    out = ["# SEC: what we are waiting on (%s)" % NOW.date(), ""]
    out.append("Waiting on %d people: %d reviews, %d answers, %d reworks, %d merges, plus %d mentions without "
               "a question. %d open PRs have no reviewer. Bold = waiting %d days or more."
               % (len(waiting), counts["Review"], counts["Answer"], counts["Rework"], counts["Merge"],
                  counts["Mention"], len(sections["no_reviewer"]), stale))
    out.append("")
    out.append("## Waiting on you")
    out.append("")
    order = sorted(waiting, key=lambda k: (-len(waiting[k]), min(i[0] for i in waiting[k])))
    for key in order:
        out.append("### %s" % people.heading(key))
        for item in sorted(waiting[key], key=lambda i: i[0]):
            out.append("- %s (%s): %s" % (item[1], days_text(item[0]), item[2]))
        out.append("")
    if not order:
        out += ["Nothing found.", ""]

    if not args.person:
        if sections["no_reviewer"]:
            out += ["## Open PRs without a reviewer", "",
                    "Nobody is asked. The author picks a reviewer, or a SEC member takes it.", ""]
            for since, text in sorted(sections["no_reviewer"], key=lambda i: i[0]):
                out.append("- %s: %s" % (days_text(since), text))
            out.append("")
        if sections["drafts"]:
            out += ["## Drafts (with the author)", ""]
            for since, text in sorted(sections["drafts"], key=lambda i: i[0]):
                out.append("- %s" % text)
            out.append("")

    if not args.no_jira:
        mine = "resolution = Unresolved AND statusCategory != Done AND (assignee = currentUser() OR comment ~ currentUser()) ORDER BY updated DESC"
        out += ["## Jira: check your own list", "",
                "Mentions above cover the last %d days only. Everything open that is assigned to you or "
                "mentions you: [my open openEHR tickets](%s)." % (args.days, mine_link(mine)), ""]
        if sections["assigned"] and not args.person:
            out += ["Open tickets by assignee: " + " · ".join(sections["assigned"]), ""]

    out.append("Legend: Review = review requested on a PR; Answer = @mentioned with a question, no reply since; "
               "Mention = @mentioned without a question, no reply since; "
               "Rework = changes requested, with the author; Merge = approved, not merged.")
    return "\n".join(out) + "\n"


def render_short(people, waiting, args):
    """Default report, made for a Discourse post: link, then who is asked; sorted by name."""
    if args.person:
        wanted = norm(args.person)
        waiting = {k: v for k, v in waiting.items()
                   if wanted in k or wanted in norm(people.login.get(k, ""))}
    kinds = ("Answer", "Mention") if args.all_mentions else ("Answer",)
    github, jira = [], []
    by_name = {norm(k): v for k, v in CONFIG.get("discourse_by_name", {}).items()}

    def ping(key):
        """@discourse.username when known, else the plain name (no ping)."""
        handle = CONFIG["discourse_names"].get(people.login.get(key, "")) or by_name.get(key)
        return "@" + handle if handle else people.display[key]

    excluded = {e.strip().lower() for e in (args.exclude or "").split(",") if e.strip()}
    review = []

    def dropped(item, key):
        ident = re.match(r"\[([^\]]+)\]", item[4]).group(1).replace(" ", "").lower()
        return ident in excluded or "%s@%s" % (ident, ping(key).lstrip("@").lower()) in excluded

    # one line per person, sorted by name; SEC members only unless --everyone
    for key in sorted(waiting):
        if not args.everyone and people.login.get(key) not in args.sec_logins:
            continue
        mine_gh, mine_jira = [], []
        for item in sorted(waiting[key], key=lambda i: i[0]):
            if len(item) < 5 or dropped(item, key):
                continue
            if item[3] == "github" and item[1] == "Review":
                mine_gh.append(item[4])
            elif item[3] == "jira" and item[1] in kinds and age(item[0]) >= args.jira_min_age:
                mine_jira.append(item[4])
                d = item[5]
                ident = re.match(r"\[([^\]]+)\]", item[4]).group(1)
                review.append("### %s@%s\n%s (status: %s)\nAsked %s by %s: %s\nComments after it: %s\n" % (
                    ident, ping(key).lstrip("@"), d["title"], d["status"], d["asked"][0].date(), d["asked"][1],
                    d["asked"][2],
                    "".join("\n- %s %s: %s" % (w.date(), a, one_line(t, 400)) for w, a, t in d["later"]) or "none"))
        if mine_gh:
            github.append("- %s: %s" % (ping(key), " · ".join(mine_gh)))
        if mine_jira:
            jira.append("- %s: %s" % (ping(key), " · ".join(mine_jira)))
    if args.review:
        return ("Jira candidates to check before the report is shown. Drop one with "
                "--exclude KEY@name (or KEY for everybody).\n\n" + "\n".join(review or ["none\n"]))
    out = ["# SEC: what we are waiting on (%s)" % NOW.date(), "", "## GitHub reviews", ""]
    out += github or ["none"]
    if not args.no_jira:
        out += ["", "## Jira: questions open for %d days or more" % args.jira_min_age, ""] + (jira or ["none"])
        mine = "resolution = Unresolved AND statusCategory != Done AND (assignee = currentUser() OR comment ~ currentUser()) ORDER BY updated DESC"
        out += ["", "Please also check your own list: [my open openEHR tickets](%s)." % mine_link(mine)]
        if args.top and not args.person:
            projects = ", ".join(CONFIG["jira_projects"])
            jql = ("project in (%s) AND resolution = Unresolved AND statusCategory != Done "
                   "ORDER BY priority DESC, updated DESC" % projects)
            # pinned tickets first (SEC project tickets are not public, so they come from the config)
            pinned = CONFIG.get("pinned_attention", [])[:args.top]
            out += ["", "## Special attention: highest priority", ""]
            for pin in pinned:
                out.append("- [%s](%s/browse/%s) %s (%s)" % (
                    pin["key"], CONFIG["jira_base"], pin["key"], md(pin["title"]), pin.get("priority", "pinned")))
            rest = args.top - len(pinned)
            top = jira_get("/rest/api/3/search/jql", {"jql": jql, "fields": "summary,priority", "maxResults": rest}) if rest else {}
            for issue in top.get("issues", []):
                f = issue["fields"]
                out.append("- [%s](%s/browse/%s) %s (%s)" % (
                    issue["key"], CONFIG["jira_base"], issue["key"], md(one_line(f["summary"], 90)),
                    (f.get("priority") or {}).get("name", "?")))
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=180, help="Jira: look at tickets and mentions of the last N days")
    ap.add_argument("--stale", type=int, default=14, help="bold the age from N days on")
    ap.add_argument("--person", help="only this person (part of name or GitHub login)")
    ap.add_argument("--no-jira", action="store_true", help="GitHub only")
    ap.add_argument("--full", action="store_true", help="detailed report: ages, who asked, reworks, PRs without reviewer, drafts")
    ap.add_argument("--all-mentions", action="store_true", help="short report: also Jira mentions that ask nothing")
    ap.add_argument("--jira-min-age", type=int, default=14, help="short report: Jira questions from N days on (default 14)")
    ap.add_argument("--everyone", action="store_true", help="short report: also people outside the SEC team")
    ap.add_argument("--top", type=int, default=5,
                    help="short report: closing list of the N open tickets with the highest priority (0 = off)")
    ap.add_argument("--review", action="store_true",
                    help="short report: print each Jira candidate with the full question and later comments, for checking")
    ap.add_argument("--exclude", help="short report: comma list of items to leave out, KEY or KEY@name (e.g. SPECPR-470@vidi42, AM#43)")
    ap.add_argument("--out", help="write the Markdown report to this file instead of stdout")
    args = ap.parse_args()

    people = People()
    members = gh_graphql(TEAM_QUERY, org=CONFIG["org"], team=CONFIG["sec_team"])
    sec_logins = []
    for m in members["organization"]["team"]["members"]["nodes"]:
        people.add_github(m["login"], m.get("name"))
        sec_logins.append(m["login"])

    args.sec_logins = set(sec_logins)
    waiting = defaultdict(list)
    sections = defaultdict(list)
    scan_github(people, sec_logins, waiting, sections)
    if not args.no_jira:
        scan_jira(people, waiting, sections, args.days)

    report = render(people, waiting, sections, args) if args.full else render_short(people, waiting, args)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8", newline="\n")
        print("written: %s" % args.out)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(report)


if __name__ == "__main__":
    main()
