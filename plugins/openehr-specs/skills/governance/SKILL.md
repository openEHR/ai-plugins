---
name: governance
description: >
  Manage openEHR specification governance: releases, change requests (CR/PR), versioning, and
  lifecycle states (Planning, Development, Trial, Stable, Paused, Retired). This skill should be
  used when the user asks to create, tag, or fix a release, update release entries in
  `manifest.json`, raise or progress a CR/PR, classify a change as a Fix, Minor change or Change
  Request, promote a spec's status, propose a new spec, or explain the SEC change process. Not
  for amendment entries (amendment-record), pre-release document review (review), local previews
  (authoring), or clinical/archetype governance.
---

# openEHR Specification Governance

This skill covers the change process, release management, and lifecycle governance for
openEHR specifications. It is based on the official governance documents at
specifications.openehr.org/governance.

**Change workflow trial.** On 2026-11-09 the SEC approved a new change workflow as a one-month
trial, until 2026-12-09: every change to a Trial or Stable specification is a Fix, a Minor
change or a Change Request, decided by approvals on the pull request or, for Change Requests,
by an SEC vote. Follow it; the published Change Process page still describes the earlier
process. The full rules are in `references/change-workflow.md`.

## Related Skills

- **authoring** — document scaffolding, repo layout, boilerplate structure
- **amendment-record** — detailed amendment record authoring conventions
- **review** — pre-release quality review of spec documents (the `spec-reviewer` and `xref-auditor` subagents run it across a whole spec or component)

## Specification Lifecycle States

Every specification follows a formal lifecycle:

```
Planning → Development → Trial → Stable
                                    ↓
                                  Paused → Retired
```

| State | Duration | Format | Versioning | Change Management |
|-------|----------|--------|------------|-------------------|
| **Planning** | 6 months max | Wiki | 0.y.z | Informal |
| **Development** | 18 months max | Wiki | 0.y.z | Optional CRs |
| **Trial** | 2 years max | HTML + computable | x.y.z | Formal CRs |
| **Stable** | Unbounded | HTML + computable | x.y.z | Formal CRs |
| **Paused** | Unbounded | HTML + computable | paused | CRs only for state changes |
| **Retired** | Unbounded | Frozen version | n/a | None |

The Specifications Editorial Committee (SEC) reviews promotion criteria three months before
target dates. Unmet criteria may trigger a single three-month extension; subsequent failure
results in retirement.

The `spec_status` field in `manifest.json` and `manifest_vars.adoc` carries this state in upper case (for example `DEVELOPMENT`, `TRIAL`, `STABLE`, `PAUSED`, `RETIRED`; the full list is in `../authoring/references/manifest-spec-entry.md`). Keep both copies identical. To promote a spec, confirm that the SEC has approved the promotion, then set `spec_status` identically in both files.

## Versioning

openEHR uses three-part semantic versioning (`x.y.z`):

- **Patch (z)**: Error corrections and minor additions that do not change semantics
- **Minor (y)**: Significant additions that do not change existing semantics
- **Major (x)**: Semantic changes requiring potential software upgrades or data migration

Documentation-only corrections (typos, clarifications) receive a revision number update
without triggering a new release number.

## Artifact Types

### Problem Reports (PRs)

- Raised by **anyone** on the public `SPECPR` Jira tracker
- Document issues, bugs, or requirements against existing specifications
- Any SEC member can pick a PR up at any time; there is no fixed review round
- Reference format in specs: `{spec_tickets}/SPECPR-NNN[SPECPR-NNN^]`

### Change Requests (CRs)

- Created **only by SEC members** on component-specific Jira trackers (e.g., `SPECRM`, `SPECAM`)
- Each CR documents a specific modification to one or more specifications
- CRs reference the PRs they address
- Reference format in specs: `{spec_tickets}/SPECRM-NNN[SPECRM-NNN^]`
- If the user is not an SEC member, direct them to raise a PR on the `SPECPR` tracker instead

## Change Workflow

Three levels, sized to the change. Small changes are decided on the pull request; only Change
Requests go to an SEC vote. Details, qualifying lists and the vote rules:
`references/change-workflow.md`.

| | Fix | Minor change | Change Request |
|---|---|---|---|
| What | A correction, or a new entry in a list meant to grow | Compatible: everything that conforms today still conforms | New in kind, or breaking |
| Ticket | Problem Report, optional | Problem Report | Change Request (SEC members only) |
| Decided by | One SEC approval on the pull request | Two SEC approvals, then one week's notice on Discourse; a veto moves it up to a Change Request | SEC vote, then three SEC approvals on the pull request |

Classify in two steps: a correction or a new entry in a list meant to grow is a **Fix**; a
compatible change that adds nothing new in kind is a **Minor change**; everything else is a
**Change Request**. The size of the diff does not matter, and when in doubt go one level up.
An SEC member who disagrees with the level moves the change up before the merge; nobody can
block a change alone.

A Change Request goes: candidate solutions, an optional 30-day ballot on Discourse for an
impactful change, the SEC vote (at least half of the members present and two-thirds of those
in favour, or two-thirds of the members on the ticket), then a pull request with three SEC
approvals confirming the text matches the vote.

