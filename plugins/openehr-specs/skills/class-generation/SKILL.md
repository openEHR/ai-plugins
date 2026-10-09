---
name: class-generation
description: >
  Generate openEHR class documentation — class-definition tables, effective views, and UML
  class/package diagrams — from BMM schemas with `bmm-publisher`, for `specifications-XX`
  repos. This skill should be used when the user asks to regenerate or
  refresh class tables or diagrams, run bmm-publisher, generate class docs from BMM/P_BMM, or replace
  hand-written or MagicDraw-derived class docs. Not for editing the BMM itself (use bmm-authoring),
  spec prose (use content-patterns), document scaffolding or hand-drawn diagrams (use authoring), or
  archetype/template work (openehr-assistant plugin).
---

# openEHR Class Documentation Generation (BMM)

Treat the per-class definition tables and the UML class/package diagrams embedded in
`specifications-XX` documents as **generated output**, never hand-written. Generate them from the
component's **BMM** (Basic Meta-Model) schema, serialised as
[P_BMM](https://specifications.openehr.org/releases/LANG/latest/bmm_persistence.html) JSON, with the
[`bmm-publisher`](https://github.com/openEHR/bmm-publisher) CLI tool.

> **Replaces MagicDraw.** Class tables and diagrams were historically extracted from MagicDraw
> `.mdzip` UML models. That mechanism is retired; `bmm-publisher` is the current BMM-based generator.

## Related Skills

- **bmm-authoring** — write or change the BMM schema itself, and check it before generating
- **authoring** — document scaffolding and repo layout; explains where generated class docs are included
- **review** — the ADOC-03 check enforces that class tables are generated, not hand-written
- **content-patterns** — prose around classes (semantics, rationale) that the generated tables do *not* cover

For the full command, option, and schema reference, see `references/bmm-publisher.md`.

## When to Regenerate

Regenerate class documentation when:

- A component's BMM schema changes (new/renamed/removed classes, properties, functions, or types)
- A spec needs its `docs/UML/classes/` tables refreshed before a release
- Class diagrams (SVGs) are stale relative to the model

## Installation

Run the tool from its Docker image, which bundles all openEHR BMM schemas and the `plantuml` CLI, so
no local PHP, Composer, or checkout is needed.

```bash
# Discover commands
docker run --rm ghcr.io/openehr/bmm-publisher list
```

To run from a cloned `bmm-publisher` checkout instead, see "Local development" in
`references/bmm-publisher.md`.

## Core Commands

| Command | Use for |
|---------|---------|
| `legacy-adoc` | Flat per-class definition tables for the legacy `docs/UML/classes` layout; `-o <container-dir>` sets the target, e.g. `/app/output/UML/classes` |
| `asciidoc` (`adoc`) | Class, effective (flattened), and definition tables plus rendered SVG class/package diagrams (current layout) |

Pass the **component repo's own BMM file** as a path, mounted into the container under `/in/`, and a
repeatable `-d` with the path of each dependency schema, loaded for cross-references only (not
exported). A bare schema id (`openehr_base_1.3.0`) or `all` loads the copy **bundled in the image**,
which lags the repos: a run from an id exits 0 but renders the older model, so use ids only to
reproduce published output. Add `-v` to log each file read (confirm it is `/in/…`) or `-vv` for detail. The other commands (`plantuml`, `embed-svg`, `yaml`,
`split-json`, `odin`) and all options are in `references/bmm-publisher.md`.

## Output Layouts and How Specs Consume Them

`bmm-publisher` writes two layouts. Read the target component's chapter files to pick one:
`include::{uml_export_dir}/classes/...` lines mean the legacy layout. If neither layout is evident,
ask the user.

### Legacy layout — `docs/UML/classes/` (the `include` model)

`legacy-adoc` produces one `.adoc` table per class, named
`org.openehr.<component>.<package>.<class>.adoc` (the class segment is **lowercased**, e.g.
`org.openehr.base.base_types.access_group_ref.adoc`). These are placed in the component's
`docs/UML/classes/` directory and pulled into chapter files via the `{uml_export_dir}` attribute
(which resolves to `../UML`):

```asciidoc
include::{uml_export_dir}/classes/{pkg}composition.adoc[]
```

`{pkg}` is the `:pkg:` attribute set in `master.adoc` (see `authoring`). This is the layout enforced by the `review` skill's **ADOC-03** check.

### Current layout — `output/Adoc/<schema>/` (tables + rendered SVGs)

`asciidoc` produces `classes/`, `effective/`, `definitions/`, `plantUML/`, and rendered SVGs under
`images/uml/{classes,diagrams}/`. Diagrams are referenced with Antora-style resource macros:

```asciidoc
image::ROOT:uml/classes/COMPOSITION.svg[]
```

## Typical Workflow

1. **Locate the schema files.** Work from the component repo's root. The schema is
   `computable/BMM/openehr_<component>_<version>.bmm.json`; each dependency comes from its sibling clone
   (RM, AM, LANG and TERM classes refer to BASE types:
   `../specifications-BASE/computable/BMM/openehr_base_<version>.bmm.json`). When a file is missing, say
   which and stop rather than falling back to a bundled id. If the schema was edited by hand, run the
   `bmm-authoring` checker on it first.
2. **Choose the command by layout** (see above): `legacy-adoc` for the legacy layout, `asciidoc` for
   the current one.
3. **Generate** into a temporary directory, mounting the files read-only and mapping ownership to the
   host user (RM shown, with its BASE dependency):
   ```bash
   OUT=$(mktemp -d)
   docker run --rm --user $(id -u):$(id -g) \
     -v "$PWD/computable/BMM/openehr_rm_1.2.0.bmm.json":/in/openehr_rm_1.2.0.bmm.json:ro \
     -v "$PWD/../specifications-BASE/computable/BMM/openehr_base_1.3.0.bmm.json":/in/openehr_base_1.3.0.bmm.json:ro \
     -v "$OUT":/app/output \
     ghcr.io/openehr/bmm-publisher asciidoc -v /in/openehr_rm_1.2.0.bmm.json -d /in/openehr_base_1.3.0.bmm.json
   ```
   For the legacy layout, run `legacy-adoc -v -o /app/output/UML/classes /in/<schema>.bmm.json -d
   /in/<dependency>.bmm.json` instead; the tables land in `$OUT/UML/classes`. Without the dependency,
   links to its types come out as `link:/classes/<Type>`.
4. **Place** the output. Legacy layout: copy `$OUT/UML/classes/*.adoc` into the component's
   `docs/UML/classes/`. Current layout: ask the user how the component wires the
   `output/Adoc/<schema>/` content. Ask before overwriting files in a `specifications-XX` repo, and do
   not commit.
5. **Verify** by publishing the spec (see the `authoring` skill) and confirming class tables and
   diagrams render and cross-references resolve.

The user-only `/openehr-specs:regen-classes` skill covers steps 1 to 3 only (output to `./out`, no
placement, no commit). When the user has already run it, continue from step 4. For a local preview,
the user can run `/openehr-specs:publish <component>`.

## Guardrails

- **Generated output is never hand-edited.** Fix the BMM schema (see `bmm-authoring`) and regenerate.
  A clean run does not prove the schema is right: `bmm-publisher` renders many modelling mistakes as
  type `Any` or drops them without a message, so run the `bmm-authoring` checker first.
- **Use the repo's BMM, not the bundled copy.** Mount the files under `/in/` and pass their paths. Do not
  mount a directory over `/app/resources`: it hides the bundled schemas, so a dependency named by id is
  then missing and the run exits 1.
- **`resources/*.bmm.json` is upstream input** in a cloned `bmm-publisher` checkout: do not modify it
  unless the task is specifically to change the model.
- Provide cross-referenced dependency schemas with `-d` so type links resolve (e.g. RM depends on BASE).
