# Amendment Record — Detailed Conventions

Lookup tables and edge-case formatting for `master00-amendment_record.adoc`. The core workflow
(structure, anchors, entry order, version bump, checklist) is in the skill body; load this file
for Jira keys, release boundaries, multi-raiser formatting, grouping, and detail-text style.

## Jira References

### Syntax

```asciidoc
{spec_tickets}/SPECRM-87[SPECRM-87^]
```

The `{spec_tickets}` attribute resolves to the specifications site ticket URL.

### Project Keys

| Key | Type | Scope |
|-----|------|-------|
| `SPECPR` | Problem Reports | Cross-component |
| `SPECRM` | Change Requests | Reference Model |
| `SPECAM` | Change Requests | Archetype Model |
| `SPECBASE` | Change Requests | BASE |
| `SPECQUERY` | Change Requests | QUERY |
| `SPECPROC` | Change Requests | PROC |
| `SPECSM` | Change Requests | Service Model |
| `SPECLANG` | Change Requests | LANG |
| `SPECCNF` | Change Requests | Conformance |
| `SPECTERM` | Change Requests | Terminology |
| `SPECPUB` | Publishing Issues | Cross-component |

### Linking CRs and PRs

When a CR addresses one or more PRs, include both:

```asciidoc
{spec_tickets}/SPECRM-87[SPECRM-87^]: Support tags (Addresses {spec_tickets}/SPECPR-265[SPECPR-265^]).
```

Common phrasing:
- "Addresses" — the CR responds to the PR
- "Fixes" — the CR directly resolves the PR
- "See" — cross-reference to related ticket

## Release Boundary Rows

Release boundaries are marked with a full-width header row spanning all 4 columns:

```asciidoc
4+^h|*XX Release N.N.N*
```

Where `XX` is the component abbreviation (e.g., `RM`, `AM`, `BASE`) and `N.N.N` is the
release version. Place the boundary row **after** all entries belonging to that release
(i.e., above the entries from the previous release).

```asciidoc
|[[latest_issue]]5.2.1
|{spec_tickets}/SPECRM-87[SPECRM-87^]: Support tags...
|S Iancu
|[[latest_issue_date]]17 Nov 2022

4+^h|*RM Release 1.1.0*

|5.2.0
|{spec_tickets}/SPECRM-55[SPECRM-55^]. Add `_folders_` on `EHR`...
|B Naess, +
S Iancu
|23 Sep 2020
```

## Multi-Raiser Formatting

When multiple people are listed as raisers, separate them with `, +` (comma, space,
AsciiDoc line continuation):

```asciidoc
|S Iancu, +
B Naess, +
M Polajnar
```

Some older entries use `, +\n ` (with leading space on continuation lines) — both forms
are acceptable, but be consistent within a single amendment record file.

## Grouping Multiple Changes

When multiple CRs are applied in a single version increment, they can be:

**Option A: Single entry with multiple CRs** — when changes are closely related:
```asciidoc
|[[latest_issue]]5.2.1
|{spec_tickets}/SPECRM-87[SPECRM-87^]: Support tags. +
{spec_tickets}/SPECRM-88[SPECRM-88^]: Improve documentation of `_uid_` in versioning.
|S Iancu, +
T Beale
|[[latest_issue_date]]17 Nov 2022
```

**Option B: Separate entries sharing a version** — when changes are independent (leave Issue
column blank for subsequent entries):
```asciidoc
|[[latest_issue]]5.2.1
|{spec_tickets}/SPECRM-87[SPECRM-87^]: Support tags...
|S Iancu
|[[latest_issue_date]]17 Nov 2022

|
|{spec_tickets}/SPECRM-107[SPECRM-107^]: Add `inactive` and `abandoned` states...
|J Holslag
|12 Aug 2022
```

Option B is the more common pattern in existing specs.

## Detail Text Conventions

- Start with the Jira ticket reference, followed by a colon and description
- Use monospace for class names (`` `COMPOSITION` ``) and attribute names (`` `_uid_` ``)
- Use period (`.`) or colon (`:`) after the ticket reference — both are used in existing specs
- Keep descriptions concise but specific — state what changed, not why (the Jira ticket has the rationale)
- Reference section names or package names when the change is localised: "updated EHR model (<<rm_ehr>>); added <<tags>>"
- Use `+` (AsciiDoc line continuation) to separate multiple changes within one cell
