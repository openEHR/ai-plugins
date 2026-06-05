# manifest.json Specification Entry Reference

Each component's `manifest.json` contains a `specifications` array. Here is the full field reference for a specification entry:

```json
{
    "id": "ehr",
    "title": "EHR Information Model",
    "title_short": "EHR",
    "description": "openEHR EHR Information Model specification",
    "summary": "The information model of the openEHR EHR.",
    "micro_summary": "Top-level health record info model",
    "classes": ["COMPOSITION", "SECTION", "ENTRY", "OBSERVATION", "EVALUATION", "INSTRUCTION", "ACTION", "ADMIN_ENTRY"],
    "copyright_year": "2003",
    "spec_status": "STABLE",
    "keywords": "EHR, EMR, reference model, openehr",
    "notes": [
        {
            "link": "https://openehr.atlassian.net/wiki/...",
            "text": "Wiki design page"
        }
    ]
}
```

## Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Identifier string matching the spec directory name under `docs/`. Lowercase, underscored. |
| `title` | Yes | Full title shown on front page below the openEHR logo. |
| `title_short` | No | Short title used in the component index page. |
| `description` | Yes | Usually `"openEHR <Title> specification"`. Used for hover text and browser tab titles. |
| `summary` | Yes | Longer description for the right-hand column of the component index page. |
| `micro_summary` | No | Shortened version of summary for the home page box. May be empty. |
| `classes` | No | Key RM/AM classes. Each is linked to the spec source location on the specifications site. |
| `copyright_year` | Yes | Year of first publication (e.g., `"2003"`). |
| `spec_status` | Yes | One of: `DEVELOPMENT`, `TRIAL`, `STABLE`, `SUPERSEDED`, `OBSOLETE`, `RETIRED`. |
| `keywords` | Yes | Comma-separated keywords affecting search engines. |
| `notes` | No | Array of `{link, text}` objects pointing to wiki pages or other supplementary material. |

## Top-Level manifest.json Structure

```json
{
    "id": "RM",
    "title": "Reference Model",
    "description": "openEHR Reference Model Component",
    "keywords": "reference model, openehr",
    "specifications": [ ... ],
    "expressions": [
        {
            "id": "openEHR_UML-RM.mdzip",
            "type": "uml",
            "title": "RM UML",
            "description": "UML file for MagicDraw 19. Contains UML 2.5 standard XMI file."
        },
        {
            "id": "openEHR_UML-BASE.mdzip",
            "dependency": {
                "component": "BASE",
                "release": "latest"
            }
        }
    ],
    "jira": {
        "open_issues": "11103",
        "roadmap": "SPECRM"
    },
    "releases": [
        {
            "id": "1.1.0",
            "date": "2020-09-29",
            "jira": {
                "crs": "SPECRM/versions/12516",
                "prs": "SPECPR/versions/10061"
            }
        }
    ]
}
```

## Releases Array

Releases are listed newest-first. A release with an empty `"date"` means it is not yet released
(i.e., it is the "cooking" release currently in development).

When creating a new release:
1. Prepend a new entry with empty `"date"` for the next development cycle
2. Set the `"date"` on the release being published to the current date (`YYYY-MM-DD`)
3. Ensure `"jira"` links point to the correct Jira version IDs

## Expressions Array

Expressions are computable artifacts associated with the component:
- **`type: "uml"`** — UML model file. Historically a MagicDraw `.mdzip`; class tables and diagrams are now generated from the component's BMM schema by `bmm-publisher` (see the `class-generation` skill).
- **`dependency`** — references an expression from another component (inherited)
