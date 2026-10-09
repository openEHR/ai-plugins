---
name: bmm-authoring
description: >
  Create or edit an openEHR component's BMM schema, the P_BMM JSON in `computable/BMM/` of a
  `specifications-XX` repo. This skill should be used when the user asks to write a BMM schema from
  scratch, add, rename or remove a class, attribute, function, invariant or enumeration in the
  model, set the schema header or includes, or check or fix a `.bmm.json`. Not for regenerating class
  tables (use class-generation), spec prose (use content-patterns), or archetype/template work
  (openehr-assistant plugin).
allowed-tools:
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check_bmm.py *)"
---

# openEHR BMM Schema Authoring (P_BMM JSON)

A component's BMM schema, `computable/BMM/openehr_<component>_<release>.bmm.json`, is the source of
truth for its classes. The class tables and diagrams in its documents are generated from it (see
`class-generation`), and
[`specifications-ITS-BMM`](https://github.com/openEHR/specifications-ITS-BMM) republishes it as JSON,
ODIN and YAML. Change the model here, and only here.

- **Format reference**: `${CLAUDE_SKILL_DIR}/references/p-bmm-json.md`. Before editing, read the
  sections for the constructs involved (its Contents lists header, packages, every class, property,
  type and function kind, what the tables show, and the spec features the toolchain does not read).
- **Worked example**: `${CLAUDE_SKILL_DIR}/assets/openehr_demo_0.1.0.bmm.json`, one of each common construct.
- **Checker**: `${CLAUDE_SKILL_DIR}/scripts/check_bmm.py` (Python 3.8+, standard library only, read-only).

## Related Skills

- **class-generation**: regenerate and place the class tables after a change
- **authoring**: the chapter `include::` lines for a new or removed class
- **amendment-record**: the entry for a change to published specification text
- **governance**: releases, and the lifecycle state a schema header names
- **content-patterns**: the prose around classes, which the tables do not carry
- **scaffold**: writes a new repository's schema, the image's bundled copy or an empty one
  (`/openehr-specs:scaffold`)

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

1. Read the header and the classes next to the one being changed, and follow their idiom. Run the
   checker once before editing (step 4) and save its output with stderr (`2>&1`) to a temp file
   outside the repo (`mktemp`): the published schemas carry findings of their own, and comparing
   that output with the one after the change separates theirs from the new ones.
2. Make the change, using the format reference. Ground every class, attribute and function name in
   the specification text being written or in the user's instruction; never invent one.
3. Increase the build number in `schema_revision` once per change set (`1.3.0.2` → `1.3.0.3`);
   if `git diff` against the base branch already shows a bump, leave it. If the release is already
   published, whether the change belongs in it or in a new release (a new `rm_release`, file and
   schema id, which the `includes` of dependent schemas then name) is a decision for the user; see
   `governance`.
4. Run the checker, passing each included schema with `-d` (from its sibling clone):
   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/check_bmm.py computable/BMM/openehr_rm_1.2.0.bmm.json \
     -d ../specifications-BASE/computable/BMM/openehr_base_1.3.0.bmm.json
   ```
   Save the output again and `diff` it with the step 1 output; fix every ERROR and WARNING the
   change added. A non-zero "N name(s) not checked" in the summary (with an "incomplete" notice)
   means an included schema was not loaded: the exit status is 3 when there are no errors, 1 when
   there are. If the sibling clone is missing, say the check is incomplete; never report such a run
   as clean.
5. Regenerate the class tables (`class-generation`) and read the table of every class touched.
   Expect the gaps listed under "What the class tables show" in the reference, such as a container's
   member count or a generic parameter's constraint.
6. A new class or package needs its `include::` line in a chapter, and a removed class loses its line
   (`authoring`); the reference's Packages section gives each table's file name. For a rename or
   removal, search the component's chapters, and the components whose schemas include this one, for
   the old name and, for a class, its `_<name in lower case>_class` anchor. Then dispatch
   `identifier-grounding` and `xref-auditor` on the affected documents.
7. Add the amendment-record entry. When asked to commit, commit the source changes (the BMM, the
   `include::` lines, the amendment record) together, following the Conventions in the repo's
   `AGENTS.md`; leave regenerated tables and HTML unstaged unless the task is to refresh them.

### Writing a schema from scratch

1. If `computable/BMM/` already holds an empty schema for the component (the `scaffold` skill writes
   one), fill that in; rename its single root package `org.openehr.<schema_name>` to the packages step
   3 names, and confirm its `schema_author` and `schema_lifecycle_state` with the user. Otherwise copy
   `${CLAUDE_SKILL_DIR}/assets/openehr_demo_0.1.0.bmm.json` to `computable/BMM/<schema id>.bmm.json`
   and replace every header value, `packages` and `class_definitions`. Set the header from the
   reference's header table: `schema_name` is the lower-case component, `rm_release` the first release
   the user confirms (scaffold's `first_release` in a new repo), `schema_revision` `<rm_release>.1`.
   Ask the user for `schema_author` rather than guessing it.
2. Include BASE (`"includes": {"openehr_base_<version>": {"id": "openehr_base_<version>"}}`) and use
   its types (`Any`, `String`, `List`, `Hash`, `HIER_OBJECT_ID`, …). Do not redefine them;
   `primitive_types` belongs to BASE only.
3. Name top-level packages `org.openehr.<schema_name>.<package>`, one for each `:pkg:` the
   component's `master.adoc` files set (see the reference's Packages section). If no `master.adoc`
   sets `:pkg:` yet, agree the package names with the user and set `:pkg:` to match (`authoring`).
   Group the classes in sub-packages as the chapters do, at most four package levels deep.
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
- Exit status: 0 complete, no errors (read any warnings: an undefined type name is one); 1 errors
  found (with `--strict`, warnings count too); 3 no errors, but names from an included schema not
  loaded with `-d` went unchecked; 2 a file is unreadable, not UTF-8 JSON, nested too deeply, or (for
  `-d`) not a BMM schema. The summary line always gives the unchecked count.
- The published schemas carry findings of their own, which the step 1 baseline shows. Report
  findings outside the change to the user; do not fix them as a side effect.
- If `python3` is missing, say so and report the schema as unchecked; review the change by hand
  against the reference's Properties and Types sections and its table of specification features
  bmm-publisher does not read, before rendering. In a tool that does not expand
  `${CLAUDE_SKILL_DIR}`, use the directory that holds this SKILL.md.

## Guardrails

- **Edit the JSON in place.** The files mix PHP-style escapes (`\/`, `\u2260`) with raw characters
  from later edits, so loading and re-serialising a file rewrites lines nobody touched. Keep the
  file's indentation (4 spaces in the published schemas) and key order, and check that `git diff`
  shows only the intended change.
- **Edit only `computable/BMM/` in the component repo.** Never the ITS-BMM copies, the generated
  `docs/UML/classes` tables, or the schemas bundled in `bmm-publisher`.
- **Keys equal names.** Every entry of a map of named things (packages, classes, properties,
  functions, parameters, constants, generic parameters) is keyed by its own `name`.
- **Use the forms bmm-publisher reads** (see the reference's table of unsupported specification
  features) and describe in `documentation` what they cannot express.
