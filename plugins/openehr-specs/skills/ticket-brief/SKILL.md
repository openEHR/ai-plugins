---
name: ticket-brief
description: >
  Read-only briefing for an openEHR specification Jira ticket: the ask, the current state
  checked against the spec repos, a two-line fix proposal, its level (Fix, Minor change or
  Change Request) and clearly related Jira, GitHub and Discourse items. Use when the user
  pastes a ticket key (SPECPR-483, SPECRM-46, SPECITS-96) or an openehr.atlassian.net URL, or
  asks "what is this ticket", "summarise SPECPR-x", "brief 475 476 478". Never changes
  anything. Not for writing the Jira or pull request text (use tracker-writing) or for the
  change process itself (use governance).
argument-hint: "<ticket key or URL> [more keys]"
---

# Ticket brief

## Rule 1: read only

This skill only reads and summarises. It never changes anything in Jira, GitHub, the spec repos
or Discourse: no comments, no links, no priority or status changes, no edits, no branches, no
pull requests. Every action after the brief needs a separate instruction from the user. When
the user then asks to post something, use the `tracker-writing` skill for the text.

## Input

- One ticket (key or URL): full brief.
- Several tickets: batch table (see below).

## Sources

| Source | Tool | What to fetch |
|---|---|---|
| Jira | Atlassian MCP if connected, site `openehr.atlassian.net`; else the public REST API (`https://openehr.atlassian.net/rest/api/3/issue/<KEY>`), which shows public tickets only | The issue with description and links, its comments, the Development field (linked pull requests), and one JQL `text ~ "<KEY>"` for tickets mentioning it |
| GitHub | `gh` CLI | `gh search prs "<KEY>" --owner openEHR` and `gh search issues "<KEY>" --owner openEHR`; `gh pr view` for any pull request found or linked |
| Discourse | Discourse MCP if connected; else WebFetch on `https://discourse.openehr.org/search.json?q=<KEY>` and on any Discourse URL in the ticket (`<topic-url>.json`) | Threads on exactly this ticket or its topic. Read the whole thread before calling anything agreed or disputed |
| Spec repos | `git grep` / `git show` on `origin/master` (run `git fetch -q origin` first) in the local `specifications-*` and `adl-antlr` clones, normally siblings of the current repository | The current text, BMM or grammar of the class, attribute, code or section the ticket names |

The spec repos are evidence for **State**. They are not listed under Related. If a source is
not available (no MCP, no `gh`, no clone of the repository concerned), say which one was not
checked; without the clone, read the published specification's Markdown twin instead and mark
State as checked against the published release, not `master`.

## Output: single ticket

```
**[<ticket title>](https://openehr.atlassian.net/browse/<KEY>)**

**Ask:** <one line: what the reporter wants or says is wrong>
**State:** <one or two lines: what master says today, with file or class reference; is the problem still there?>
**Fix (proposal):**
1. <what should change>
2. <where or how, or the split: what is a quick fix now vs. what needs its own ticket>
**Level:** <Fix | Minor change | Change Request>, <impact in a few words: who or what is affected, breaking or not>

**Related:**
- <Type>: [<item>](<url>) (<date or state>)
```

- Header: only the ticket title, as a clickable link. No key line, no type, priority, status or people.
- **Ask** is the reporter's request, not the discussion.
- **State** is checked against `origin/master`, never taken from the ticket text alone.
- **Fix (proposal)** is at most two lines. If the ticket mixes a text inconsistency with a redesign, line 1 is the fix of the inconsistency and line 2 says the redesign becomes its own SPECPR ticket (label `discussion`). Consistent spec first.
- **Level** rates the fix against the SEC change workflow, so the impact can be reviewed before
  anything is done. The rules and qualifying lists are in the `governance` skill
  (`references/change-workflow.md`); in short:
  - **Fix**: a correction, or a new entry in a list meant to grow (typo, schema or BMM bug, missing
    unit or term, class description). One SEC approval on the pull request.
  - **Minor change**: compatible; everything that conforms today still conforms, nothing new in
    kind (a cardinality relaxed, a class changed in the BMM, a small optional addition). Two SEC
    approvals, then one week of notice on Discourse.
  - **Change Request**: new in kind, or breaking (tightened constraint, removed or renamed element,
    new class, new dependency, data migration). SEC vote.

  The size of the diff does not matter; when in doubt, one level up. The level is also the label
  the pull request will carry (`fix`, `minor`, `change-request`). The impact part names what is
  affected: data, implementations, schemas or mirrors, other documents. For a non-fix outcome
  (Won't Do, Duplicate) write `n/a`.
- Add a **Discussion:** line between State and Fix only when there are comments with an open question, naming who asked what and whether it was answered.

### Related: clear relations only

Each entry starts with its type:

- `Fixed by`: a merged pull request or closed Change Request that already fixes the problem.
- `In progress`: an open pull request or Change Request working on it.
- `Duplicate of`: another ticket with the same request.
- `Discussed in`: a Discourse thread about exactly this ticket or topic, with the date of the last post.

No type, no entry. "Similar topic" is not a relation. If nothing qualifies, write `**Related:** none clear`. If something is `Fixed by`, the Fix proposal says "verify and resolve".

Every ticket key, pull request and thread is a clickable link.

## Output: several tickets

Quick mode, no topic search (only the ticket, its links, its Development field and `gh search` by key):

```
| Ticket | Status | Fix (proposal) | Level |
|---|---|---|---|
| [<title>](<url>) | <status>, <priority> | <one line> | <Fix / Minor / CR>, <impact> |
```

## Example

**[ADL 2 ARCHETYPE_HRID syntax: conflicting definitions](https://openehr.atlassian.net/browse/SPECPR-363)**

**Ask:** `concept_id` may end in `-`/`_` per Identification, but not per the ADL2 lexer; also split `LABEL` for URL vs HRID
**State:** contradiction gone: BASE Artefact Identification allows trailing `-`/`_`, and adl-antlr `LABEL` does too. Still open: 1-char concept (lexer `*` vs BASE `+`), `LABEL` not split
**Fix (proposal):**
1. Resolve Fixed once SPECBASE-50 and SPECAM-103 close; the main contradiction is already gone.
2. Raise the two grammar nits (1-char `concept_id`, `LABEL` split) as their own ticket for the ADL 2.4 grammar work.
**Level:** Fix, nothing changes for implementations; the grammar nits are a Minor change in adl-antlr

**Related:**
- Fixed by: [BASE PR #29](https://github.com/openEHR/specifications-BASE/pull/29), merged 16 Oct (SPECBASE-50 "resolves SPECPR-363")
- In progress: [SPECBASE-50](https://openehr.atlassian.net/browse/SPECBASE-50); [AM PR #41](https://github.com/openEHR/specifications-AM/pull/41) open (SPECAM-103)
