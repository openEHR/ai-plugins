---
name: amendment-record
description: >
  Author or update amendment records in openEHR specification documents: the
  `master00-amendment_record.adoc` table in `specifications-XX` repos. This skill should be used
  when the user asks to add or update an amendment entry, choose the document version bump, add a
  CR/PR reference, mark a release boundary, or fix the `latest_issue`/`latest_issue_date` anchors.
  Not for the ITS-REST amendment record (use its-rest), general spec authoring (use authoring), the
  release process (use governance), or non-openEHR documents.
argument-hint: "[SPECXX-NN[,SPECPR-NN] — one-line summary of the change]"
---

# openEHR Specification Amendment Record Authoring

The amendment record tracks every change to an openEHR specification document. It appears as
`master00-amendment_record.adoc` in each spec directory within the `specifications-XX`
repositories (RM, AM, BASE, LANG, PROC, SM, QUERY, CNF, TERM, ITS-*) and is included in
`master.adoc` after the front matter. The conventions here are specific to the openEHR
specification ecosystem and its Jira-based change management process. The `specifications-ITS-REST`
record is an HTML table, not this file; use the `its-rest` skill for it.

For detailed lookups — Jira project keys, CR/PR linking phrasing, release-boundary placement,
multi-raiser formatting, multi-change grouping, and detail-text style — see
**`references/conventions.md`**.

## File Structure

```asciidoc
= Amendment Record

[cols="1,6,2,2", options="header"]
|===
|Issue|Details|Raiser|Completed

|[[latest_issue]]N.N.N
|{Details of most recent change.}
|{Raiser name(s)}
|[[latest_issue_date]]dd Mon yyyy

|
|{Details of previous change.}
|{Raiser name(s)}
|dd Mon yyyy

4+^h|*XX Release N.N.N*

|N.N.N
|{Details of change in previous release.}
|{Raiser name(s)}
|dd Mon yyyy

|===
```

Fill the four columns as follows: **Issue** (version, only on the first entry of a group; blank for
subsequent entries in the same version), **Details** (change description + Jira refs),
**Raiser** (name(s)), and **Completed** (`dd Mon yyyy`).

## Critical Rules

### Anchors

Two anchors are **mandatory** and must appear on the **first (most recent) entry**:

- `[[latest_issue]]` — immediately before the issue version number
- `[[latest_issue_date]]` — immediately before the completion date

`doc_id_block.adoc` in the front matter references them to display the current revision and
date. If missing or misplaced, the front matter shows incorrect information.

```asciidoc
|[[latest_issue]]5.2.1
|{spec_tickets}/SPECRM-87[SPECRM-87^]: Support tags; ...
|S Iancu, +
B Naess
|[[latest_issue_date]]17 Nov 2022
```

### Entry Order

Order entries **most-recent-first**: insert each new entry at the **top** of the table, immediately
after the header row. Mark release boundaries with a full-width row — see
`references/conventions.md`.

### Column Format

- `[cols="1,6,2,2", options="header"]` — standard (no AsciiDoc markup in cells)
- `[cols="1a,6,2,2a", options="header"]` — when cells need AsciiDoc block content (lists, etc.)

### Jira References

Reference tickets as `{spec_tickets}/SPECXX-NNN[SPECXX-NNN^]` (the `{spec_tickets}` attribute
resolves to the site ticket URL). The full project-key table and CR↔PR linking phrasing are in
`references/conventions.md`.

## Version Numbering

The issue number tracks the **document version**, independent of the component release version
(a release may span multiple issue increments).

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| New content, new sections, semantic changes | Minor (x.**Y**.z) | 5.1.0 → 5.2.0 |
| Error corrections, typos, clarifications, formatting | Patch (x.y.**Z**) | 5.2.0 → 5.2.1 |
| Major restructuring or rewrite | Major (**X**.y.z) | 4.x.x → 5.0.0 |

## Direct Invocation

Run the checklist below from `/openehr-specs:amendment-record <SPECXX-NN[,SPECPR-NN] — summary>` or from
a plain request ("add an amendment entry for SPECRM-142"). Take the CR/PR key(s) and the change
description from `$ARGUMENTS`; when it is empty, take them from the user's message. Ask for anything
still missing. Example arguments:

```text
SPECRM-142 — add tags to LOCATABLE; addresses SPECPR-401
```

## Checklist for Adding an Entry

1. Locate the spec's `master00-amendment_record.adoc` (ask which spec when several are in scope) and read it to understand the current version and format. Ask the author for the raiser name(s) if not given, and copy the name style of the existing entries.
2. Choose the Issue number: bump patch, minor, or major per the table above, or reuse the top entry's number when the change ships in the same version increment (see "Grouping Multiple Changes" in `references/conventions.md`). If the right bump is unclear, state the assumed bump and proceed; the diff in step 8 lets the author correct it. Run `git -C <repo> status --short` and `git -C <repo> diff --stat` when the change is already in the working tree, so the entry describes what actually changed.
3. Add the new entry at the **top** of the table (after the header row)
4. Move `[[latest_issue]]` and `[[latest_issue_date]]` anchors to the new entry. When the version is reused, leave the Issue cell of the previous top entry blank.
5. Reference all relevant Jira CRs and PRs (see `references/conventions.md` for keys, phrasing, and detail-text style)
6. If this is the first entry after a release, add a release boundary row directly below the new entry, labelled with the release just completed (the newest release with a date in the `releases` array of `manifest.json`; ask the author if unsure)
7. Use today's date as the completion date unless the author gives one (ask if uncertain; do not guess), in the format `dd Mon yyyy` (e.g., `17 Nov 2022`)
8. When invoked directly, show the diff of the record (`git -C <repo> diff -- <record>`) and stop; do not publish or commit unless asked. Inside a larger flow (a release, an authoring task), return to that flow instead.
