---
name: authoring
description: >
  Create or edit openEHR specification documents — the AsciiDoc sources, `manifest.json`, and
  boilerplate includes in `specifications-XX` repos. This skill should be used when the user asks to
  create a new spec, add or edit a chapter/section, set up `master.adoc`, edit a spec
  `manifest.json`, or work on `.adoc` files in a `specifications-XX` repo. Not for:
  archetype/template/AQL work (openehr-assistant plugin), amendment records (use amendment-record),
  prose style (use content-patterns), ITS-REST OpenAPI (use its-rest), or BMM class tables/diagrams
  (use class-generation).
---

# openEHR Specification Document Authoring

This skill covers creating and editing openEHR specification documents — the AsciiDoc sources
that live in `specifications-XX` repositories (RM, AM, BASE, LANG, PROC, SM, QUERY, CNF, TERM, ITS-*).

> **Note:** `specifications-ITS-REST` is an exception — it uses OpenAPI YAML with embedded Markdown
> rather than the standard AsciiDoc approach. See the "ITS-REST Exception" section below.

## Related Skills

- **content-patterns** — prose writing patterns for spec chapters (overview, semantics, design rationale, etc.)
- **amendment-record** — dedicated guide for amendment record authoring
- **review** — checklist-driven quality review of spec documents
- **its-rest** — for OpenAPI YAML and Markdown in the ITS-REST repo
- **governance** — release management, change requests, lifecycle governance
- **class-generation** — regenerate the class-definition tables and UML diagrams in `docs/UML/` from BMM via `bmm-publisher`
- **Cross-reference guide** — see `references/cross-references.md` for attribute naming patterns

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

The `specifications-AA_GLOBAL` repo (always a sibling) provides:
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

Under `specifications-XX/docs/`, create a directory matching the spec `id` from `manifest.json`.

### Step 2: Create `manifest_vars.adoc`

This file defines per-document Asciidoctor attributes used by the boilerplate:

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
- **`:spec_status:`** — One of: `DEVELOPMENT`, `TRIAL`, `STABLE`, `SUPERSEDED`, `OBSOLETE`, `RETIRED`
- **`:keywords:`** — Comma-separated keywords for the HTML meta tag
- **`:description:`** — One-line description for the HTML meta tag

### Step 3: Create `master.adoc`

The master file follows a strict structure. Here is the canonical template:

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

ifdef::package_qualifiers[]
:pkg: org.openehr.<component>.<spec>.
endif::[]

include::master01-preface.adoc[leveloffset=+1]
include::master02-overview.adoc[leveloffset=+1]
// ... additional chapters ...

//
// --------------------------------------------- Amendment Record -----------------------------------------------
//
:sectnums!:
include::master00-amendment_record.adoc[leveloffset=+1]

//
// --------------------------------------------- REFERENCES -----------------------------------------------
//
:sectnums!:
== References

bibliography::[]
```

**Include order in the header matters:**
1. `book_style_settings.adoc` — sets doctype, syntax highlighter, TOC
2. `manifest_vars.adoc` — local spec variables
3. `global_vars.adoc` — global openEHR attributes (depends on nothing above)

**Front block choice:**
- Use `full_front_block.adoc` for primary specifications (includes block diagram)
- Use `short_front_block.adoc` for secondary/overview documents (no block diagram)

### Step 4: Create `master00-amendment_record.adoc`

```asciidoc
= Amendment Record

[cols="1a,6,2,2a", options="header"]
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

Amendment record entries reference Jira tickets using `{spec_tickets}/SPECXX-NNN[SPECXX-NNN^]` syntax.
Release boundaries are marked with a full-width header row:

```asciidoc
4+^h|*RM Release 1.1.0*
```

### Step 5: Create chapter files

Name chapters sequentially: `master01-preface.adoc`, `master02-overview.adoc`, etc.

The preface (`master01-preface.adoc`) typically contains:
- Purpose of the specification
- Related documents
- Conformance/status notes
- Conventions used

### Step 6: Update `manifest.json`

Add the new specification entry to the `specifications` array.
See `references/manifest-spec-entry.md` for the full field reference.

### Step 7: Publish locally

```bash
# From the parent directory containing all specifications-XX repos:
./specifications-AA_GLOBAL/bin/spec_publish.sh -f -v XX
# Or via Docker:
docker run -u $(id -u):$(id -g) -v "$(pwd):/documents/" openehr/asciidoctor development XX
```

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
- **External references**: Check `reference_definitions.adoc` first — it has hundreds of pre-defined URLs for HL7, W3C, ISO, IETF, Wikipedia, SNOMED, etc.

### Global Variables

All release version attributes follow the pattern `:{component_id}_release:` and default to `latest`.
These are defined in `global_vars.adoc`:

```
:rm_release: latest
:am_release: latest
:base_release: latest
...
```

When publishing a named release, the publisher overrides these via `-a rm_release=Release-1.0.4`.

### URL Patterns in reference_definitions.adoc

References follow a consistent naming convention:

```
:openehr_{component}_{spec}: {openehr_{component}_releases}/{spec}.html
:openehr_{component}_latest_{spec}: {openehr_{component}_latest}/{spec}.html
:openehr_{component}_development_{spec}: {openehr_{component}_development}/{spec}.html
```

When adding new references, follow this pattern exactly.

### Amendment Record Updates

When editing a specification, always update the amendment record:
1. Add a new entry at the **top** of the table (most recent first)
2. Reference the relevant CR/PR Jira tickets
3. Update `[[latest_issue]]` version and `[[latest_issue_date]]` date on the new top entry
4. For non-release changes, increment the patch version

### Diagrams

- Place SVG diagrams in `<spec-id>/diagrams/`
- Reference as: `image::{diagrams_uri}/<filename>[...]`
- UML class and package diagrams are generated from the component's BMM schema by `bmm-publisher` (which renders them to SVG via PlantUML). This replaces the historical MagicDraw `.mdzip` extraction. See the **class-generation** skill to regenerate them.

### ITS-REST Exception

The `specifications-ITS-REST` component uses a different authoring approach:
- REST API definitions are specified using **OpenAPI YAML** schemas, not AsciiDoc
- Some documentation within ITS-REST is written in **Markdown** (embedded in the OpenAPI schema), not AsciiDoc
- Not all text documents in ITS-REST follow the standard AsciiDoc conventions described above
- The OpenAPI YAML files define REST API endpoints, request/response bodies, and include inline Markdown descriptions
