# openEHR Specification Review — Check Catalog

The full check list for the `review` skill, grouped by category. Each check has an ID, a
severity (ERROR / WARNING / INFO), and the condition. Collect findings per category and report
them with `file:line` references.

XREF checks rely on the attribute naming patterns in `../authoring/references/cross-references.md`.

## 1. Document Structure (STRUCT)

| ID | Severity | Check |
|----|----------|-------|
| STRUCT-01 | ERROR | `master.adoc` exists and follows the canonical include order: `book_style_settings.adoc` → `manifest_vars.adoc` → `global_vars.adoc` |
| STRUCT-02 | ERROR | `manifest_vars.adoc` exists and defines all required attributes: `:spec_title:`, `:copyright_year:`, `:spec_status:`, `:keywords:`, `:description:` |
| STRUCT-03 | ERROR | `master00-amendment_record.adoc` exists |
| STRUCT-04 | ERROR | `master01-preface.adoc` exists |
| STRUCT-05 | WARNING | Chapter files are numbered sequentially (`master01-`, `master02-`, ...) with no gaps |
| STRUCT-06 | WARNING | `master.adoc` includes `reference_definitions.adoc` |
| STRUCT-07 | WARNING | `master.adoc` has Acknowledgements section with Editor, Contributors, Trademarks subsections |
| STRUCT-08 | WARNING | `master.adoc` ends with References section using `bibliography::[]` |
| STRUCT-09 | INFO | Front block choice is appropriate: `full_front_block.adoc` for primary specs, `short_front_block.adoc` for secondary/overview docs |

## 2. Preface Completeness (PREF)

| ID | Severity | Check |
|----|----------|-------|
| PREF-01 | ERROR | Preface contains `== Purpose` section |
| PREF-02 | WARNING | Preface contains `== Related Documents` section with prerequisite and related doc links |
| PREF-03 | ERROR | Preface contains `== Status` section with `{spec_status}` reference and development link |
| PREF-04 | WARNING | Preface contains `== Feedback` section with forum, PR tracker, and CR tracker links |
| PREF-05 | INFO | Preface contains `== Conformance` section (recommended for primary specs) |
| PREF-06 | INFO | Status section includes TBD example paragraph with `[.tbd]` role |

## 3. Amendment Record (AMEND)

| ID | Severity | Check |
|----|----------|-------|
| AMEND-01 | ERROR | Table has `[[latest_issue]]` anchor on the first (most recent) issue number |
| AMEND-02 | ERROR | Table has `[[latest_issue_date]]` anchor on the first entry's date |
| AMEND-03 | ERROR | Entries are ordered most-recent-first |
| AMEND-04 | WARNING | Release boundary rows use `4+^h\|*XX Release N.N.N*` format |
| AMEND-05 | WARNING | Jira references use `{spec_tickets}/SPECXX-NNN[SPECXX-NNN^]` syntax |
| AMEND-06 | WARNING | Table column spec is `[cols="1,6,2,2", options="header"]` or `[cols="1a,6,2,2a", options="header"]` |
| AMEND-07 | INFO | PR references (SPECPR) are included where CRs address PRs, using "Addresses/Fixes" phrasing |

## 4. Cross-References (XREF)

| ID | Severity | Check |
|----|----------|-------|
| XREF-01 | ERROR | All `{openehr_*}` attributes used in the document exist in `reference_definitions.adoc` or `global_vars.adoc` |
| XREF-02 | WARNING | Cross-spec links include display text and external link marker: `{attr}[Display Text^]` |
| XREF-03 | WARNING | Links to other openEHR specs use the predefined attributes, not hardcoded URLs |
| XREF-04 | INFO | Preface "Related Documents" links use `{openehr_*}` attributes consistently |

## 5. Figures and Diagrams (FIG)

| ID | Severity | Check |
|----|----------|-------|
| FIG-01 | WARNING | All `image::` directives have an `id=` attribute |
| FIG-02 | WARNING | All `image::` directives have `align="center"` |
| FIG-03 | WARNING | All figures have a title line (`.Title text`) preceding the image directive |
| FIG-04 | WARNING | Figures use `[.text-center]` role before the title line |
| FIG-05 | INFO | UML diagrams use `{uml_diagrams_uri}` path; hand-drawn diagrams use `{diagrams_uri}` |
| FIG-06 | INFO | SVG format preferred for diagrams; PNG acceptable for legacy |

## 6. AsciiDoc Conventions (ADOC)

| ID | Severity | Check |
|----|----------|-------|
| ADOC-01 | WARNING | Class/type names use monospace: `` `COMPOSITION` ``, `` `DV_TEXT` `` |
| ADOC-02 | WARNING | Attribute names use italic-in-monospace: `` `_uid_` ``, `` `_value_` `` |
| ADOC-03 | WARNING | No hand-written class definition tables — should `include::{uml_export_dir}/classes/...` the BMM-generated tables (regenerate via the `class-generation` skill, not by hand) |
| ADOC-04 | INFO | TBD markers use `[.tbd]` role followed by `*TBD*: (description)` |
| ADOC-05 | INFO | Deprecated markers use `[.deprecated]` role followed by `*Deprecated*: (explanation)` |
| ADOC-06 | INFO | Bibliographic citations use `cite:[Key]` or `citenp:[Key]` syntax |

## 7. Manifest Consistency (MANIFEST)

| ID | Severity | Check |
|----|----------|-------|
| MAN-01 | ERROR | Spec has a corresponding entry in the component's `manifest.json` `specifications` array |
| MAN-02 | WARNING | `manifest.json` entry `id` matches the spec directory name |
| MAN-03 | WARNING | `manifest.json` `spec_status` matches `manifest_vars.adoc` `:spec_status:` |
| MAN-04 | INFO | `manifest.json` entry has `title`, `description`, `summary`, `copyright_year`, `keywords` |

## 8. Content Quality (CONTENT)

| ID | Severity | Check |
|----|----------|-------|
| CONTENT-01 | WARNING | Chapter files start with a level-1 heading (`= Chapter Title`) |
| CONTENT-02 | WARNING | Chapters defining a package/model begin with an Overview subsection |
| CONTENT-03 | INFO | No hardcoded URLs to `specifications.openehr.org` — use attributes instead |
| CONTENT-04 | INFO | Inventory of all `[.tbd]` markers with their locations |
| CONTENT-05 | INFO | Inventory of all `[.deprecated]` markers with their locations |
