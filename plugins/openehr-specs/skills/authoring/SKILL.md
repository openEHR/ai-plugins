---
name: authoring
description: >
  Create or edit openEHR specification AsciiDoc sources, `manifest.json` spec entries, and
  boilerplate includes in `specifications-XX` repos. This skill should be used when the user asks
  to scaffold a new spec, add or edit a chapter, set up `master.adoc`, add a cross-reference or
  figure, or build a local HTML preview. Not for amendment records (amendment-record), prose
  style (content-patterns), releases or manifest release entries (governance), ITS-REST OpenAPI
  (its-rest), class tables (class-generation), or archetype/AQL work (openehr-assistant plugin).
---

# openEHR Specification Document Authoring

Use this skill to create and edit openEHR specification documents: the AsciiDoc sources that live
in `specifications-XX` repositories (RM, AM, BASE, LANG, PROC, SM, QUERY, CDS, CNF, TERM, ITS-*).

> **Note:** In `specifications-ITS-REST`, the OpenAPI YAML and Markdown sources are covered by the
> **its-rest** skill. The AsciiDoc specs under its `docs/` (for example `simplified_formats`,
> `smart_app_launch`) follow this skill.

## Related Skills

- **content-patterns** — prose writing patterns for spec chapters (overview, semantics, design rationale, etc.)
- **amendment-record** — dedicated guide for amendment record authoring
- **review** — checklist-driven quality review of spec documents (the `spec-reviewer` subagent runs it over a whole spec or component)
- **its-rest** — for OpenAPI YAML and Markdown in the ITS-REST repo
- **governance** — release management, change requests, lifecycle governance
- **class-generation** — regenerate the class-definition tables and UML diagrams in `docs/UML/` from BMM via `bmm-publisher`

For attribute naming patterns, read `references/cross-references.md`. To verify that every
`{openehr_*}` attribute and deep-link anchor resolves, dispatch the `xref-auditor` subagent.

## Repository Layout

Each specification component lives in its own repo: `specifications-XX` (e.g., `specifications-RM`).
The shared infrastructure repo `specifications-AA_GLOBAL` provides boilerplate, styles, references,
and publishing scripts used by all components.

```
specifications-XX/
├── manifest.json              # Component metadata, specs, releases, Jira links
├── docs/
│   ├── index.adoc             # Component index page
│   ├── <spec-id>/             # One directory per specification
│   │   ├── master.adoc        # Main entry point
│   │   ├── manifest_vars.adoc # Per-spec variables
│   │   ├── master00-amendment_record.adoc
│   │   ├── master01-preface.adoc
│   │   ├── master02-*.adoc ... masterNN-*.adoc
│   │   ├── diagrams/          # SVG/PNG diagrams
│   │   └── images/            # Other images
│   ├── UML/                   # BMM-generated class docs + diagrams (do NOT hand-edit; see class-generation skill)
│   └── common/                # Shared content within component
```