Releases are not voted on. A minor or major release goes to a 30-day community ballot on
Discourse before it is published; a patch release does not. Label pull requests `fix`,
`minor` or `change-request` so the SEC can list them.

When one change needs pull requests in several repositories (text, BMM, schemas, OpenAPI), the
one with the specification text is the **collection pull request**: it lists the others, they
link back, approvals are given on it once and count for all, and the SEC votes once on the
Change Request, never per pull request. Merge them together, the collection last.

**Release allocation.** When you open a pull request, set the Fix Version of its ticket (Problem
Report or Change Request) to the next planned release of every component the pull request
touches, one per component: on `SPECPR` the per-component versions (`AM version 2.4.0`,
`RM Release 1.2.0`), on a component tracker its own (`Release 1.2.0`, `ADL 2.4.0`). Three pull
requests for one Problem Report, in three components, give it three Fix Versions: add the one
for your component, keep the others. It is the default; anyone may move the ticket out of a
release later by changing it. Pick the lowest unreleased version of the component; ask when
more than one is open and the choice is not obvious.

### Jira Ticket Flow: Resolve → Release → Close

A CR or PR ticket is closed in two steps, never straight from Open or Analysis:

0. **Allocate** when the pull request is opened: set the Fix Version to the next release of each
   component the pull request touches (Release allocation above). Resolve only confirms it.
1. **Resolve** when the change is merged: walk the ticket to Resolved (Approve transition,
   resolution Done or Fixed) with the Fix Version set to the release that will carry the
   change. Comment with the merged PR (tracker-writing skill).
2. **Release**: the ticket stays Resolved until that component release is published (see
   Release Process). The release's Jira saved searches list these Resolved tickets.
3. **Close** after the release is deployed. Closing earlier drops the ticket from the release
   lists and hides that the change is still unreleased.

The SPEC CR trackers' workflow, with the transition names and the fields each one requires:

| Transition | From → To | Set on the way |
|---|---|---|
| Assign | Open → Analysis | Affects Version/s, Fix Version/s, Analyst |
| Commence | Analysis → In Progress | Due date, Priority, Impact Analysis (and Fix Version/s if still empty) |
| Start Review | In Progress → In Review | Change Description (what changed, with the PR link) |
| Approve | In Review → Resolved | resolution Done or Fixed; SEC members record their vote in the Acceptance field first |
| Closed | any → Closed | nothing; use only after the release |

Impact Analysis and Change Description are rich-text fields: via the API they take an ADF
document, not a plain string. Set every field in the table even when a transition does not
force it, so the ticket reads the same as the others in the tracker. A direct "Closed"
transition exists from every state; do not use it before the release, and never from Open or
Analysis, which leaves the ticket without Fix Version, resolution and change description.

## Release Process

Releases organize changes by component. The SEC defines release identifiers and delivery
dates, allocating CRs to releases.

### Release Naming

- Releases: `Release-N.N.N` (e.g., `Release-1.0.4`)
- Fix releases: `Release-N.N.NvM` (e.g., `Release-1.0.4v1`) — for post-release corrections

### Steps to Create a Release

Read `references/release-checklist.md` for the full step-by-step checklist.

The high-level process:

1. **Jira** (a user task, not doable from the repo): ask the user to confirm that all CRs and PRs for the release are Resolved (not yet Closed, see "Jira Ticket Flow") and the saved searches exist, then continue.
1. **Ballot** (minor and major releases): draft the Discourse post from `references/ballot-post.md` for the user to publish; wait for the 30 days to pass and the comments to be answered before tagging.
2. **manifest.json**: Set the release date, verify `spec_status` for each spec, ensure Jira links are correct, and prepend the next-cycle `releases` entry with an empty `date`.
3. **Git**: Create a release branch (`Release-N.N.N`), publish in release mode with the exact command in the checklist (do not use `/openehr-specs:publish`; it builds previews only), commit, and create the annotated tag. Ask the user before pushing.
4. **Webhook**: The push triggers the specifications.openehr.org server to pull and deploy.
5. **Jira** (a user task): once deployed, close the Resolved CRs and PRs that carry this Fix Version.

### Steps to Fix a Release

Follow the Fix Release section of `references/release-checklist.md`.

## Creating a New Specification

New specifications are proposed via PR or CR. The SEC verifies:
- Identifier assignment (the `id` field)
- Structural placement within the specification library
- Scope consistency with existing specifications
- Component location

To scaffold the document and its `manifest.json` entry once identifier and placement are agreed,
follow the **authoring** skill ("Creating a New Specification Document").

### Required Structure

All specifications must include:
- Front matter: identifier, version, amendments, copyright
- Introduction: purpose, related documents, status, tools, change history
- Main content
- References
- Internationalization considerations (where relevant)

### Entry Paths

1. **Mature external offering**: SEC assesses maturity; may start at Trial or Stable
2. **New development**: Starts at Planning state with 0.y.z versioning

## Roles

| Role | Responsibility |
|------|---------------|
| **SEC** (Specifications Editorial Committee) | Decides Change Requests by vote, defines releases, promotes specs |
| **SEC members** | Approve Fixes and Minor changes on the pull request, vote on Change Requests, raise Change Requests |
| **Component Maintainer** | Supervises component specs |
| **Community** | Raises PRs, comments in release ballots and on announced Minor changes on Discourse |
