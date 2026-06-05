# Cross-Reference Attribute Guide

This reference applies exclusively to the openEHR specification ecosystem — the AsciiDoc sources
in `specifications-XX` repositories and their shared infrastructure in `specifications-AA_GLOBAL`.

openEHR specifications use Asciidoctor attributes for all cross-references. These attributes are defined in three tiers, resolved at publish time.

## Attribute Tiers

### Tier 1: Global Variables (`specifications-AA_GLOBAL/docs/boilerplate/global_vars.adoc`)

Defines foundational attributes used everywhere:

| Category | Examples | Pattern |
|----------|----------|---------|
| Sites | `{openehr_specs}`, `{openehr_git}`, `{openehr_forums_site}` | `{openehr_*}` |
| Release versions | `{rm_release}`, `{am_release}`, `{base_release}` | `{component_release}` — defaults to `latest` |
| UML paths | `{uml_export_dir}`, `{uml_diagrams_uri}` | Used for generated class docs and diagrams |
| Diagram paths | `{diagrams_uri}`, `{images_uri}` | Resolve to `{doc_name}/diagrams` and `{doc_name}/images` |
| Common paths | `{common_diagrams_uri}`, `{common_images_uri}` | For shared diagrams across specs in a component |
| Jira | `{spec_tickets}`, `{component_prs}`, `{component_history}`, `{component_roadmap}` | `{component}` is set per-repo |
| Forums | `{openehr_rm_forum}`, `{openehr_adl_forum}`, `{openehr_aql_forum}` | Per-topic discussion links |
| Class index | `{classes_url_root}` | Links to specification site class index |

### Tier 2: Reference Definitions (`specifications-AA_GLOBAL/docs/references/reference_definitions.adoc`)

Defines all cross-spec and external URLs. Organised by component and external standard.

### Tier 3: Per-Document Variables (`manifest_vars.adoc`)

Each spec document defines local attributes:

```asciidoc
:spec_title: EHR Information Model
:copyright_year: 2003
:spec_status: STABLE
:keywords: EHR, EMR, reference model, openehr
:description: openEHR EHR Information Model specification
```

## openEHR Spec Cross-Reference Patterns

All openEHR spec references follow predictable naming. Learn the pattern rather than memorising every attribute.

### Component base URL

```
:{component_id}_releases: {openehr_specs}/releases/{COMPONENT}/{component_id_release}
```

Where `{component_id}` is lowercase (e.g., `rm`, `am`, `base`, `query`, `proc`, `sm`, `lang`, `cnf`, `term`).

Examples:
- `:openehr_rm_releases:` resolves to `https://specifications.openehr.org/releases/RM/{rm_release}`
- `:openehr_am_releases:` resolves to `https://specifications.openehr.org/releases/AM/{am_release}`

### Spec document links (three variants)

For a spec with id `{spec_id}` in component `{comp}`:

| Variant | Attribute pattern | Resolves to |
|---------|------------------|-------------|
| Release-relative | `{openehr_{comp}_{spec_id}}` | `{openehr_{comp}_releases}/{spec_id}.html` |
| Latest | `{openehr_{comp}_latest_{spec_id}}` | `.../releases/{COMP}/latest/{spec_id}.html` |
| Development | `{openehr_{comp}_development_{spec_id}}` | `.../releases/{COMP}/development/{spec_id}.html` |

**Examples — RM component:**
- `{openehr_rm_common}` — Common IM at current release
- `{openehr_rm_latest_common}` — Common IM at latest release
- `{openehr_rm_latest_ehr}` — EHR IM at latest release

**Examples — AM component:**
- `{openehr_am_adl2}` — ADL2 spec at current release
- `{openehr_am_aom2}` — AOM2 spec at current release
- `{openehr_am_development_adl2}` — ADL2 at development

**Examples — BASE component:**
- `{openehr_foundation_types}` — Foundation Types (note: no `base_` prefix for this one)
- `{openehr_base_types}` — Base Types
- `{openehr_overview}` — Architecture Overview (also no `base_` prefix)
- `{openehr_resource}` — Resource spec

**Examples — QUERY component:**
- `{openehr_query_aql}` — AQL spec
- `{openehr_query_aql_examples}` — AQL Examples

### Deep links (anchors within a spec)

