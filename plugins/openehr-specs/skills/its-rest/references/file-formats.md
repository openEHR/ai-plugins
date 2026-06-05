# ITS-REST Source File Formats

Detailed authoring conventions for each ITS-REST source file type. The skill body holds the
repository structure, workflows, and scope; load this file when actually writing or editing a
top-level entry, operation, schema, Markdown description, or the amendment record.

## Top-Level Entry YAML Files

Each API domain has a top-level `*.openapi.yaml` file that defines:

```yaml
openapi: 3.0.3
info:
  title: EHR API
  version: latest
  x-status: STABLE          # Spec lifecycle status
  x-spec: ehr               # Spec identifier
  contact:
    name: Specifications Editorial Committee openEHR
    url: 'https://specifications.openehr.org/'
    email: info@openehr.org
  license:
    name: Creative Commons Attribution-NoDerivs 3.0 Unported
    url: 'https://creativecommons.org/licenses/by-nd/3.0/'
  description:
    $ref: ./docs/ehr/Description.md
servers:
  - url: 'https://{baseUrl}/v1'
    description: An example openEHR server URL.
    variables:
      baseUrl:
        default: openEHRSys.example.com
security: []
paths:
  '/ehr':
    post:
      $ref: ./operations/ehr_create.yaml
    get:
      $ref: ./operations/ehr_get_by_subject.yaml
  # ... more paths
```

### Conventions

- `openapi: 3.0.3` — all specs use this version
- `x-status` — mirrors the `spec_status` lifecycle (STABLE, DEVELOPMENT, TRIAL)
- `x-spec` — identifies the spec for build tooling
- `description` is always a `$ref` to a Markdown file in `docs/<domain>/Description.md`
- Server URL uses `{baseUrl}` variable with `openEHRSys.example.com` as default
- Paths reference operations via `$ref: ./operations/<operation_id>.yaml`

## Operation Files

Each operation lives in `specifications/operations/<operation_id>.yaml`:

```yaml
operationId: composition_create
summary: Create COMPOSITION
description: |
  Creates the first version of a new COMPOSITION in the EHR identified by `ehr_id`.
tags:
  - COMPOSITION
parameters:
  - $ref: ../parameters/path/ehr_id.yaml
  - $ref: ../parameters/header/Prefer.yaml
  - $ref: ../parameters/header/Accept_LOCATABLE.yaml
  - $ref: ../parameters/header/ContentType_LOCATABLE.yaml
requestBody:
  description: |
    The COMPOSITION.
  content:
    application/json:
      schema:
        $ref: ../schemas/ehr/Composition.yaml
  required: true
responses:
  '201':
    $ref: ../responses/201_COMPOSITION.yaml
  '400':
    $ref: ../responses/400.yaml
  '404':
    $ref: ../responses/404_unknown_ehr_id.yaml
  '422':
    $ref: ../responses/422.yaml
```

### Conventions

- `operationId` — unique, snake_case, matches the filename (without `.yaml`)
- `summary` — short imperative phrase (e.g., "Create COMPOSITION", "Get EHR by id")
- `description` — Markdown, uses `|` block scalar for multi-line
- `tags` — one tag matching the RM class or domain (e.g., `EHR`, `COMPOSITION`, `QUERY`)
- Parameters, request bodies, responses, and headers use `$ref` to shared definitions
- Response codes follow HTTP semantics: `201` for creation, `200` for retrieval, `204` for no-content, `4xx` for client errors

### Naming Conventions for Operation Files

```
<resource>_<action>.yaml
```

Examples:
- `ehr_create.yaml`, `ehr_get_by_id.yaml`, `ehr_get_by_subject.yaml`
- `composition_create.yaml`, `composition_get.yaml`, `composition_update.yaml`, `composition_delete.yaml`
- `definition_query_store.yaml`, `definition_query_list.yaml`
- `versioned_composition_get.yaml`, `versioned_composition_revision_history.yaml`

## Schema Files

Schemas live in `specifications/schemas/<domain>/<SchemaName>.yaml`:

```yaml
title: RESULT_SET
required:
  - rows
type: object
properties:
  meta:
    $ref: ./ResultSetMetadata.yaml
  name:
    $ref: ./QueryName.yaml
  columns:
    type: array
    items:
      $ref: ./ResultSetColumn.yaml
    description: |
      A set of AQL column specifications.
  rows:
    type: array
    items:
      $ref: ./ResultSetRow.yaml
```

### Conventions

