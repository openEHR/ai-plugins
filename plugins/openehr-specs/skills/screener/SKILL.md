---
name: screener
description: >
  Read-only personal screen of the openEHR specification work, in two parts: first what the
  user can close (their pull requests that have the approvals their level needs and, for a
  Minor change, the week of notice; Jira tickets to resolve or close), then who is waiting on
  them (review requests, unanswered questions, requested changes). Use when the user asks
  "what can I close", "what can I merge", "what is open for me", "is anybody waiting on me",
  "screen my PRs and tickets". Not for the SEC-wide reminder list
  (openehr-specs-maintenance:sec-waiting) or for one ticket in depth (ticket-brief).
argument-hint: "[--all] [--no-jira] [--login <github login>]"
allowed-tools:
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/screener.py *)"
---

# Screener

Two questions, in this order: **is there anything open that I can close**, and **where are
people waiting on me**. Closing comes first, because a merged pull request or a closed ticket
takes work off everybody's list.

## Rule 1: read only

The skill reads GitHub and Jira and prints a list. It never merges, approves, resolves,
closes, comments or pings. Each of those needs a separate instruction from the user, per
item; for the text use `tracker-writing`, for the ticket transitions `governance`.

## Rule 2: candidates, not verdicts

The script applies rules to what GitHub and Jira show. Before showing its report, check each
entry of part 1 and each "Answer" of part 2, and drop or annotate what does not hold:

- **Ready to merge, Minor change.** The script counts the week from the approval that
  completed the set. The workflow counts it from the announcement on Discourse, which the
  script cannot see: look for the announcement and a veto (Discourse MCP or search), or tell
  the user to confirm both.
- **Ready to merge, Major change.** Three approvals confirm the text; the SEC vote is on
  the Change Request ticket. Check that the vote is recorded there.
- **Resolve.** The pull request is merged and the ticket is open. Make sure the pull request
  implements the ticket and does not merely mention it (the script says when the key is in
  the description only), and that no other pull request for the ticket is still open.
- **Close / Fix Version missing.** Read the ticket; a Resolved ticket without a Fix Version
  needs the version, not closing.
- **Answer.** The comment must put a question or a request to the user that nobody has
  settled since. Being named is not enough.

When in doubt, keep the entry and say what is unverified. Report what you dropped and why.

## Steps

```
python3 ${CLAUDE_SKILL_DIR}/scripts/screener.py
```

1. Run the script. It screens for the logged-in `gh` user and takes the Jira name from the
   GitHub profile; pass `--jira-name "<name>"` when the two differ.
2. Check the candidates (Rule 2).
3. Show the report in its order: 1 what can be closed, 2 who is waiting on you, 3 not
   closable yet. Keep the links. Do not add advice the user did not ask for.
4. Offer nothing beyond the list. If the user then says "merge it" or "resolve it", that is
   a new instruction for exactly the items named.

Needs `python3` (3.8+, standard library only) and the `gh` CLI, logged in. Jira is read
through the public REST API without a login, so restricted tickets are not seen; the report
names the keys it could not read. If `python3` or `gh` is missing, say so and stop. In a tool
that does not set `${CLAUDE_SKILL_DIR}`, use the directory that holds this SKILL.md.

| Option | Meaning |
|---|---|
| `--all` | every open pull request in scope, not only the user's own (for whoever merges for others) |
| `--no-jira` | GitHub only (fast) |
| `--days N` | window for merged pull requests and Jira questions, default 90 |
| `--login <login>` | screen for another GitHub user |
| `--jira-name <name>` | display name in Jira, when it differs from the GitHub profile name |
| `--out <file>` | write the report to a file |

## What the script reports

### 1. What can be closed

| Entry | Rule |
|---|---|
| Pull request ready to merge | the user's open pull request, not a draft, no conflict, checks not failing, no changes requested, and the approvals its level label needs: `fix` 1, `minor` 2 and 7 days since the second approval, `major` 3 |
| Resolve | a ticket named by a pull request of the user that was merged in the window, and that is not yet Resolved or Done |
| Close | a Resolved ticket assigned to the user whose Fix Versions are all released |
| Fix Version missing | a Resolved ticket assigned to the user without a Fix Version |

The levels and their approvals are those of the SEC change workflow (`governance` skill,
`references/change-workflow.md`). Only approvals by members of the GitHub team `openEHR/sec`
other than the author count; if the team cannot be read, every approval counts and the report
says so. A pull request without exactly one level label is never ready: the report asks for
the label.

### 2. Who is waiting on you

| Entry | Rule |
|---|---|
| Review | a review is requested from the user and not yet given |
| Answer | the user is @mentioned in a comment that looks like a question, on a pull request or an open Jira ticket, and has not commented since |
| Rework | changes are requested on the user's pull request |

### 3. Not closable yet

Approved Minor changes still in their week, with the date it ends, and the user's other open
pull requests with what each one lacks (approvals, label, conflict, draft, failing checks,
who was asked to review).

## Configuration

`config.json` in the skill directory: the GitHub organisation and SEC team, the repositories
in scope (`specifications-*` plus `adl-antlr`, `terminology`, `antora-openehr`, `ai-plugins`),
the SPEC* Jira projects, the Jira statuses that count as resolved, and the approvals and
waiting days per level. Change the numbers there when the SEC changes the workflow.

## Limits

- The Discourse announcement and veto of a Minor change, and the SEC vote on a Change
  Request, are not visible to the script.
- An answer given outside the pull request or ticket (call, Discourse, another ticket) is not
  seen.
- GitHub and Jira identities are joined by name.
- Inline review comments on GitHub are not scanned for mentions.
