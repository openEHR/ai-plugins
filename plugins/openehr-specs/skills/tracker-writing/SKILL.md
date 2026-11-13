---
name: tracker-writing
description: >
  Write Jira issues, Jira comments, and GitHub pull request titles and bodies for the openEHR
  specification trackers and repos. Use whenever text is about to be posted to Jira or GitHub:
  create or edit an issue, comment, open a PR, write a review comment. Issues and PRs open with
  a capped summary, then a Details part of at most 5 to 7 minutes' reading; comments stay
  summary only. Fixed structure, ask before going over. Not for commit messages (repo AGENTS.md),
  amendment entries (amendment-record), or spec prose (authoring, content-patterns).
argument-hint: "[issue | comment | pr] - what the text is about"
---

# Tracker Writing: Jira issues, comments and pull requests

Text posted to a tracker is read by busy SEC members on a phone, in a notification, or in a
list of fifty issues. Every word they do not need costs attention. This skill gives every
Jira issue and GitHub PR the same two parts: a short **summary** for everyone who scans it, and
**Details** for the person who has to decide, review or implement. Comments are summary only.

## Style

- **Clear.** One idea per sentence. Say what is wrong, where, and what should change.
- **Precise.** Name the class, attribute, section or file. Quote the exact wording in question.
  Never paraphrase a spec statement when the exact words fit.
- **Consistent.** Same structure every time, same order of parts, same labels. A reader who has
  seen one of our tickets can scan the next one.
- **Not wordy.** No preamble, no restating what the reader already sees (the title, the diff,
  the parent ticket), no "please note", no closing thanks, no explanation of how the text was
  produced. Facts and asks only.

## Hard caps

| Text | Cap | Counted on |
|---|---|---|
| Jira issue, summary part | **120 words** | description field, everything above the Details heading |
| Pull request, summary part | **80 words** | PR description, everything above the Details heading |
| Details part (issue or PR) | **1,000 words** to aim for, **1,500 words** hard | everything below the Details heading; 5 to 7 minutes' reading |
| Jira comment / PR review comment | **40 words** | comment body; no Details part |
| Jira summary / PR title | **80 characters** | one line, no trailing period |

Counting: every whitespace-separated token is a word; a URL or an issue key counts as one.
Code spans count. Headings and list markers do not.

The caps are hard. The agent does not post text that exceeds them. When the content cannot
fit without dropping something the reader needs, follow **Over the cap** below.

## Over the cap

Some texts legitimately need more: a design proposal with options and a fallback, a
reproduction with several steps, a review that lists many defects. The rule is:

1. Draft the text in the short form first. Remove context, repetition and hedging before
   removing facts.
2. If it still does not fit, **do not post**. Show the user the draft with its word count and ask
   one question: post the long form as is, or drop named parts to fit the cap.
3. Post what the user chooses. Never cut silently, and never post a long form without that
   confirmation.

A long form that was approved keeps the same structure, opens with a one-line TL;DR, and keeps
each part to one paragraph.

This applies to comments and to the summary part. A Details part over 1,500 words is not posted
either: say what it holds and its word count, and ask whether to cut named sections, split the
topic into several tickets, or move the bulk to a linked page.

## Summary, then Details

A Jira issue and a pull request body have two parts, in this order:

1. **The summary part**: the structure given below for the text type, within its cap, with no
   heading above it. It stands alone: a reader who stops there knows the defect or the change,
   where it is, and what is asked.
2. **Details**: under a heading `Details`, everything that was prepared and that the reader
   needs in order to decide, review or implement, in readable form.

Details are for information, not for length:

- **Complete.** Every fact, quote, option and check that was prepared for this ticket or PR and
  that bears on the decision is there. The reader does not have to redo the analysis or ask
  what was looked at.
- **Precise.** Quote the exact spec wording with its location. Give the proposed wording or
  model change exactly. Name what was verified and how, and what was not verified.
- **Readable.** The sections below, each a short paragraph or a list. A table when two or more
  things are compared. No section repeats the summary or another section.
- **Not a bible.** No background the SEC already knows, no history of how the text was
  produced, no hedging, no restating the diff. Leave a section out when it has nothing to say.
  If the summary already says everything (a typo, a broken link), there is no Details part.

Sections, in this order, each only when it has content:

| Jira issue | Pull request |
|---|---|
| **Current state**: what the spec, model or schema says today, quoted, with location | **What changed**: by document or model area, not by file; old and new wording for a normative change |
| **Problem**: why that is wrong or insufficient, and what it causes | **Decisions**: the choices made where the ticket left room, and what was rejected and why |
| **Proposal**: the change in exact terms; with several options, a table of option, effect, drawback, and which one is recommended | **Impact**: level (Fix, Minor change, Change Request) and what is affected |
| **Impact**: level (Fix, Minor change, Change Request; see the governance skill) and what is affected: data, implementations, schemas, other documents | **Review**: what to look at first, what was checked (build, link check, schema check) with the result, and what was not checked |
| **References**: tickets, pull requests and threads, each a link with one phrase on what it adds | **Open**: what this PR leaves for later, with the ticket if there is one |

