---
name: sec-agenda
description: >
  Draft the agenda page for the next openEHR Specifications Editorial Committee (SEC) call on
  Confluence, from the standard template, and carry over what the previous call left open:
  topics not reached, follow-ups of discussed topics, and unchecked action items. Use when the
  user says "draft the next SEC agenda", "new SEC call notes", "prepare the agenda for
  <date>", "carry over the open topics", or "add this to the next agenda". Not for the list of
  pending reviews and unanswered questions (use sec-waiting) or for Jira and pull request
  text (use openehr-specs:tracker-writing).
argument-hint: "<date of the call, YYYY-MM-DD> [topics to add]"
---

# SEC agenda

The SEC keeps one Confluence page per call, in the Specifications space
(`https://openehr.atlassian.net/wiki/spaces/spec`), titled `YYYY-MM-DD SEC call notes`. The
page is the agenda before the call and the minutes after it. This skill drafts the page for
the next call.

Needs the Atlassian MCP with write access to that space. Without it, give the user the draft
as text to paste, and say that nothing was created.

## Rule 1: draft first, write on a yes

Show the draft and the list of what was carried over, and create or change a Confluence page
only when the user confirms, or asked for the page to be created in the first place. Editing
the previous call's page (step 6) always needs its own yes. Never delete a page, a row or an
action item; a moved row is removed from the previous page only after it is on the new one.

## Rule 2: copy, do not invent

- People are Confluence mentions with an account id. Copy a mention from the previous page as
  it is; never make one up. Someone who is not on the previous page is written as a plain
  name, and the user is told to turn it into a mention.
- A topic keeps its presenter, its wording and its links when it moves. Shorten notes only to
  drop what was settled.
- A decision is carried over only as written on the previous page. If the notes do not say
  whether a topic was decided, ask.

## Steps

1. **Date.** Take it from the user. If none is given, look for "Next call" on the previous
   page; if that is missing too, ask. Do not derive it from the cadence.
2. **Previous page.** Find the latest call page: search the space for pages titled
   `SEC call notes` (older ones say `SEC Call notes` or name a face-to-face meeting), take the
   one with the latest date in its title before the new date, and read its full body as HTML.
   If a page for the new date already exists, work on that page instead of creating a second
   one, and keep everything already on it.
3. **Sort what is on the previous page** into the four groups under "What carries over".
4. **Draft** the new page from `${CLAUDE_SKILL_DIR}/assets/agenda-template.html` (in a tool
   that does not set the variable: the `assets` directory next to this file). Show the user
   the rows in order and, per row, why it is there (standing, follow-up, moved, new).
5. **Create** the page on a yes: same space and same parent as the previous page, title
   `YYYY-MM-DD SEC call notes`, wide content width. Read the page back and give the link.
6. **Previous page**, on a separate yes: remove the rows that moved, and add below the table
   "Only <topics> were discussed. All other topics were moved to the <link to the new page>."
   Leave the discussed rows, their notes and the action items as they are.

## The template

Sections in this order; nothing else. The page has no Address and no Call Link section.

| Section | Content |
|---|---|
| Date | the date of the call, as a Confluence date |
| Participants | an empty list; filled in during the call |
| AGENDA additions | only when topics were moved: "The topics below were moved from the <link to the previous page>, where only <topics> were discussed." |
| Discussion topics | a table: Time, Presenter / Suggested by, Issue, Notes |
| Action items | an empty task list |

The Notes cell of an agenda row holds what the SEC needs in order to decide, in two or three
bullets: the problem in one line, the proposal, and a last bullet starting "Decide:" when a
decision is asked for. Tickets and pull requests are links. The outcome is written into the
same cell during the call.

A longer report, such as the specification status, may get its own section between the table
and the action items after the call, as on the 2026-11-09 page.

## What carries over

Rows go into the table in this order:

1. **Standing rows**, on every agenda. Copy them from the previous page; if one is missing
   there, add it from the template.
   - *General*: check and work with the SEC board.
   - *Specification status*: presenter as on the previous page, Notes empty. The status is
     reported in the call and never copied from the last one.
2. **Follow-ups.** A topic that was discussed and left something open gets a row
   `<topic>: follow-up from <date>`. Its Notes list only the open points, each with its link:
   bullets marked "Open:", a trial or deadline that is still running, work sent offline
   ("discuss offline until the next meeting"), and every unchecked action item that belongs
   to the topic. A topic that was closed with a decision and has nothing open is not carried.
3. **Moved topics.** A row that was not reached moves as it is: presenter, issue, notes, in
   the old order.
4. **New topics** from the user, last, in the same row shape. If the user gives only a ticket
   or a pull request, read it and write the Notes bullets; keep to what the ticket says.

An unchecked action item that fits no topic gets its own follow-up row with its owner as
presenter. The Action items list of the new page starts empty: open items live in the
follow-up rows until they are done, so nothing is tracked twice.

Tell the user what was not carried and why (closed with a decision, action item ticked).

## Adding to an existing agenda

"Add this to the next agenda" means: find the page for the next call, append one row in the
shape above after the last topic, and change nothing else. Use the tool's node-level edit, not
a full-body replace, so that edits others made in the meantime are kept.

## Limits

- The skill reads only the previous page. Topics agreed elsewhere (Discourse, chat, a call)
  come from the user.
- It does not time-box the agenda. Fill the Time column only with what the user gives.
- It does not notify anyone. Announcing the agenda is a separate request.
