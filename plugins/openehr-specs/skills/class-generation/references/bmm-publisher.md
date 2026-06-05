# bmm-publisher — full reference

This reference applies exclusively to the openEHR specification ecosystem. `bmm-publisher` is the
openEHR Foundation CLI that reads **BMM** (Basic Meta-Model) schemas — serialised as
[P_BMM](https://specifications.openehr.org/releases/LANG/latest/bmm_persistence.html) JSON — and
generates class documentation for the [specifications site](https://specifications.openehr.org/).

- Repository: <https://github.com/openEHR/bmm-publisher>
- Image: `ghcr.io/openehr/bmm-publisher`
- Requires: Docker only (the image bundles all BMM schemas, the `plantuml` CLI, OpenJDK, and Graphviz)

## What it generates

From each BMM schema the tool can produce:

- **AsciiDoc** class-definition tables, effective (flattened) views, cross-referenced type links, and
  class/package diagrams pre-rendered to SVG
- **PlantUML** `.puml` sources (the diagram source of truth)
- **YAML** serialisation of each schema
- **Per-type JSON** (one file per class)
- **ODIN** `.bmm` files (the hand-authored openEHR BMM format)

## Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `asciidoc` | `adoc` | Class tables + class/package diagrams rendered as standalone SVGs under `images/uml/{classes,diagrams}/`, referenced from the tabs partial via `image::ROOT:uml/classes/<name>.svg[]`. Self-contained: writes tables, runs PlantUML, and publishes SVGs in one invocation. |
| `legacy-adoc` | | Legacy `docs/UML/classes` layout — flat per-class definition tables only. `-o <dir>` chooses the output directory. |
| `plantuml` | `uml`, `puml` | Standalone PlantUML source tree (`output/PlantUML/<schema>/...`) — only the `.puml` files. |
| `embed-svg` | | Re-run only the SVG sanitise + publish step against existing `.svg` files (surgical re-renders). |
| `yaml` | | Convert BMM JSON schemas to YAML. |
| `split-json` | | Split the latest BMM JSON of each component into per-type files. |
| `odin` | | Convert BMM JSON schemas to ODIN `.bmm` schema files. |

## Arguments and options

- **Positional**: one or more schema ids **without** the `.bmm.json` extension (e.g.
  `openehr_rm_1.2.0`), or literal `.bmm.json` paths, or `all` to process every schema in the input
  directory.
- **`-d <schema>`** (repeatable): a dependency schema id or path, loaded for cross-reference
  resolution only — **not** exported. Accepted by `asciidoc`, `legacy-adoc`, and `plantuml`. Example:
  RM references BASE types, so generate RM with `-d openehr_base_1.3.0`.
- **`-o <dir>`** (`legacy-adoc` only): output directory for the class `.adoc` files. Default:
  `<output>/legacy-adoc/<schema_id>` per schema.
- **`-v`** / **`-vv`**: progress output / detailed file-write logging.

## Input / output

- **Input**: BMM schemas in `resources/` (`.bmm.json`, shipped with the image). Mount your own with
  `-v ./my-schemas:/app/resources`.
- **Output**: artefacts in `output/` — mount a volume to retrieve them: `-v ./out:/app/output`.
- **`BMM_OUTPUT_DIR`** env var overrides the output path: `-e BMM_OUTPUT_DIR=/data/out`.

### Bundled schema ids

Schemas follow the pattern `openehr_<component>_<version>`. The image bundles (among others):

- `openehr_base_1.0.4` … `openehr_base_1.3.0`
- `openehr_rm_1.0.2` … `openehr_rm_1.2.0`
- `openehr_am_1.4.0` … `openehr_am_2.4.0`
- `openehr_lang_1.0.0`, `openehr_lang_1.1.0`
- `openehr_term_3.0.0`, `openehr_term_3.1.0`

Run `docker run --rm ghcr.io/openehr/bmm-publisher list` and inspect `resources/` for the exact set
shipped by a given image tag.

## Invocation examples (Docker)

```bash
# All bundled schemas → AsciiDoc tables + SVG diagrams
docker run --rm -v ./out:/app/output ghcr.io/openehr/bmm-publisher asciidoc all

# Single schema with a dependency, host-owned output, verbose
docker run --rm --user $(id -u):$(id -g) \
  -v ./out:/app/output \
  ghcr.io/openehr/bmm-publisher asciidoc -v openehr_rm_1.2.0 -d openehr_base_1.3.0

# Legacy per-class tables straight into a spec repo's docs/UML/classes
docker run --rm --user $(id -u):$(id -g) \
  -v ./out:/app/output \
  ghcr.io/openehr/bmm-publisher legacy-adoc -o /app/output/UML/classes openehr_base_1.3.0

# Your own BMM schemas
docker run --rm \
  -v ./my-schemas:/app/resources \
  -v ./out:/app/output \
  ghcr.io/openehr/bmm-publisher yaml all

# PlantUML sources only
docker run --rm -v ./out:/app/output ghcr.io/openehr/bmm-publisher plantuml openehr_rm_1.2.0
```

### Host-user mapping

By default the image runs as the bundled `app` user (uid 1000). Pass `--user $(id -u):$(id -g)` so
files in a bind-mounted `output/` are owned by the host user. The image supports arbitrary uids (any
non-root user keeps gid 0, and `/app/output` is group-writable).

### Tagged images

Tags follow SemVer: `ghcr.io/openehr/bmm-publisher:1.0.0`, `:1.0`, `:1`.

## Local development (cloned checkout)

The repo has **no host PHP requirement** — drive everything through its Docker dev container:

```bash
make install        # composer install in the container
make sh             # interactive shell
make publish-all    # regenerate everything under output/
make ci             # full quality gate (lint, PHPCS, PHPStan, PHPUnit)

# Inside the dev container:
./bin/bmm-publisher asciidoc openehr_rm_1.2.0 -d openehr_base_1.3.0
```

Guardrails from the tool's own AI workflow:

- `output/` is committed but **generated** — never hand-edit; regenerate via `make publish-all`.
- `resources/*.bmm.json` is upstream input — do not modify unless the task says so.

## Extending the tool

BMM formally describes the full openEHR type system, so it can drive downstream artefacts beyond docs
(code skeletons, JSON Schema/OpenAPI, GraphQL types, DB DDL, diff reports, conformance fixtures). The
architecture is deliberately simple: `BmmSchemaCollection` loads and indexes all schemas; a writer
(a single callable class) iterates them and writes output. Fork and add a writer for new formats.