## Structure per text type

Use these parts, in this order, with these labels. Omit a part only when it is empty; never add
parts.

### Jira issue (problem report or change request)

```
<one sentence: what is wrong or what is asked>

Where: <spec> <release or branch>, <section or class.attribute>[, file path]
Change: <what the text or model should say instead, or the question to decide>
Origin: <PR, discussion, or ticket link, only if there is one>

Details
<Current state, Problem, Proposal, Impact, References: see "Summary, then Details">
```

Summary line: `<Spec>: <defect or change in five to ten words>`. Examples:
`EHR Extract: EXTRACT_SPEC.priority should be a coded value`,
`ADL2: single regex String constraint instead of value list?`.

A question to a person goes in the Change line as a plain question, not a paragraph. The
assignee is set in the field, not in the text.

Fields: when the issue is created, set **Component/s**, **Affects Version/s** and, when the
target release is known, **Fix Version/s**, if the location identifies them. Use only
components and versions that already exist in the target Jira project: list them first (for
example `GET /rest/api/3/project/<KEY>/components` and `.../versions`) and pick from that list.
Never create a component or version, and leave the field empty when no existing value clearly
fits.

### Jira comment

Summary only, 40 words, never a Details part. When a comment needs more, it is usually
information that belongs in the issue description: propose to add it there, or follow
**Over the cap**.

```
<action or finding>. <reason, one sentence>.[ <ask, one sentence>]
```

Examples:
`Resolved Won't Do. SM component retired by SEC decision 2026-10-09.`
`Fixed by PR specifications-TERM #28 (merged 2026-10-16). Resolving.`
`Proposal: remove the five service classes from the RM; fallback is P_BMM_INTERFACE. Remove, or interface?`

Mention a person with @ only when their answer is needed.

### Pull request

Title: `<KEY>: <what changed>` for one ticket, `<KEY1>/<KEY2>: ...` for several, or
`<what changed> (editorial)` when there is no ticket. Match the commit convention in the repo's
`AGENTS.md` when it differs.

Body:

```
<what changed, one or two sentences>
Why: <ticket key with link, or the reason when there is no ticket>
Amendment record: <entry n.n added | not needed: <reason>>
[Check: <one thing the reviewer must verify, only if not obvious from the diff>]

## Details
<What changed, Decisions, Impact, Review, Open: see "Summary, then Details">
```

When one change needs pull requests in several repositories (see the governance skill,
`references/change-workflow.md`, "One change, several pull requests"), add after `Why:`:

- in the collection pull request:
  ```
  **Collection PR.** Approving this PR approves the whole change; the related PRs need no approvals of their own, only a check that they match. Merge all together, this one last.
  Related:
  - <full URL of each other pull request> (<what it changes>)
  ```
- in each other pull request:
  ```
  Part of collection PR <full URL>: approve there. This PR needs no approval of its own, only a check that it matches; it is merged together with the collection.
  ```

Use full URLs: a bare `repo#N` without the owner does not link across repositories, and GitHub's
`closes`/`fixes` keywords close issues, not pull requests. These lines belong to the summary
part and do not count toward the cap.

Do not list the changed files, the diff shows them; in Details, describe the change by document
or model area. Do not add a checklist unless the reviewer has to tick something.

### PR review comment

Same form as a Jira comment: the defect, the fix, in one or two sentences. Quote the line only
when the position does not identify it.

## Batches

When creating several issues or comments from one task (a clean-up sweep, a review with many
findings), the shared context is written once: in the first issue, in a parent or linking
ticket, or in the PR. Each individual issue carries only what differs: the location and the
specific point. Never repeat an origin paragraph or a question paragraph across a batch. The
same holds for Details: shared analysis is written once, and the other issues link to it.

## Before posting

- Word count within the cap, or the user has approved the long form.
- First line stands alone: a reader who stops there knows the defect or the action.
- Issue or PR: the summary part comes first and is complete without the Details. The Details
  hold everything that was prepared, are within 1,500 words, and no section repeats another.
- Comment: summary only.
- Every identifier (class, attribute, section, key, PR number) is one the agent has seen in the
  repo, the spec, or the tracker. No invented keys.
- No part repeats the title, the diff, or the parent ticket.
- Labels, assignee, component, priority are set in fields, not described in the text.

Worked before/after examples are in **`references/examples.md`**.
