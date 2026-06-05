---
name: its-rest
description: >
  Create, edit, or review the openEHR ITS-REST API sources (OpenAPI 3.0 YAML + Markdown) in the
  `specifications-ITS-REST` repo. This skill should be used when the user asks to add or edit a REST
  endpoint/operation/schema/response, write an operation description, review the ITS-REST spec, or
  update its amendment record. Not for AsciiDoc specs (use authoring) — including the AsciiDoc docs
  under `specifications-ITS-REST/docs/` (simplified_formats, smart_app_launch).
---

# openEHR ITS-REST API Specification Authoring

This skill covers creating and editing the openEHR REST API specification sources in the
`specifications-ITS-REST` repository. Unlike other `specifications-XX` repos that use
AsciiDoc, ITS-REST uses **OpenAPI 3.0.3 YAML** with **Markdown** descriptions, split across
many small files that are bundled into publishable artifacts.

> **Exception**: The `docs/` directory contains some AsciiDoc-based specs (e.g.,
> `simplified_formats`, `smart_app_launch`) that follow the standard openEHR authoring
> conventions. This skill does NOT cover those — use the `authoring` skill instead.

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
| Schema | `specifications/schemas/<domain>/<SchemaName>.yaml` | PascalCase `title` = RM class name, properties, `$ref`s |
| Markdown description | `specifications/docs/<domain>/Description.md` | RFC 2119 prose, hardcoded spec URLs, `http`/`json` code examples |
| Amendment record | `specifications/docs/overview/Amendment_record.md` | HTML table, `SPECITS` Jira links (not AsciiDoc) |

## Build Toolchain

Quick reference from the `development/` directory (full details in `references/build-pipeline.md`):

```bash
make bundle SPEC=ehr        # Bundle a single spec
make validate SPEC=ehr      # Validate
make all                    # Bundle all specs
```

## Adding a New Endpoint

1. Create the operation file: `specifications/operations/<operation_id>.yaml`
2. Add shared parameters to `specifications/parameters/` if new ones are needed
3. Add shared response definitions to `specifications/responses/` if new ones are needed
4. Add or reference schemas in `specifications/schemas/<domain>/`
5. Wire the operation into the appropriate top-level `*.openapi.yaml` under `paths:`
6. Update the amendment record in `specifications/docs/overview/Amendment_record.md`
7. Bundle and validate: `cd development && make bundle SPEC=<spec> && make validate SPEC=<spec>`

## Adding a New Schema

1. Create `specifications/schemas/<domain>/<SchemaName>.yaml`
2. Reference it from the operation or parent schema via `$ref`
3. Use `title` matching the RM class name
4. Follow existing patterns for `required`, `type`, `properties`, and `description`

## Scope Boundaries

- This skill covers the **OpenAPI YAML and Markdown** sources in `specifications-ITS-REST/specifications/`
- It does NOT cover AsciiDoc documents in `specifications-ITS-REST/docs/` (simplified_formats, smart_app_launch) — use `authoring` for those
- It does NOT cover the PHP build tooling in `development/` — consult `.junie/guidelines.md` for that
- It does NOT cover other `specifications-XX` repositories
