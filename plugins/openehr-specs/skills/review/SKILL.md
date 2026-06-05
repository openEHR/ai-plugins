---
name: review
description: >
  Review an openEHR specification document for quality, completeness, and convention compliance in
  `specifications-XX` repos. This skill should be used when the user asks to review, lint, or
  quality-check an openEHR spec, validate its conventions, or run a pre-release review. Not for
  archetype/template review (openehr-assistant plugin), the governance process (use governance), or
  non-openEHR documents.
---

# openEHR Specification Document Review

This skill performs a structured review of an openEHR specification document against the
conventions used across all `specifications-XX` repositories.

## Review Process

1. **Identify the target** — determine the spec directory (e.g., `docs/ehr/`) and read the key files
2. **Run each check category** — work through the full catalog in `references/check-catalog.md`,
   collecting findings as ERROR, WARNING, or INFO
3. **Present findings** grouped by category with `file:line` references
4. **Propose fixes** for ERRORs and WARNINGs (only modify files if asked)

## Pre-Review: File Discovery

Read these files for the target spec:
- `master.adoc` — main entry point
- `manifest_vars.adoc` — per-document variables
- `master00-amendment_record.adoc` — amendment record
- `master01-preface.adoc` — preface
- At least 2-3 chapter files (`master02-*.adoc`, etc.)
- The component's `manifest.json` (in the repo root)

Also reference the shared infrastructure:
- `specifications-AA_GLOBAL/docs/boilerplate/global_vars.adoc`
- `specifications-AA_GLOBAL/docs/references/reference_definitions.adoc`

## Check Categories

Run all eight categories. The full check list — each with an ID, severity, and condition — is in
**`references/check-catalog.md`**; load it when performing a review.

| # | Category (ID prefix) | Covers |
|---|----------------------|--------|
| 1 | Document Structure (STRUCT) | `master.adoc` include order, required files, section scaffolding |
| 2 | Preface Completeness (PREF) | Purpose, Related Documents, Status, Feedback, Conformance |
| 3 | Amendment Record (AMEND) | `latest_issue` anchors, entry order, release boundaries, Jira refs |
| 4 | Cross-References (XREF) | `{openehr_*}` attributes resolve; display text + `^` markers; no hardcoded URLs |
| 5 | Figures and Diagrams (FIG) | `image::` `id=`/`align`, titles, `[.text-center]`, path attributes |
| 6 | AsciiDoc Conventions (ADOC) | Monospace class/attribute names, generated class tables, `[.tbd]`/`[.deprecated]` |
| 7 | Manifest Consistency (MANIFEST) | `manifest.json` entry present and consistent with `manifest_vars.adoc` |
| 8 | Content Quality (CONTENT) | Chapter headings, Overview sections, no hardcoded site URLs |

XREF checks use the attribute naming patterns in `../authoring/references/cross-references.md`.

## Output Format

Present findings as a table:

```
| ID | Severity | Location | Finding |
|----|----------|----------|---------|
| STRUCT-02 | ERROR | manifest_vars.adoc | Missing `:keywords:` attribute |
| AMEND-01 | ERROR | master00-amendment_record.adoc:5 | Missing `[[latest_issue]]` anchor |
| FIG-01 | WARNING | master03-overview.adoc:42 | Image directive missing `id=` |
```

Follow with a summary:
- Total: N findings (E errors, W warnings, I info)
- Recommended actions (grouped, prioritised)

## Scope Boundaries

- This skill reviews **openEHR specification documents** — the AsciiDoc sources in `specifications-XX` repositories (RM, AM, BASE, LANG, PROC, SM, QUERY, CNF, TERM, ITS-*)
- All checks are derived from conventions observed in the openEHR specification library and its shared infrastructure in `specifications-AA_GLOBAL`
- It does NOT apply to non-openEHR specifications, general AsciiDoc documents, or other standards
- It does NOT review archetypes, templates, AQL queries, or governance process
- It does NOT modify files — it reports findings for the author to act on (unless asked to fix)
