---
name: bmm-authoring
description: >
  Create or edit an openEHR component's BMM schema, the P_BMM JSON in `computable/BMM/` of a
  `specifications-XX` repo. This skill should be used when the user asks to write a BMM schema from
  scratch, add, rename or remove a class, attribute, function, invariant or enumeration in a
  component's model, set the schema header or includes, or check a hand-edited `.bmm.json`. Not for
  regenerating class tables (use class-generation) or spec prose (use content-patterns).
allowed-tools:
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check_bmm.py *)"
---

# openEHR BMM Schema Authoring (P_BMM JSON)

A component's BMM schema, `computable/BMM/openehr_<component>_<release>.bmm.json`, is the source of
truth for its classes. The class tables and diagrams in its documents are generated from it (see
`class-generation`), and
[`specifications-ITS-BMM`](https://github.com/openEHR/specifications-ITS-BMM) republishes it as JSON,
ODIN and YAML. Change the model here, and only here.

- **Format reference**: `references/p-bmm-json.md` (header, packages, every class, property, type and
  function kind, what the tables show, spec features the toolchain does not read).
- **Worked example**: `${CLAUDE_SKILL_DIR}/assets/openehr_demo_0.1.0.bmm.json`, one of each construct.
- **Checker**: `${CLAUDE_SKILL_DIR}/scripts/check_bmm.py` (Python 3.8+, standard library only, read-only).

## Related Skills

- **class-generation**: regenerate and place the class tables after a change
- **authoring**: the chapter `include::` lines for a new or removed class
- **amendment-record**: the entry for a change to published specification text
- **governance**: releases, and the lifecycle state a schema header names
- **content-patterns**: the prose around classes, which the tables do not carry

## Why the Checker Comes Before the Render

`bmm-publisher` exits 0 on most modelling mistakes and renders something else in their place:

- a misspelt or missing `_type` falls back to a single property or a simple type, often of type `Any`;
- an unknown key (`is_mandantory`) is ignored without a message;
- a class missing from `packages` gets no table;
- `{"lower": 2, "upper": 5}` loses its upper limit unless `"upper_unbounded": false` is written out;
- spec constructs it does not read (indexed containers, `ancestor_defs`, `type_ref` value sets) are
  dropped.

A clean run therefore proves little. `check_bmm.py` reports each of these, so run it first, then
render and read the tables.

## Workflow

### Changing a schema

1. Read the header and the classes next to the one you are changing, and follow their idiom. Run the
   checker once before editing (step 4) and keep its output: the published schemas carry findings
   of their own, and that output separates them from yours.
2. Make the change, using the format reference. Ground every class, attribute and function name in
   the specification text being written or in the user's instruction; never invent one.
3. Increase the build number in `schema_revision` (`1.3.0.2` → `1.3.0.3`). If the release is already
   published, whether the change belongs in it or in a new release (a new `rm_release`, file and
   schema id, which the `includes` of dependent schemas then name) is a decision for the user; see
   `governance`.
4. Run the checker, passing each included schema with `-d` (from its sibling clone):
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/check_bmm.py computable/BMM/openehr_rm_1.2.0.bmm.json \
     -d ../specifications-BASE/computable/BMM/openehr_base_1.3.0.bmm.json
   ```
   Fix every ERROR and WARNING that was not in the step 1 output.
5. Regenerate the class tables (`class-generation`) and read the table of every class you touched.
   Expect the gaps listed under "What the class tables show" in the reference, such as a container's
   member count or a generic parameter's constraint.
6. A new class or package needs its `include::` line in a chapter, and a removed class loses its line
   (`authoring`). Each table is named after the first four parts of its class's package path and the
   class name in lower case: `LOCATABLE` in `org.openehr.rm.common` → `archetyped` gives
   `org.openehr.rm.common.locatable.adoc`, included as `{pkg}locatable.adoc`.
7. Add the amendment-record entry. When asked to commit, commit the BMM change on its own, as the
   repo's `AGENTS.md` says; leave regenerated tables and HTML unstaged unless the task is to refresh
   them.

### Writing a schema from scratch

1. If `computable/BMM/` already holds an empty schema for the component, fill that in. Otherwise
   copy `${CLAUDE_SKILL_DIR}/assets/openehr_demo_0.1.0.bmm.json` to
   `computable/BMM/<schema id>.bmm.json` and replace its content. Set the header from the
   reference's header table: `schema_name` is the lower-case component, `rm_release` the release,
   `schema_revision` `<rm_release>.1`. Ask the user for `schema_author` rather than guessing it.
2. Include BASE (`"includes": {"openehr_base_<version>": {"id": "openehr_base_<version>"}}`) and use
   its types (`Any`, `String`, `List`, `Hash`, `HIER_OBJECT_ID`, …). Do not redefine them;
   `primitive_types` belongs to BASE only.
3. Give each specification document of the component one top-level package,
   `org.openehr.<schema_name>.<package>`, matching the `:pkg:` that document's `master.adoc` sets
   (`org.openehr.<schema_name>.<package>.`): RM has `org.openehr.rm.common`, `org.openehr.rm.ehr`
   and others; TERM has the one package `org.openehr.term.terminology`. Group its classes in
   sub-packages as the document's chapters do.
4. Add the classes, then continue from step 4 of "Changing a schema".

## Quick Reference

| To model | Write |
|----------|-------|
| `uid: HIER_OBJECT_ID`, mandatory | `P_BMM_SINGLE_PROPERTY`, `"type": "HIER_OBJECT_ID"`, `"is_mandatory": true` |
| `items: List<ITEM>`, never empty | `P_BMM_CONTAINER_PROPERTY`, `type_def` `{"container_type": "List", "type": "ITEM"}`, `cardinality` `{"lower": 1, "upper_unbounded": true}`, `"is_mandatory": true` |
| `ranks: List<Integer>`, 2 to 5 members | `cardinality` `{"lower": 2, "upper": 5, "upper_unbounded": false}` |
| `index: Hash<String, ITEM>` | `P_BMM_GENERIC_PROPERTY`, `type_def` `{"root_type": "Hash", "generic_parameters": ["String", "ITEM"]}` |
| `content: T` in `BOX<T: ITEM>` | class `generic_parameter_defs` `{"T": {"name": "T", "conforms_to_type": "ITEM"}}`; property `P_BMM_SINGLE_PROPERTY_OPEN`, `"type": "T"` |
| `List<BOX<GROUP>>` | container `type_def` holding a nested `type_def` with `"_type": "P_BMM_GENERIC_TYPE"` |
| `B` inherits `A` | `"ancestors": ["A"]` |
| `B<T>` inherits `A<T>` (open binding) | `"ancestors": ["A"]`, and redeclare `T` in `B`'s `generic_parameter_defs` |
| `B` inherits `A<Integer>` (closed binding) | `"ancestors": ["A"]` only, and state the binding in `documentation` |
| String enumeration | `"_type": "P_BMM_ENUMERATION_STRING"`, `"ancestors": ["String"]`, `item_names`, `item_documentations` |
| Function | `functions` entry: `parameters`, `result` (a type object with its `_type`), `pre_conditions`, `post_conditions` |
| Invariant | `"invariants": {"Name_valid": "not name.is_empty()"}` |

## The Checker

- Each finding is `ERROR`, `WARNING` or `INFO`, with a JSON path. ERROR means bmm-publisher fails,
  reads something other than what the file says (a misspelt `is_mandatory` included), or a generic
  argument does not conform to its parameter's `conforms_to_type`. WARNING means a broken convention
  or content the publisher ignores. INFO lists what could not be checked, typically type names from
  an included schema that was not passed with `-d`.
- Exit status 1 means errors were found (with `--strict`, warnings count too); 2 means the file is
  unreadable or not JSON.
- The published schemas carry some warnings and a few errors of their own, such as missing
  documentation, or AM 2.4.0's `P_ARCHETYPE_SLOT.includes`, a `List` with no element type that renders
  as `List<Any>`. Report findings outside your change to the user; do not fix them as a side effect.
- If `python3` is missing, say so, check the change by hand against the reference's lists, and
  render. In a tool that does not expand `${CLAUDE_SKILL_DIR}`, use the directory that holds this
  SKILL.md.

## Guardrails

- **Edit the JSON in place.** The files mix PHP-style escapes (`\/`, `\u2260`) with raw characters
  from later edits, so loading and re-serialising a file rewrites lines you did not touch. Keep the
  4-space indentation and key order, and check that `git diff` shows only your change.
- **Edit only `computable/BMM/` in the component repo.** Never the ITS-BMM copies, the generated
  `docs/UML/classes` tables, or the schemas bundled in `bmm-publisher`.
- **Keys equal names.** Every map entry is keyed by its own `name`.
- **Use the forms bmm-publisher reads** (see the reference's table of unsupported specification
  features) and describe in `documentation` what they cannot express.