Append `#anchor` to any spec attribute:
```asciidoc
{openehr_rm_data_types}#dv_quantity[DV_QUANTITY^]
{openehr_rm_common}#change_control_package[Change Control^]
{openehr_base_types}#_identification_package[Identification Package^]
{openehr_overview}#_paths_and_locators[Paths and Locators^]
```

### Usage in text

Always include display text and external link marker (`^`):
```asciidoc
the {openehr_rm_common}[Common IM^]
the {openehr_am_aom2}[AOM2 specification^]
{openehr_foundation_types}[Foundation Types^]
```

For links to specific classes in the specifications site class index:
```asciidoc
{classes_url_root}/COMPOSITION[COMPOSITION^]
```

### Preface Status link

Each preface uses the `_development_` variant to link to the development version of itself:
```asciidoc
This specification is in the {spec_status} state. The development version of this document can be found at {openehr_rm_development_ehr}[{openehr_rm_development_ehr}^].
```

### Preface Feedback links

Standard pattern using per-component variables (set automatically from `{component}`):
```asciidoc
Feedback may be provided on the {openehr_rm_forum}[openEHR RM specifications forum^].
Issues may be raised on the {component_prs}[specifications Problem Report tracker^].
To see changes made due to previously reported issues, see the {component_history}[{component} component Change Request tracker^].
```

## External Standard References

Attributes are grouped by organisation in `reference_definitions.adoc`.

### ISO standards
Pattern: `{iso_NNNNN}` — links to `https://www.iso.org/standard/NNNNN.html`

Common ones:
- `{iso_8601}` — Date/time (Wikipedia link)
- `{iso_13606}`, `{iso_13606-1}` through `{iso_13606-4}` — EHR communication
- `{iso_18308}` — EHR requirements
- `{iso_2788}` — Monolingual thesauri
- `{iso_5964}` — Multilingual thesauri

### IETF RFCs
Pattern: `{rfcNNNN}` — links to `https://tools.ietf.org/html/rfcNNNN`

Common ones:
- `{rfc3986}` — URIs
- `{rfc4880}` — OpenPGP
- `{rfc4122}` — UUIDs
- `{rfc5646}` — Language tags

### HL7
Pattern: `{hl7_*}` — various HL7 resources

Common ones:
- `{hl7}` — HL7 site root
- `{hl7_fhir}` — FHIR base
- `{hl7_cda}` — CDA
- `{hl7v3_rim}` — RIM
- `{hl7_cql}` — CQL

### W3C
- `{w3c_xml_schema}`, `{w3c_xpath}`, `{xquery}`, `{w3c_owl}`, `{w3c_sparql}`

### OMG
- `{omg_uml}`, `{omg_ocl}`, `{omg_idl}`, `{omg_bpmn}`, `{omg_cmmn}`, `{omg_dmn}`

### Clinical / e-Health
- `{snomed_ct}` — SNOMED CT
- `{loinc}` — LOINC
- `{who_icd}` — ICD
- `{ucum}` — UCUM units

### Wikipedia
Pattern: `{wikipedia_*}` — links to `https://en.wikipedia.org/wiki/*`

- `{wikipedia_sql}`, `{wikipedia_oql}`, `{wikipedia_lambda_calculus}`, etc.

### General IT
- `{semver}` — Semantic Versioning
- `{json}` — JSON.org
- `{graphql}` — GraphQL
- `{commonmark_spec}` — CommonMark

## Jira Ticket References

For referencing Jira tickets in amendment records and body text:
```asciidoc
{spec_tickets}/SPECRM-87[SPECRM-87^]
{spec_tickets}/SPECPR-265[SPECPR-265^]
```

The `{spec_tickets}` attribute resolves to the specifications site ticket URL pattern. The Jira project keys are:
- `SPECPR` — Problem Reports (cross-component)
- `SPECRM`, `SPECAM`, `SPECBASE`, `SPECQUERY`, `SPECPROC`, `SPECSM`, `SPECLANG`, `SPECCNF`, `SPECTERM` — Change Requests per component
- `SPECPUB` — Publishing issues

## When Unsure

**Do not guess attribute names.** Instead:

1. Search `reference_definitions.adoc` for the target spec or standard name
2. Search `global_vars.adoc` for infrastructure attributes
3. Follow the naming patterns above to construct the expected name, then verify it exists

The files are at:
- `/src/openehr/specifications-AA_GLOBAL/docs/boilerplate/global_vars.adoc`
- `/src/openehr/specifications-AA_GLOBAL/docs/references/reference_definitions.adoc`
