---
name: its-rest
description: >
  Create, edit, or review the openEHR ITS-REST API sources (OpenAPI 3.0 YAML + Markdown) in the
  `specifications-ITS-REST` repo. This skill should be used when the user asks to add or edit a REST
  endpoint/operation/schema/response, write an operation description, review the ITS-REST spec, add
  an ITS-REST amendment entry, or bundle and validate the OpenAPI specs. Not for AsciiDoc specs (use
  authoring), including the AsciiDoc docs under `specifications-ITS-REST/docs/` (simplified_formats,
  smart_app_launch).
---

# openEHR ITS-REST API Specification Authoring

Create and edit the openEHR REST API specification sources in the `specifications-ITS-REST`
repository. Unlike other `specifications-XX` repos, which use AsciiDoc, ITS-REST uses
**OpenAPI 3.0.3 YAML** with **Markdown** descriptions, split across many small files that are
bundled into publishable artifacts.

## References

- **File-format conventions**: see `references/file-formats.md` for the detailed format and
  conventions of each source type — top-level entry YAML, operation files, schema files,
  Markdown description files, and the HTML amendment record. Load it when writing or editing any
  of these.
- **Build toolchain**: see `references/build-pipeline.md` for the full Redocly + PHP pipeline,
  validation, live preview, and code generation.

## Repository Structure

```
specifications-ITS-REST/
├── specifications/                    # Source OpenAPI specs (authoring)
│   ├── overview.openapi.yaml          # Top-level entry: overview/cross-cutting concerns
│   ├── ehr.openapi.yaml               # Top-level entry: EHR API
│   ├── query.openapi.yaml             # Top-level entry: Query API
│   ├── definition.openapi.yaml        # Top-level entry: Definition API
│   ├── demographic.openapi.yaml       # Top-level entry: Demographic API
│   ├── system.openapi.yaml            # Top-level entry: System API
│   ├── admin.openapi.yaml             # Top-level entry: Admin API
│   ├── operations/                    # One YAML file per API operation
│   ├── schemas/<domain>/              # Reusable schema components (ehr, query, common, …)
│   ├── parameters/{path,query,header}/ # Reusable parameter definitions
│   ├── responses/                     # Reusable response definitions
│   ├── headers/                       # Reusable response header definitions
│   ├── docs/<domain>/                 # Markdown description files (overview, ehr, query, …)
│   └── tags/                          # Tag description files (schema docs)
├── computable/OAS/                    # Build output (bundled specs in JSON/YAML)
├── docs/                              # AsciiDoc specs AND rendered HTML output
│   ├── simplified_formats/            # AsciiDoc spec (use authoring skill)
│   ├── smart_app_launch/              # AsciiDoc spec (use authoring skill)
│   └── *.html                         # Rendered HTML (build output)
├── development/                       # Build tooling (PHP, Docker, Makefile)
├── manifest.json                      # Component manifest
├── Makefile                           # Top-level build targets
└── .redocly.yaml                      # Redocly configuration
```

## Source File Types

Each source type has its own format and conventions — detailed in `references/file-formats.md`:

| Source | Location | Holds |
|--------|----------|-------|
| Top-level entry | `specifications/<domain>.openapi.yaml` | `info`/`x-status`/`x-spec`, servers, `paths` wiring operations via `$ref` |
| Operation | `specifications/operations/<resource>_<action>.yaml` | `operationId`, summary, tags, params, requestBody, responses (all `$ref`) |
| Schema | `specifications/schemas/<domain>/<SchemaName>.yaml` | PascalCase file name; `title` = RM class name; properties; `$ref`s |
| Markdown description | `specifications/docs/<domain>/Description.md` | RFC 2119 prose, hardcoded spec URLs, `http`/`json` code examples |
| Amendment record | `specifications/docs/overview/Amendment_record.md` | HTML table, `SPECITS` Jira links (not AsciiDoc) |

## Build Toolchain

Run build commands from the `development/` directory. Docker is required; first-time setup and full
details are in `references/build-pipeline.md`.

```bash
make bundle SPEC=ehr        # Bundle a single spec
make validate SPEC=ehr      # Validate
make all                    # Bundle all specs
```

## Adding a New Endpoint

1. Create the operation file: `specifications/operations/<operation_id>.yaml`
2. Reuse shared definitions from `specifications/parameters/`, `responses/`, and `headers/`. Add a new
   file only when none fits, and copy the structure and naming of its closest sibling in the same folder.
3. Add or reference schemas in `specifications/schemas/<domain>/`
4. Wire the operation into the appropriate top-level `*.openapi.yaml` under `paths:` (ask the user
   which API domain when it is unclear)
5. Add an entry to the amendment record in `specifications/docs/overview/Amendment_record.md`. Ask the
   user for the `SPECITS` ticket, the raiser, and the completion date; do not invent them.
6. Bundle and validate: `cd development && make bundle SPEC=<spec> && make validate SPEC=<spec>`

## Adding a New Schema

1. Create `specifications/schemas/<domain>/<SchemaName>.yaml` (PascalCase file name)
2. Set `title` to the RM class name
3. Reference it from the operation or parent schema via `$ref`
4. Follow the layout of the closest sibling schema for `required`, `type`, `properties`, and `description`

## Reviewing Changes

Check each changed file against `references/file-formats.md`:

1. Operation: `operationId` is unique, snake_case, and equals the file name; `summary` is a short
   imperative phrase; `tags` holds one tag; parameters, request bodies, responses, and headers use
   `$ref` to shared definitions.
2. Schema: the file name is PascalCase, `title` is the RM class name, and every relative `$ref` resolves.
3. Markdown: RFC 2119 keywords are in ALL CAPS, prose is third person and present tense with no
   contractions, spec links are hardcoded URLs, and code examples use `http` or `json` fences.
4. Amendment record: an entry with a `SPECITS` link exists.
5. `make bundle` and `make validate` pass for the affected spec.

## Scope Boundaries

- Cover the **OpenAPI YAML and Markdown** sources in `specifications-ITS-REST/specifications/`.
- Use `authoring` for the AsciiDoc documents in `specifications-ITS-REST/docs/` (simplified_formats, smart_app_launch).
- Leave the PHP build tooling internals in `development/` alone; consult `.junie/guidelines.md` for those. The `make` commands above are in scope.
- Do not cover other `specifications-XX` repositories.
- Do not apply the AsciiDoc-only tools to these sources. The `review` skill, the `spec-reviewer` and `xref-auditor` subagents, and the `/openehr-specs:amend` command expect AsciiDoc sources (`master*.adoc`); hardcoded spec URLs and the HTML amendment record are correct here.
