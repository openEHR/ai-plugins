---
name: sec-waiting
description: >
  Read-only reminder list for the openEHR Specifications Editorial Committee (SEC): who are we
  waiting on, and for what. Lists per SEC member the pull request reviews requested from them
  and the open Jira tickets where they were asked a question and have not answered, as a short
  message ready to paste into Discourse. Use when the user says "sec status", "what are we
  waiting on", "who owes a review", "pending reviews", "reminder for the SEC", or wants the
  list for one person. Not for writing the Jira or pull request text itself (use
  openehr-specs:tracker-writing).
argument-hint: "[person] [--no-jira] [--full]"
allowed-tools:
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/sec_waiting.py *)"
---

# SEC waiting list

## Rule 1: read only

The skill only reads GitHub and Jira and prints a list. It never comments, pings, requests a
review, or posts the list anywhere. Posting it (Discourse, Jira, mail) needs a separate
instruction from the user; then use `openehr-specs:tracker-writing` for the text.

## Rule 2: check before you show

The script finds candidates by rule; it cannot read. Never show its report unchecked. An entry
may only be in the message when all of this holds:

1. **The ticket or pull request is open.** No closed, resolved, done or merged item is linked.
2. **The person was pinged and asked something.** The comment @mentions them and puts a
   question or a request to them ("is this still relevant?", "please review", "do you agree").
   Being named is not enough: "agree with @x", "per @x", "thanks @x", "@x was right" are out.
3. **The question is still open.** The person has not answered, and nobody else has settled it
   in a later comment (someone else answered the question, the asker withdrew it or decided,
   the ticket moved on).

When in doubt, leave the entry out. A missing reminder costs less than a wrong ping.

## Steps

```
python3 ${CLAUDE_SKILL_DIR}/scripts/sec_waiting.py --review
```

1. Run with `--review`. It prints every Jira candidate as `### KEY@name` with the ticket
   status, the full comment that pinged the person, and all comments after it.
2. Judge each candidate against Rule 2. Collect the ones that fail as `KEY@name` (or `KEY` to
   drop a ticket for everybody).
3. Run again without `--review`, with `--exclude "KEY@name,KEY@name,..."`. Check that no
   excluded entry is left.
4. GitHub reviews come from GitHub's own review-request state, so they need no reading. Only
   check that the report lists no pull request that was merged or closed in the meantime.
5. Show the report in a code block, then one line per dropped entry with the reason
   ("SPECAM-83@jane.doe: named, not asked").

Needs `python3` (3.8+, standard library only) and the `gh` CLI, logged in with an account that
can read the `openEHR/sec` team. Jira is read through the public REST API without a login, so
restricted tickets are not seen. If `python3` or `gh` is missing, say so and stop. In a tool
that does not set `${CLAUDE_SKILL_DIR}`, use the directory that holds this SKILL.md.

| Option | Meaning |
|---|---|
| `--review` | print the Jira candidates with full context, for the check above |
| `--exclude <list>` | leave these out: `KEY@name` or `KEY`, comma separated; pull requests as `AM#43` |
| `--person <name or login>` | only this person |
| `--no-jira` | GitHub only (fast) |
| `--everyone` | also people outside the SEC team |
| `--jira-min-age N` | Jira questions open for N days or more, default 14 |
| `--all-mentions` | also Jira mentions the keyword check rates as "asks nothing" |
| `--days N` | Jira window for tickets and mentions, default 180 |
| `--top N` | length of the closing priority list, default 5; 0 turns it off |
| `--full` | detailed report instead: ages, who asked, excerpts, reworks, merges, pull requests without a reviewer, drafts, tickets per assignee; everyone, not only the SEC. Unchecked; say so when showing it |
| `--out <file>` | write the report to a file |

## The message (default report)

Made to be pasted into a Discourse post as a reminder.

- One line per person, sorted by name: `@discourse.username: link · link`. A pull request or
  ticket that waits on several people appears under each of them.
- Only members of the GitHub team `openEHR/sec`. People outside the SEC were already pinged in
  Jira and are not pinged again in a SEC reminder (`--everyone` adds them).
- GitHub reviews: every open review request, whatever its age.
- Jira: only questions open for 14 days or more. Fresh questions are left out, so the reminder
  does not nag. The closing link lets each member check all their own tickets.
- Last section "Special attention: highest priority": the 5 open SPEC* tickets with the highest
  Jira priority, most recently updated first within a priority, with title and priority, no
  pings. It is a plain sort by the Jira priority field; if a ticket there looks stale or
  wrongly rated, say so below the report instead of dropping it.
- Discourse limits the number of users one post may mention (default 10). If the report pings
  more, tell the user and offer to split it into a GitHub post and a Jira post.

## Configuration

`config.json` in the skill directory holds the scope: the GitHub organisation and SEC team,
the repositories (`specifications-*` plus `adl-antlr`, `terminology`, `antora-openehr`,
`ai-plugins`) and the SPEC* Jira projects. It ships without any personal data.

Personal settings go in a second file of the same shape, merged over it: the path in the
environment variable `SEC_WAITING_CONFIG`, or `config.local.json` next to `config.json` (lost
when the plugin updates, so prefer the variable). Keep that file out of public repositories:
it joins people's accounts across platforms.

| Key | Content |
|---|---|
| `discourse_names` | GitHub login → Discourse username, so the message pings the person. Without an entry the plain name is printed; look the username up on discourse.openehr.org and add it |
| `discourse_by_name` | display name → Discourse username, for people without a SEC GitHub login |
| `github_names` | GitHub login → name as written in Jira, when the two differ |
| `jira_names` | Jira display name → the name to use, when the two differ |
| `pinned_attention` | tickets listed first in "Special attention", each `{"key", "title", "priority"}`. For tickets the script cannot see, such as those of the non-public Jira project SEC. They count towards the 5 |

Before showing a report with pinned tickets, check with the Atlassian MCP, if connected, that
each one is still open and that no critical ticket of the SEC project is missing; tell the
user what to change in their file.

## How the script finds candidates

| Kind | Source | Rule | Waiting on |
|---|---|---|---|
| Review | GitHub | review requested and not yet given | the reviewer |
| Answer | GitHub, Jira | @mentioned in a comment that looks like a question (keyword check); the person has not commented since | the person mentioned |
| Mention | GitHub, Jira | same, but the comment asks nothing | nobody; `--full` and `--all-mentions` only |
| Rework | GitHub | latest review is "changes requested", review not re-requested | the pull request author; `--full` only |
| Merge | GitHub | approved, no open request, not merged | the pull request author; `--full` only |

- Jira tickets count as open when they are unresolved and not in a Done status. Some closed
  tickets carry no resolution, so the resolution alone is not enough.
- "Has answered" is matched by name, not by account: some people have two Jira accounts and
  are mentioned on one while answering from the other.
- GitHub and Jira identities are joined by name; fix a mismatch in `github_names` or
  `jira_names`.
- Bots and draft pull requests are skipped.

## Limits

- An answer given outside the ticket or pull request (call, Discourse, another ticket) is not
  seen.
- A question the keyword check rates as "asks nothing" never reaches the review step; run
  `--all-mentions --review` now and then to see what it hides.
- Inline review comments on GitHub are not scanned for mentions.
