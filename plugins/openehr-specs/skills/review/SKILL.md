---
name: review
description: >
  Review an openEHR specification document for quality, completeness, and convention compliance in
  `specifications-XX` repos. This skill should be used when the user asks to review, lint, or
  quality-check an openEHR spec or chapter, validate its conventions, or run a pre-release review.
  Not for prose-style advice (use content-patterns), archetype/template review (openehr-assistant
  plugin), the governance process (use governance), or non-openEHR documents.
---

# openEHR Specification Document Review

Review an openEHR specification document against the conventions used across all
`specifications-XX` repositories.

## Review Process

1. **Identify the target** — determine the spec directory (e.g., `docs/ehr/`) and read the key files
2. **Run each check category** — work through the full catalog in `references/check-catalog.md`,
   collecting findings as ERROR, WARNING, or INFO
3. **Present findings** grouped by category with `file:line` references
4. **Propose fixes** for ERRORs and WARNINGs (only modify files if asked)

## Inline Review or Subagent

Choose by scope:

- **Review inline** for one chapter, one file, or a few files. Apply only the checks those files
  allow and state which checks were skipped.
- **Dispatch the `spec-reviewer` subagent** for a whole spec directory, a whole component, or a
  pre-release review. It runs this same catalog in an isolated context and returns only the findings table.
- **Dispatch the `xref-auditor` subagent** when the concern is links. XREF-01 to XREF-04 only check
  that attributes are defined and links are styled; the subagent also resolves `<<anchor>>` targets
  and, with web access, cross-spec `#fragment` anchors.
- **Dispatch the `identifier-grounding` subagent** to verify that class, attribute, and function
  names exist in the published specifications. No check in this catalog does this.

## Pre-Review: File Discovery

Read these files for the target spec:
- `master.adoc` — main entry point
- `manifest_vars.adoc` — per-document variables
- `master00-amendment_record.adoc` — amendment record
- `master01-preface.adoc` — preface
- Every chapter file in scope (`master02-*.adoc`, etc.); search all chapters for the pattern checks (FIG, ADOC, XREF, CONTENT) rather than sampling
- The component's `manifest.json` (in the repo root)

Also reference the shared infrastructure in the sibling `specifications-AA_GLOBAL` checkout (if it is absent, skip XREF-01 and say so):
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
| 7 | Manifest Consistency (MAN) | `manifest.json` entry present and consistent with `manifest_vars.adoc` |
| 8 | Content Quality (CONTENT) | Chapter headings, Overview sections, TBD and deprecated inventories |

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

List failing checks only, unless the author asks for passing checks too.

Follow with a summary:
- Total: N findings (E errors, W warnings, I info)
- Recommended actions (grouped, prioritised)

Route fixes: AMEND-* to the `amendment-record` skill, ADOC-03 to `class-generation`, XREF-* to
`../authoring/references/cross-references.md`.

## Scope Boundaries

- Review only the AsciiDoc sources of openEHR specifications in `specifications-XX` repositories (RM, AM, BASE, LANG, PROC, SM, QUERY, CNF, TERM, ITS-*). Derive every finding from the catalog.
- Do not review archetypes, templates, AQL queries, the governance process, or non-openEHR documents.
- Do not modify files; report findings for the author to act on, unless asked to fix them.
- Run static checks only. Missing includes or images show up in a build, so tell the author to run `/openehr-specs:publish` (user-invoked) to surface Asciidoctor warnings.
