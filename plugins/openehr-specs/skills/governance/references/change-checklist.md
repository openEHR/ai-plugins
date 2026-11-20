# Change checklist: what a change has to touch

The change workflow (`change-workflow.md`) says who decides a change and when. This list says
what to check while making it, so that the text, the model, the schemas and the reference
implementation still say the same thing afterwards. It is a working aid of this plugin, not part
of the workflow the SEC approved.

Go through it for every change, in this order. Most changes stop after one or two steps; a
step that is not affected is still looked at, and the result is recorded (last section).

## Working order

| # | Step | Where | What to do |
|---|---|---|---|
| 1 | **BMM** | `computable/BMM/*.bmm.json` in the component repository (AM, BASE, LANG, RM, TERM) | A change to a class, attribute, type, cardinality, function, invariant or class description starts here, never in the text: edit the schema and bump `schema_revision` (bmm-authoring skill), then regenerate the class tables (class-generation skill). Never edit `docs/UML/classes/` by hand |
| 2 | **Text** | `docs/<document>/master*.adoc` | The hand-written prose that states the same thing, in this document and in every other document or component that repeats it. Add the amendment-record entry (amendment-record skill) |
| 3 | **Examples** | In the text, and in the downstream repositories | Every example that shows what changed: code blocks and included files in the chapters, the XML instances in `specifications-ITS-XML/examples/`, the example operations and responses in `specifications-ITS-REST/specifications/` |
| 4 | **Downstream** | The ITS repositories, the grammars, the terminology | See the table below |
| 5 | **Archie** | `openEHR/archie` | A pull request when the implementation no longer matches, see "Archie" |

A change with no model part skips step 1 and starts with the text.

## Step 4: downstream artefacts

| Artefact | Repository and path | Affected when |
|---|---|---|
| BMM mirrors (JSON, ODIN, YAML) | `specifications-ITS-BMM/components/<COMPONENT>/` | Every BMM change. Not edited by hand: the JSON is imported from the component repository and the ODIN and YAML are regenerated (that repository's `AGENTS.md`; `../../bmm-authoring/references/p-bmm-json.md`). Check that the mirror carries the new `schema_revision` |
| XML schemas | `specifications-ITS-XML/components/<COMPONENT>/` (RM, AM, BASE, OET, QUERY) | A class, attribute, type or cardinality that is serialised changes |
| JSON schemas | `specifications-ITS-JSON/components/<COMPONENT>/` (RM, AM, BASE) | The same |
| OpenAPI files, simplified formats | `specifications-ITS-REST` (its-rest skill) | A type the REST API carries, or a rule of the simplified formats, changes |
| ADL, cADL and ODIN grammars | `adl-antlr`, `src/main/antlr/adl/` | The syntax of ADL 1.4, ADL2, ODIN or the base expressions changes |
| AQL grammar | `specifications-QUERY/docs/AQL/grammar/` | The AQL syntax changes |
| Terminology | `specifications-TERM/computable/XML/` | A code, code set or vocabulary the text names is added, changed or removed. The FHIR files are generated from the XML (that repository's `AGENTS.md`) |

Each repository's `AGENTS.md` says which files are sources and which are generated, and which
release directory a change goes into. The ITS schemas are published per component release, so
a change may need a new schema release there; say so in the pull request instead of deciding it.

## What kind of change needs which step

| Change | 1 BMM | 2 Text | 3 Examples | 4 Downstream | 5 Archie |
|---|---|---|---|---|---|
| Prose only, meaning unchanged | no | yes | no | no | no |
| Class description | yes | where the prose repeats it | no | BMM mirrors | no |
| Class, attribute, type or cardinality | yes | yes | check | BMM mirrors, XML and JSON schemas, OpenAPI | check |
| Function or invariant | yes | yes | check | BMM mirrors | check |
| Syntax (ADL, ODIN, AQL, expressions) | no | yes | check | grammar | check |
| Code, term or code set | no | yes | check | terminology | check |
| Wire format (XML, JSON, REST) | no | yes | check | that ITS repository | check |

"Check" means: look, and record what was found. The table is a starting point; a change that
fits no row is checked against all five steps.

## Archie

[Archie](https://github.com/openEHR/archie) is the reference implementation, not a
specification. Look at the part that implements what changed: `grammars/` (its ADL and AQL
grammars), `aom/`, `openehr-rm/`, `bmm/`, `openehr-terminology/`.

- Archie already does what the new text says: no pull request; record it.
- Archie differs: open a pull request there as a **draft** that links the collection pull
  request, and take it out of draft once the specification change is approved.
- The Archie pull request is not part of the collection: it needs no SEC approval, it is not
  listed under the collection's `Related:`, and the specification pull requests do not wait
  for it. The checklist line of the collection names it (last section).

Other implementations are out of scope; name a known effect on them under Impact.

## Pull requests and order of merging

- Steps 1 to 3 inside one component repository are one pull request. Every other repository
  that changes gets its own, under one collection pull request (`change-workflow.md`, "One
  change, several pull requests").
- The working order above is not the order of merging: the pull requests are merged together,
  the collection, normally the one with the text, last.
- The level (Fix, Minor change, Major change) is that of the whole change, not of the smallest
  pull request in it.

## Recording the result

A step that was checked and found unaffected is a finding, and the approver has to be able to
see it. In the collection pull request, under Details, Review (tracker-writing skill), give the
result in one line:

```
Checklist: changed BMM, class tables, XML schema; not affected: JSON schema, grammar, examples; Archie: draft <URL>; not checked: <what, and why>
```

Write "not affected" only after looking. A prose-only Fix needs no line.
