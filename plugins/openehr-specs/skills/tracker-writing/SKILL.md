---
name: tracker-writing
description: >
  Write Jira issues, Jira comments, and GitHub pull request titles and bodies for the openEHR
  specification trackers and repos. Use whenever text is about to be posted to Jira or GitHub:
  create or edit an issue, comment, open a PR, write a review comment. Hard length caps, a fixed
  structure per text type, ask before going over. Not for commit messages (repo AGENTS.md),
  amendment entries (amendment-record), or spec prose (authoring, content-patterns).
argument-hint: "[issue | comment | pr] - what the text is about"
---

# Tracker Writing: Jira issues, comments and pull requests

Text posted to a tracker is read by busy SEC members on a phone, in a notification, or in a
list of fifty issues. Every word they do not need costs attention. This skill makes every
Jira issue, Jira comment and GitHub PR short, structured the same way, and precise.

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
| Jira issue body | **120 words** | description field, all parts together |
| Pull request body | **80 words** | PR description |
| Jira comment / PR review comment | **40 words** | comment body |
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

## Structure per text type

Use these parts, in this order, with these labels. Omit a part only when it is empty; never add
parts.

### Jira issue (problem report or change request)

```
<one sentence: what is wrong or what is asked>

Where: <spec> <release or branch>, <section or class.attribute>[, file path]
Change: <what the text or model should say instead, or the question to decide>
Origin: <PR, discussion, or ticket link, only if there is one>
```

Summary line: `<Spec>: <defect or change in five to ten words>`. Examples:
`EHR Extract: EXTRACT_SPEC.priority should be a coded value`,
`ADL2: single regex String constraint instead of value list?`.

A question to a person goes in the Change line as a plain question, not a paragraph. The
assignee is set in the field, not in the text.

### Jira comment

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
```

Do not list the changed files, the diff shows them. Do not add a checklist unless the reviewer
has to tick something.

### PR review comment

Same form as a Jira comment: the defect, the fix, in one or two sentences. Quote the line only
when the position does not identify it.

## Batches

When creating several issues or comments from one task (a clean-up sweep, a review with many
findings), the shared context is written once: in the first issue, in a parent or linking
ticket, or in the PR. Each individual issue carries only what differs: the location and the
specific point. Never repeat an origin paragraph or a question paragraph across a batch.

## Before posting

- Word count within the cap, or the user has approved the long form.
- First line stands alone: a reader who stops there knows the defect or the action.
- Every identifier (class, attribute, section, key, PR number) is one the agent has seen in the
  repo, the spec, or the tracker. No invented keys.
- No part repeats the title, the diff, or the parent ticket.
- Labels, assignee, component, priority are set in fields, not described in the text.

Worked before/after examples are in **`references/examples.md`**.