- Schema file names use PascalCase matching the RM class name
- Schemas reference other schemas via relative `$ref` paths
- `title` should match the RM class name (e.g., `COMPOSITION`, `EHR_STATUS`, `RESULT_SET`)
- Use `description` with `|` block scalar for multi-line Markdown
- Include `example` values where they aid understanding
- Prefixed schemas (`UM*`, `U*`) are internal/simplified variants — see build tooling docs

## Markdown Description Files

Descriptions in `specifications/docs/<domain>/` use Markdown with these conventions:

### Tone and Register

- Same formal register as AsciiDoc specs but uses **RFC 2119 keywords**: MUST, MUST NOT,
  SHOULD, SHOULD NOT, MAY, REQUIRED, OPTIONAL — always in ALL CAPS
- Requirements statement in overview: "The key words 'MUST', 'MUST NOT'... are to be
  interpreted as described in BCP 14 [RFC 2119], [RFC 8174]"
- Third person, present tense, no contractions
- Concrete HTTP examples using code blocks with `http` language tag

### Structure of Description.md

Each domain has a `Description.md`:

```markdown
## Description

### Purpose

This specification describes service endpoints, resources and operations as well as
details of requests and responses that interacts with {Domain} openEHR API in a RESTful manner.

### Related Documents

Prerequisite documents for reading this document include:

- The [{RM Spec Title}](https://specifications.openehr.org/releases/RM/latest/{spec}.html)

Related documents include:

- The [openEHR Architecture Overview](https://specifications.openehr.org/releases/BASE/latest/architecture_overview.html)

### Status

This specification is in the `{STATUS}` state, and can be downloaded as
[OpenAPI specification](https://spec.openapis.org/oas/v3.0.3) file (in YAML format)
[for validation](computable/OAS/{spec}-validation.openapi.yaml), or
[for code generators](computable/OAS/{spec}-codegen.openapi.yaml).
```

### Links

Unlike AsciiDoc specs, ITS-REST Markdown uses **hardcoded URLs** (no Asciidoctor attributes).
Links to other openEHR specs use the full URL:

```markdown
[EHR Information Model](https://specifications.openehr.org/releases/RM/latest/ehr.html)
[Common IM](https://specifications.openehr.org/releases/RM/latest/common.html#_change_control_package)
```

### Code Examples

HTTP request/response examples use fenced code blocks:

````markdown
```http
PUT https://openEHRSys.example.com/v1/ehr/{ehr_id}/composition/{version_uid}
If-Match: "8849182c-82ad-4088-a07f-48ead4180515::openEHRSys.example.com::2"
Prefer: return=representation
Content-Type: application/json
```
````

JSON examples use `json` language tag:

````markdown
```json
{
    "message": "Error message",
    "code": 90000
}
```
````

## Amendment Record

The ITS-REST amendment record uses **HTML tables** (not AsciiDoc) in
`specifications/docs/overview/Amendment_record.md`:

```html
[comment]: # (title: Amendment Record)

<table>
    <colgroup>
        <col style="width: 9%;">
        <col style="width: 55%;">
        <col style="width: 18%;">
        <col style="width: 18%;">
    </colgroup>
    <thead>
    <tr>
        <th>Issue</th>
        <th>Details</th>
        <th>Raiser, Implementer</th>
        <th>Completed</th>
    </tr>
    </thead>
    <tbody>
    <tr>
        <td>N.N</td>
        <td><a href="https://specifications.openehr.org/tickets/SPECITS-NN" target="_blank" rel="noopener">SPECITS-NN</a>:
            Description of change</td>
        <td>Raiser name(s)</td>
        <td>dd Mon yyyy</td>
    </tr>
    <!-- Release boundary -->
    <tr>
        <th colspan="4"><a href="https://specifications.openehr.org/releases/ITS-REST/Release-N.N.N" target="_blank" rel="noopener">Release-N.N.N</a></th>
    </tr>
    </tbody>
</table>
```

### Key Differences from AsciiDoc Amendment Records

| Aspect | AsciiDoc specs | ITS-REST |
|--------|---------------|----------|
| Format | AsciiDoc table | HTML table |
| Jira project | `SPECRM`, `SPECAM`, etc. | `SPECITS` |
| Jira link syntax | `{spec_tickets}/SPECITS-NN[SPECITS-NN^]` | `<a href="https://specifications.openehr.org/tickets/SPECITS-NN">SPECITS-NN</a>` |
| Release boundary | `4+^h\|*XX Release N.N.N*` | `<th colspan="4"><a href="...">Release-N.N.N</a></th>` |
| Anchors | `[[latest_issue]]`, `[[latest_issue_date]]` | Not used (no front matter linkage) |
| Column header | "Raiser" | "Raiser, Implementer" |
