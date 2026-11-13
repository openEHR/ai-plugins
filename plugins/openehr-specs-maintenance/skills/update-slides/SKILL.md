---
name: update-slides
description: >
  Build the specification update decks as HTML slides: the SEC update for a Specifications
  Editorial Committee call, and the shorter Board update that is cut from it. Fixed sections,
  numbers pulled from GitHub and Jira, a share-safe check before anything leaves the machine,
  and a summary for the call notes. Use when the user says "make the spec update slides",
  "SEC update deck", "board update", "slides for the next call", or "update the numbers on the
  slides". Not for the call agenda (sec-agenda) or the reminder list (sec-waiting).
argument-hint: "<sec | board> <date of the meeting, YYYY-MM-DD>"
allowed-tools:
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/activity.py *)"
---

# Update slides

Two decks, one source. The **SEC update** reports the specification work to the SEC and asks
for decisions. The **Board update** is cut from the latest SEC deck for the board: fewer
slides, outcomes instead of process, no ticket-level detail. Both are a single HTML file
built on `${CLAUDE_SKILL_DIR}/assets/deck-template.html` (reveal.js from cdnjs, no build step;
in a tool that does not set the variable, use the `assets` directory next to this file).

Default location, unless the user names another: `spec-update/<date>/index.html` and
`board-update/<date>/index.html` in the current directory, one folder per meeting, so earlier
decks stay as they were.

## Rule 1: the user's content, the skill's frame

The skill gives the sections, the layout and the numbers. What the user is doing, planning or
negotiating comes from the user. Ask for each section's content; never fill one from guesses,
from an earlier deck, or from other material lying around. A section with nothing to report is
left out, not padded.

## Rule 2: share-safe

A deck gets passed on: as a file, a link, a screenshot, a summary in the call notes. Before a
deck is shown as finished, check it slide by slide, speaker notes included, and list what you
removed or want the user to decide on:

- **No per-person numbers.** Counts are for the group ("9 people commented"), never a ranking
  or a per-name split ("Jane 40, John 18"), and never the presenter's own share.
- **No strategy, money or negotiation.** Plans before they are announced, revenue or
  cost-sharing, partner or vendor deals, who has or has not answered a request, and board-level
  priorities stay out of the deck. Where the user wants to mention them, use one neutral line
  ("ranked against the strategy plan") and keep the substance for the meeting.
- **No private links.** No personal preview sites, private repositories, local paths,
  restricted Jira projects or Confluence pages that need a login, unless the audience has
  access and the user confirms.
- **Speaker notes are content.** They travel with the file. Notes hold what to say, not what
  must not be read.
- **Names** of people only where they own a workstream and agreed to be named; thanks are said,
  not written.

## Steps

1. **Meeting and audience.** Take the deck (SEC or Board) and the date. For a Board deck, find
   the latest SEC deck first; the Board deck feeds from it.
2. **Numbers.** Run the script for the reporting period (normally since the last update):

   ```
   python3 ${CLAUDE_SKILL_DIR}/scripts/activity.py --since <start of period> --until <end>
   ```

   It prints JSON: open Problem Reports, resolved in the period by resolution, newly raised,
   the oldest open one, and per month merged pull requests, resolved Problem Reports, Jira
   comments and people commenting. Put the date the numbers were pulled into the deck. Needs
   `python3` and a logged-in `gh`; Jira is read anonymously, so restricted tickets are not
   counted. Without the tools, ask the user for the figures and mark them as given.
3. **Content.** Walk the user through the sections below, one question per section. Keep
   their wording; shorten, do not embellish.
4. **Build** the deck from the template: copy it, keep the components, replace every
   `{{...}}`, delete the sample slides that are not used.
5. **Check** against Rule 2 and show the user the list of what was left out or needs a
   decision. Count the slides against the time slot: about one minute per slide.
6. **After the meeting**, on request: a short summary for the call notes (one bullet per
   section, numbers and links, nothing from Rule 2), to go into the "Specification status"
   section of the notes page (see `sec-agenda`). Publishing the deck itself, as an artifact
   or in a repository, is a separate decision of the user; run the Rule 2 check again first.

## SEC update: sections

In this order; each one or two slides.

| # | Section | What goes in | Component |
|---|---|---|---|
| 1 | Title | meeting and date, the topics in one line, presenter | title slide |
| 2 | Backlog | Problem Reports resolved in the period with the split by resolution, open before and after, still to screen; one or two lines on the approach | three stat tiles + list |
| 3 | Still open | what needs a pull request, a board decision, or an SEC decision, with ticket links | check list |
| 4 | Problems seen | process problems the work showed, each with a proposal or a question to the SEC | two columns |
| 5 | Activity | merged pull requests and Jira comments per month, people commenting; the current month against the year | two bar charts + comparison line |
| 6 | Workstreams | one slide per running workstream (for example conformance, publishing, tooling): status tag, what moved, what is open | list with tag |
| 7 | Goals | the goals until the next milestone, as a check list | big check list |
| 8 | Releases | what the next release needs, with the collection ticket, and the help asked for | list |
| 9 | Agenda | "any pressing topics?", then the points the SEC is asked to decide today | numbered list |
| 10 | Proposals | only when a proposal is up for decision: why, the options or levels, and what is asked by when | flow rows, table |

Section 10 is for a decision on the table, such as a change to the workflow. Present the
proposal from its own source pages and link them; the deck is not where the proposal is kept.

## Board update: sections

Cut from the latest SEC deck; five to seven slides, about six minutes.

| # | Section | Taken from the SEC deck |
|---|---|---|
| 1 | Title | the topics in one line |
| 2 | Backlog | the stat tiles; the approach in one line |
| 3 | Activity | the charts and the comparison line |
| 4 | Deliverables | one tile per workstream: status tag and one or two lines of outcome |
| 5 | Process | only when the SEC is changing how it works: today vs. proposed in two rows, and what is decided when |
| 6 | Goals | the same check list |

Leave out for the Board: ticket keys and links beyond one collection ticket, the "still open"
and "problems seen" detail, the agenda, and anything the SEC has not seen yet. A topic for the
Board that is not in the SEC deck comes from the user and still goes through Rule 2.

## Components in the template

| Component | Use for |
|---|---|
| Title slide | kicker with meeting and date, title, rule, subtitle, presenter |
| Stat tiles (`.stats`) | three numbers with a label; `.warn` for the one that needs attention |
| Bar charts (`.chart`) | monthly series; the data sits in the script block at the end, with its source and pull date |
| Comparison line (`.compare`) | two or three numbers that put the current period in context |
| Check list (`ul.check`) | open items and goals |
| Two columns (`.split`, `.two`) | problem and proposal side by side |
| Flow rows (`.flow`) | today vs. proposed, one row each |
| Levels table (`table.levels`) | comparing options or levels; `tr.key` marks the deciding row |
| Status tag (`.tag`, `.tag.amber`) | under way, released, ongoing |

Keep one idea per slide and no more than five bullets. Numbers carry their unit and period.
