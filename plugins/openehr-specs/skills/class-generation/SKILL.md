---
name: class-generation
description: >
  Generate openEHR class documentation — class-definition tables, effective views, and UML
  class/package diagrams — from BMM schemas with the `bmm-publisher` tool, for `specifications-XX`
  repos and their `docs/UML/` content. This skill should be used when the user asks to regenerate
  class tables, run bmm-publisher, generate class docs from BMM/P_BMM, or render a spec's class
  diagrams. Not for spec prose (use content-patterns), document scaffolding (use authoring), or
  archetype/template work (openehr-assistant plugin).
---

# openEHR Class Documentation Generation (BMM)

openEHR specification class documentation — the per-class definition tables and the UML class/package
diagrams embedded in `specifications-XX` documents — is **generated, not hand-written**. The source of
truth is the component's **BMM** (Basic Meta-Model) schema, serialised as
[P_BMM](https://specifications.openehr.org/releases/LANG/latest/bmm_persistence.html) JSON, and the
generator is the [`bmm-publisher`](https://github.com/openEHR/bmm-publisher) CLI tool.

> **Replaces MagicDraw.** Class tables and diagrams were historically extracted from MagicDraw
> `.mdzip` UML models. That mechanism is retired; `bmm-publisher` is the current BMM-based generator.

## Related Skills

- **authoring** — document scaffolding and repo layout; explains where generated class docs are included
- **review** — the ADOC-03 check enforces that class tables are generated, not hand-written
- **content-patterns** — prose around classes (semantics, rationale) that the generated tables do *not* cover

For the full command, option, and schema reference, see `references/bmm-publisher.md`.

## When to Regenerate

Regenerate class documentation when:

- A component's BMM schema changes (new/renamed/removed classes, properties, functions, or types)
- A spec needs its `docs/UML/classes/` tables refreshed before a release
- Class diagrams (SVGs) are stale relative to the model

Never hand-edit the generated output — change the BMM schema upstream and regenerate.

## Installation

The tool is distributed as a Docker image that bundles all openEHR BMM schemas and the `plantuml` CLI.
No local PHP, Composer, or checkout is required.

```bash
# Discover commands
docker run --rm ghcr.io/openehr/bmm-publisher list
```

For local development against a cloned `bmm-publisher` checkout, drive everything through its dev
container (no host PHP): `make install`, `make sh`, `make publish-all`. See `references/bmm-publisher.md`.

## Core Commands

| Command | Aliases | Produces |
|---------|---------|----------|
| `asciidoc` | `adoc` | AsciiDoc class/effective/definition tables **and** rendered SVG class/package diagrams (self-contained) |
| `legacy-adoc` | | Flat per-class definition tables only, in the legacy `docs/UML/classes` layout (`-o <dir>` to target) |
| `plantuml` | `uml`, `puml` | Standalone PlantUML `.puml` sources only |
| `embed-svg` | | Re-run only the SVG sanitise + publish step |
| `yaml` | | Machine-readable YAML serialisation of each schema |
| `split-json` | | Per-type JSON files |
| `odin` | | ODIN `.bmm` schema files (the hand-authored BMM format) |

Pass schema id(s) **without** the `.bmm.json` suffix (e.g. `openehr_base_1.3.0`), or `all`. Use
repeatable `-d <schema>` for dependency schemas loaded for cross-references only (not exported), and
`-v`/`-vv` for progress / detailed logging.

## Output Layouts and How Specs Consume Them

`bmm-publisher` writes two layouts; pick the one the target component uses.

### Legacy layout — `docs/UML/classes/` (the `include` model)

`legacy-adoc` produces one `.adoc` table per class, named
`org.openehr.<component>.<package>.<class>.adoc` (the class segment is **lowercased**, e.g.
`org.openehr.base.base_types.access_group_ref.adoc`). These are placed in the component's
`docs/UML/classes/` directory and pulled into chapter files via the `{uml_export_dir}` attribute
(which resolves to `../UML`):

```asciidoc
include::{uml_export_dir}/classes/{pkg}composition.adoc[]
```

This is the layout enforced by the `review` skill's **ADOC-03** check.

### Current layout — `output/Adoc/<schema>/` (tables + rendered SVGs)

`asciidoc` produces `classes/`, `effective/`, `definitions/`, `plantUML/`, and rendered SVGs under
`images/uml/{classes,diagrams}/`. Diagrams are referenced with Antora-style resource macros:

```asciidoc
image::ROOT:uml/classes/COMPOSITION.svg[]
```

## Typical Workflow

1. **Identify the schema** for the component and version, e.g. `openehr_base_1.3.0`, `openehr_rm_1.2.0`
   (naming pattern: `openehr_<component>_<version>`).
2. **Generate** into a working directory, mapping ownership to the host user:
   ```bash
   docker run --rm --user $(id -u):$(id -g) \
     -v ./out:/app/output \
     ghcr.io/openehr/bmm-publisher asciidoc -v openehr_rm_1.2.0 -d openehr_base_1.3.0
   ```
3. **Place** the generated `classes/*.adoc` into the component's `docs/UML/classes/` (legacy layout)
   or wire the `output/Adoc/<schema>/` content per the component's current convention.
4. **Verify** by publishing the spec (see the `authoring` skill) and confirming class tables and
   diagrams render and cross-references resolve.

## Guardrails

- **Generated output is never hand-edited.** Fix the BMM schema and regenerate.
- **`resources/*.bmm.json` is upstream input** — do not modify it unless the task is specifically to
  change the model.
- Provide cross-referenced dependency schemas with `-d` so type links resolve (e.g. RM depends on BASE).