The `specifications-AA_GLOBAL` repo (expected as a sibling checkout; if absent, read its files at
https://github.com/openEHR/specifications-AA_GLOBAL) provides:
```
specifications-AA_GLOBAL/
├── docs/boilerplate/          # Shared AsciiDoc includes
│   ├── global_vars.adoc       # Global Asciidoctor attributes
│   ├── book_style_settings.adoc
│   ├── basic_style_settings.adoc
│   ├── full_front_block.adoc  # Full front matter (with block diagram)
│   ├── short_front_block.adoc # Short front matter (without block diagram)
│   ├── doc_id_block.adoc      # Release/status/revision table
│   └── licence_block.adoc     # Copyright and licence table
├── docs/references/
│   └── reference_definitions.adoc  # All cross-spec and external URLs
├── resources/css/             # Stylesheets
├── resources/logos/           # openEHR logos
└── bin/
    ├── spec_publish.sh        # Main publishing script
    └── do_spec_publish.sh     # Wrapper
```

The `{ref_dir}` Asciidoctor attribute resolves to the AA_GLOBAL repo root relative to the
consuming spec document.

## Creating a New Specification Document

### Step 1: Create the spec directory

Choose the spec `id` (the SEC verifies identifier and placement for new specs; see the **governance**
skill) and create `specifications-XX/docs/<id>/`. Use the same `id` in the `manifest.json` entry (Step 6).

### Step 2: Create `manifest_vars.adoc`

Define the per-document Asciidoctor attributes that the boilerplate reads. The values below come from
the EHR IM; replace them with the new spec's own:

```asciidoc
:spec_title: EHR Information Model
:copyright_year: 2003
:spec_status: STABLE
:keywords: EHR, EMR, reference model, openehr
:description: openEHR EHR Information Model specification
```

Fields:
- **`:spec_title:`** — The document title, displayed after the openEHR logo
- **`:copyright_year:`** — Year of first publication (used in licence block)
- **`:spec_status:`** — One of: `DEVELOPMENT`, `TRIAL`, `STABLE`, `PAUSED`, `SUPERSEDED`, `OBSOLETE`, `RETIRED`. Use the state the SEC assigned (see the **governance** skill) and keep it identical to `spec_status` in `manifest.json`
- **`:keywords:`** — Comma-separated keywords for the HTML meta tag
- **`:description:`** — One-line description for the HTML meta tag

### Step 3: Create `master.adoc`

Write `master.adoc` from this canonical template:

```asciidoc
//
// ============================================ Asciidoc HEADER =============================================
//
include::{ref_dir}/docs/boilerplate/book_style_settings.adoc[]
include::manifest_vars.adoc[]
include::{ref_dir}/docs/boilerplate/global_vars.adoc[]

//
// ============================================ Asciidoc PREAMBLE =============================================
//

image::{openehr_logo}["openEHR logo",align="center"]

= {spec_title}

include::{ref_dir}/docs/boilerplate/full_front_block.adoc[]
include::{ref_dir}/docs/references/reference_definitions.adoc[]

//
// ============================================= Asciidoc BODY ===============================================
//

include::master00-amendment_record.adoc[leveloffset=+1]

//
// --------------------------------------------- Preface -----------------------------------------------
//

== Acknowledgements

=== Editor

* <Editor Name>, <Affiliation>.

=== Contributors

<List of contributors>

=== Trademarks

* 'openEHR' is a trademark of the openEHR Foundation

//
// --------------------------------------------- CHAPTERS -----------------------------------------------
//
:sectnums:

// `package_qualifiers` is set by the publisher's -q flag; :pkg: is the lower-case package prefix of the spec.
ifdef::package_qualifiers[]
:pkg: org.openehr.<component>.<spec>.
endif::[]

include::master01-preface.adoc[leveloffset=+1]
include::master02-overview.adoc[leveloffset=+1]
// ... additional chapters ...

//
// --------------------------------------------- REFERENCES -----------------------------------------------
//
:sectnums!:
== References

bibliography::[]
```

**Keep the header includes in this order:**
1. `book_style_settings.adoc` — sets doctype, syntax highlighter, TOC
2. `manifest_vars.adoc` — local spec variables
3. `global_vars.adoc` — global openEHR attributes

**Front block choice:**
- Use `full_front_block.adoc` for primary specifications (includes block diagram)
- Use `short_front_block.adoc` for secondary/overview documents (no block diagram)

### Step 4: Create `master00-amendment_record.adoc`

```asciidoc
= Amendment Record

[cols="1,6,2,2", options="header"]
|===
|Issue|Details|Raiser|Completed

|[[latest_issue]]0.1.0
|Initial writing.
|<Author Name>
|[[latest_issue_date]]<dd Mon yyyy>

|===
```

The `[[latest_issue]]` and `[[latest_issue_date]]` anchors are required — the `doc_id_block.adoc`
references them to display revision and date in the front matter table.

For Jira references, version bumps, and release boundaries, see the **amendment-record** skill.

### Step 5: Create chapter files

Name chapters sequentially: `master01-preface.adoc`, `master02-overview.adoc`, etc., and keep the
numbering gap-free. Appendices use `masterAppA-<name>.adoc`. Start each chapter file with a
`= Chapter Title` heading, and add a matching `include::masterNN-<name>.adoc[leveloffset=+1]` line to
`master.adoc`.

Create `master01-preface.adoc` with a `= Preface` heading and these `==` sections in order: Purpose,
Related Documents, Status, Feedback, then optionally Conformance, Tools, and Changes from Previous
Versions. Use the Status and Feedback link patterns in `references/cross-references.md`.

### Step 6: Update `manifest.json`

Add the new specification entry to the `specifications` array, with `id`, `title`, `description`,
`copyright_year`, `spec_status`, and `keywords` matching `manifest_vars.adoc`. See
`references/manifest-spec-entry.md` for the full field reference.

### Step 7: Preview locally

Build a local HTML preview after creating or editing a spec. The user can run
`/openehr-specs:publish <component>` (user-only; it wraps the commands below), or run them
from the parent directory that contains all `specifications-*` repos. `-f` forces regeneration, `-v`
is verbose, and `XX` is the component (for example `RM`):

```bash
./specifications-AA_GLOBAL/bin/spec_publish.sh -f -v XX
# Or via Docker:
docker run -u $(id -u):$(id -g) -v "$(pwd):/documents/" openehr/asciidoctor development XX
```

The preview does not tag or deploy a release; that is the **governance** skill's process.

## Editing Existing Specifications

### Conventions

- **Chapter files**: Edit `masterNN-*.adoc` files directly. Never edit files under `docs/UML/` — those are generated from the component's BMM schema by `bmm-publisher` (see the **class-generation** skill); change the BMM and regenerate.
- **Cross-references within spec**: Use `<<anchor_name>>` or `<<anchor_name, display text>>`.
- **Cross-references to other specs**: Use the URL attributes from `reference_definitions.adoc`:
  ```asciidoc
  {openehr_rm_common}[Common IM^]
  {openehr_rm_data_types}#dv_quantity[DV_QUANTITY^]
  ```
- **Cross-references to classes**: Use `{classes_url_root}` for linking to the class index.
- **Jira ticket references**: `{spec_tickets}/SPECRM-87[SPECRM-87^]`
- **External references**: Check `reference_definitions.adoc` first — it has hundreds of pre-defined URLs for HL7, W3C, ISO, IETF, Wikipedia, SNOMED, etc. If an attribute is missing, add it to `specifications-AA_GLOBAL/docs/references/reference_definitions.adoc` (a separate repo and commit) following the naming pattern, and tell the user the change spans two repos.

### Global Variables and URL Patterns

Release-version attributes (`{rm_release}` and so on, defaulting to `latest`) and spec-link attributes
follow fixed naming patterns; read `references/cross-references.md` before constructing one, and
follow the pattern exactly when adding a new reference. To build a named release, pass the label to the
publisher with `-l <label>` (see the **governance** skill).

### Amendment Record Updates

Add an entry to the spec's amendment record for every change, following the **amendment-record**
skill (entry order, anchors, version-bump table, Jira references). The user can also run
`/openehr-specs:amendment-record <SPECXX-NN[,SPECPR-NN] — summary>` to have the entry added directly.

### Diagrams

- Place hand-drawn SVG diagrams in `<spec-id>/diagrams/`. Generated UML diagrams use `{uml_diagrams_uri}`.
- Write each figure as a titled block:

  ```asciidoc
  [.text-center]
  .Figure title
  image::{diagrams_uri}/<filename>.svg[id=<anchor_id>, align="center"]
  ```
- UML class and package diagrams are generated from the component's BMM schema by `bmm-publisher` (which renders them to SVG via PlantUML). This replaces the historical MagicDraw `.mdzip` extraction. See the **class-generation** skill to regenerate them.
