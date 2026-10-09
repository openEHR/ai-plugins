# P_BMM JSON — format reference

The openEHR BMM schemas in `specifications-XX/computable/BMM/*.bmm.json` are JSON serialisations of
the `P_BMM_*` classes of the
[BMM Persistence specification](https://specifications.openehr.org/releases/LANG/development/bmm_persistence.html)
(LANG, development version; [Markdown](https://specifications.openehr.org/releases/LANG/development/bmm_persistence.md)).
Its chapter "Persistence Package" holds the class tables, the normative list of attributes; its
chapter "BMM Persistence Syntax" names JSON as the primary format of
[`bmm-publisher`](https://github.com/openEHR/bmm-publisher) and shows the rules, mostly in ODIN.
P_BMM version 2.4 added functions, constants and invariants to the structural features.

This reference describes the JSON that the published schemas use and that bmm-publisher reads,
through its parser library [`cadasto/openehr-bmm`](https://github.com/Cadasto/openehr-bmm). Where
the specification and the toolchain differ, both are stated. It was checked against bmm-publisher
0.12.0 (parser 0.3.0); the published-schema counts and defects named here are those found at the
time of writing.

`assets/openehr_demo_0.1.0.bmm.json` is a complete worked example with one each of the common
constructs. It passes `scripts/check_bmm.py` and renders with `bmm-publisher`.

## Contents

- [The file](#the-file)
- [Header](#header)
- [Includes](#includes)
- [Packages](#packages)
- [Classes](#classes)
- [Properties](#properties)
- [Types](#types)
- [Functions](#functions)
- [Invariants, constants and conditions](#invariants-constants-and-conditions)
- [Documentation text](#documentation-text)
- [What the class tables show](#what-the-class-tables-show)
- [Specification features bmm-publisher does not read](#specification-features-bmm-publisher-does-not-read)
- [Reading the specification's ODIN and YAML examples](#reading-the-specifications-odin-and-yaml-examples)

## The file

- One file per component release, named after its schema id: `<rm_publisher>_<schema_name>_<rm_release>.bmm.json`,
  for example `openehr_rm_1.2.0.bmm.json`. (LANG also carries `openehr_lang_1.1.0-bmm3.bmm.json`, an
  overlay with the same schema id; the checker flags its name.)
- The working copy is in the component's `specifications-XX` repo under `computable/BMM/`.
  [`specifications-ITS-BMM`](https://github.com/openEHR/specifications-ITS-BMM) publishes the JSON
  with the ODIN and YAML forms it generates from it, never edited by hand. A component repo that
  carries ITS-BMM's notify workflow (its `.github/sender-workflow-example.yml`) sends each change
  on a push to `master`; without it, the update is made in ITS-BMM.
- Every map of named things (`packages`, `class_definitions`, `properties`, `functions`,
  `parameters`, `constants`, a class's `generic_parameter_defs`) is keyed by the item's own `name`, as
  the specification requires. Keep the two equal: the parser keeps the key for function `parameters`
  (the parameter documentation in the table prints it) and uses `name` everywhere else. A type's
  `generic_parameter_defs` holds type objects, which have no `name`: key them by the root class's
  parameter names (see [Types](#types)).

## Header

`P_BMM_SCHEMA` and its parent `BMM_SCHEMA_CORE` define the header. bmm-publisher refuses a file that
lacks a field marked *yes*.

| Field | Required | Value |
|-------|----------|-------|
| `bmm_version` | no (the specification requires it) | the P_BMM version, `"2.4"`. bmm-publisher assumes `2.4` when it is missing and writes back what it read |
| `rm_publisher` | yes | `"openehr"` |
| `schema_name` | yes | lower-case component name: `base`, `rm`, `am`, `lang`, `term` |
| `rm_release` | yes | 3-part release, `"1.2.0"`; part of the schema id and the file name |
| `schema_revision` | yes | `<rm_release>.<build>`, for example `"1.2.0.2"`. Increase the build number with every change: ITS-BMM expects each schema change to bump it |
| `schema_lifecycle_state` | yes | no value set is defined, and every published schema says `"stable"`. For an unreleased schema, suggest the specification's lifecycle state in lower case (`development`, `trial`; see the `governance` skill) and confirm it with the user |
| `schema_description` | yes | one sentence |
| `schema_author` | yes | the published schemas use `Name <email>`; ask the user who to name |
| `includes` | no | see below |
| `packages` | yes | see below |
| `primitive_types` | no | class definitions of primitive types; only BASE has them |
| `class_definitions` | no | all other class definitions; optional in the model, present in every published schema |

`BMM_SCHEMA_CORE` also defines `schema_contributors` and the archetype hints
`archetype_parent_class`, `archetype_data_value_parent_class`, `archetype_rm_closure_packages` and
`archetype_visualise_descendants_of`, and the specification's ODIN header example shows a
`model_name`. bmm-publisher reads none of them, so they are absent from every generated output,
including the ODIN and YAML forms.

A changed release (a new `rm_release`) is a new file with a new schema id; while a release is still
in development, edit its file and increase the build number in `schema_revision`.

## Includes

```json
"includes": {
  "openehr_base_1.3.0": { "id": "openehr_base_1.3.0" }
}
```

The key is the included schema id, as in every published schema. `includes` records the dependency
in the model, but bmm-publisher does not resolve it: pass the included file with `-d` both to
`bmm-publisher` (see the `class-generation` skill) and to `check_bmm.py`.

## Packages

```json
"packages": {
  "org.openehr.demo.inventory": {
    "name": "org.openehr.demo.inventory",
    "packages": {
      "item": { "name": "item", "classes": ["DEMO_ITEM", "DEMO_GROUP", "DEMO_STATUS"] },
      "box":  { "name": "box",  "classes": ["DEMO_BOX", "DEMO_BOX_REF"] }
    }
  }
}
```

- Only a top-level package name may contain `.`; sub-package names are single words.
- A package lists only classes defined in the same schema.
- Every class definition must be listed in exactly one package: bmm-publisher writes tables per
  package, so an unlisted class gets no table, and no message. A listed class that is not defined stops the
  run with `Class X not found in schema`.
- bmm-publisher visits packages four levels deep (top-level package = 1). Classes deeper than that
  get no table, again without a message.
- Top-level packages are named `org.openehr.<schema_name>.<package>`, and a specification
  document's `master.adoc` sets `:pkg:` to one of them plus a dot before the chapters that include
  its tables. A document can cover several: RM's `ehr` document sets `org.openehr.rm.ehr.` and then
  `org.openehr.rm.composition.`. BASE has `org.openehr.base.base_types`,
  `org.openehr.base.foundation_types` and `org.openehr.base.resource`; TERM has
  `org.openehr.term.terminology`. Sub-packages group the classes as the chapters do.
- The legacy class-table file name is the first four parts of the class's package path, then the
  class name in lower case: `LOCATABLE` in `org.openehr.rm.common` → `archetyped` gives
  `org.openehr.rm.common.locatable.adoc`, which a chapter includes as `{pkg}locatable.adoc`.
  Deeper sub-packages do not change the name. A top-level package named just
  `org.openehr.<schema_name>` takes its fourth part from its sub-package, but classes listed
  directly in it get files named `org.openehr.<schema_name>.org.<class>.adoc`.
- A top-level package that holds only sub-packages makes bmm-publisher print `Empty package …`;
  BASE does the same, and the warning is harmless.

## Classes

A class definition is one of four kinds, chosen by `_type` (omitted for a plain class):

| `_type` | Keys bmm-publisher reads |
|---------|--------------------------|
| *(none)* — plain class | `name`, `documentation`, `is_abstract`, `ancestors`, `generic_parameter_defs`, `constants`, `properties`, `functions`, `invariants` |
| `P_BMM_ENUMERATION_STRING`, `P_BMM_ENUMERATION_INTEGER` | `name`, `documentation`, `ancestors`, `item_names`, `item_values`, `item_documentations`, `functions` |
| `P_BMM_INTERFACE` | `name`, `documentation`, `functions` |

Any other key on an enumeration or interface (`properties`, `invariants`, `ancestors` on an
interface) is dropped.

- **`ancestors`** is a list of class names. A root class names `Any`, or has no `ancestors`; both
  forms occur in RM.
- **Generic class**: declare each parameter, with an optional constraint:
  ```json
  "generic_parameter_defs": { "T": { "name": "T", "conforms_to_type": "DEMO_ITEM" } }
  ```
- **Generic inheritance**: `ancestors` takes class names only. For an open binding (`IMPORTED_VERSION<T>`
  inherits `VERSION<T>`), list the root class and redeclare the parameter, as RM does:
  `"ancestors": ["VERSION"]` with `"generic_parameter_defs": {"T": {"name": "T"}}`. For a closed
  binding, list the root class only and state the binding in `documentation`, as BASE does for
  `Multiplicity_interval` ("An Interval of Integer", `"ancestors": ["Proper_interval"]`). The
  specification's `ancestor_defs` is not read.
- **Enumerations**: `item_names` are the symbolic names. `item_values` (optional) gives one value
  per name, all strings or all integers by kind. `item_documentations` gives one text per name, by
  position. The table prints integer values only when `Integer` is among the `ancestors` (the
  parser assumes `["Integer"]` when `ancestors` is missing), and never prints string values.

## Properties

Every property carries `_type`. Without it, a property is read as `P_BMM_SINGLE_PROPERTY`, and a
property with a `type_def` then silently becomes type `Any`.

| `_type` | For | Shape |
|---------|-----|-------|
| `P_BMM_SINGLE_PROPERTY` | `uid: HIER_OBJECT_ID` | `"type": "HIER_OBJECT_ID"` |
| `P_BMM_SINGLE_PROPERTY_OPEN` | `content: T` in a generic class | `"type": "T"`, a parameter of the class |
| `P_BMM_CONTAINER_PROPERTY` | `items: List<DEMO_ITEM>` | `"type_def": {"container_type": "List", "type": "DEMO_ITEM"}` plus `cardinality` |
| `P_BMM_GENERIC_PROPERTY` | `index: Hash<String, DEMO_ITEM>`, `target: DEMO_BOX<DEMO_GROUP>` | `"type_def": {"root_type": "Hash", "generic_parameters": ["String", "DEMO_ITEM"]}` |

- **`is_mandatory`**: `true` or absent (optional).
- **`cardinality`** (container properties only) counts the members:
  `{"lower": 0, "upper_unbounded": true}` is `0..*`, and `{"lower": 1, "upper_unbounded": true}`
  is a never-empty list (set `is_mandatory` too). A bounded upper limit needs
  `"upper_unbounded": false` written out: `{"lower": 2, "upper": 5, "upper_unbounded": false}`.
  bmm-publisher treats a missing `upper_unbounded` as `true` and drops the limit.
- **`Hash<K,V>`** and any other container with two parameters is a `P_BMM_GENERIC_PROPERTY` with
  `root_type: "Hash"`, as in BASE and RM. `container_type` takes one-parameter containers only:
  `List`, `Set`, `Array`. A generic property has no `cardinality`, so state a member count as an
  invariant, for example `"Codes_valid": "not codes.is_empty"`.
- **Generic arguments** bind in the order the root class declares its `generic_parameter_defs`,
  and each must conform to that parameter's `conforms_to_type`; bmm-publisher checks neither. BASE
  declares `Hash<K: Ordered, V>` and `FUNCTION<ARGS: TUPLE, RESULT>`, so a function taking two
  strings and returning a Boolean is `FUNCTION<TUPLE2<String, String>, Boolean>`.
- **`default`** (single properties) gives a default value, `false` or `"active"` for example; the
  table shows it as `{default = …}`. It is a toolchain addition, not a P_BMM attribute.

## Types

A type is a class name (`"type": "String"`) or a type object. The rules for type objects:

- Directly inside a property or parameter, `type_def` has **no** `_type`; its kind follows from
  the property's `_type`.
- Everywhere else (a function `result`, an entry of `generic_parameter_defs`, a nested `type_def`
  inside a container type) the object carries `_type`, as the specification requires where the
  subtype is ambiguous. Without it, the object is read as a simple type.

| `_type` | Keys |
|---------|------|
| `P_BMM_SIMPLE_TYPE` | `type` |
| `P_BMM_CONTAINER_TYPE` | `container_type`, then either `type` (a name) or `type_def` (a nested generic type; the parser also accepts a nested container type, which the P_BMM model does not) |
| `P_BMM_GENERIC_TYPE` | `root_type`, then either `generic_parameters` or `generic_parameter_defs`, with one entry per parameter of the root class |

Nesting, `replaced: List<DEMO_BOX<DEMO_GROUP>>`:

```json
"type_def": {
  "container_type": "List",
  "type_def": {
    "_type": "P_BMM_GENERIC_TYPE",
    "root_type": "DEMO_BOX",
    "generic_parameters": ["DEMO_GROUP"]
  }
}
```

bmm-publisher renders some valid nestings wrongly, so keep to these forms:

- A simple element type goes in the container's `type`; a `P_BMM_SIMPLE_TYPE` in its `type_def`
  renders as `List<Any>`, and so does a container with neither.
- `generic_parameters` holds names, or nested generic types as BASE writes them
  (`FUNCTION<TUPLE1<T>, Boolean>` in `Container.for_all`). A simple or container type object there
  stops bmm-publisher with a type error.
- Give `generic_parameters` or `generic_parameter_defs`, not both: with both, the defs are ignored.
- bmm-publisher prints `generic_parameter_defs` entries in the order written and ignores their keys,
  so write them in the root class's declared order, each keyed by its parameter name. A
  `P_BMM_CONTAINER_TYPE` there prints nothing, although the specification allows it; write the
  container as a generic type with `root_type: "List"`.

## Functions

```json
"functions": {
  "is_tagged": {
    "name": "is_tagged",
    "documentation": "True if `_tags_` contains `_a_tag_`.",
    "parameters": {
      "a_tag": {
        "_type": "P_BMM_SINGLE_FUNCTION_PARAMETER",
        "name": "a_tag",
        "documentation": "Tag to look for.",
        "type": "String"
      }
    },
    "pre_conditions": { "Pre_tag_valid": "not a_tag.is_empty()" },
    "result": { "_type": "P_BMM_SIMPLE_TYPE", "type": "Boolean" }
  }
}
```

- Function keys: `name`, `documentation`, `parameters`, `result`, `pre_conditions`,
  `post_conditions`, `aliases`, `is_abstract`, `is_nullable`.
- `result` is a type object with `_type`. The specification reads a function with no `result` as a
  procedure, but the table then prints an empty result type, so the published schemas almost always
  write `{"_type": "P_BMM_SIMPLE_TYPE", "type": "void"}`.
- `is_nullable: true` on a function means it may return `Void` (the table shows `0..1`); on a
  parameter it makes the parameter optional. Without it, every parameter shows as mandatory (`[1]`).
- Parameter kinds mirror the property kinds: `P_BMM_SINGLE_FUNCTION_PARAMETER` (`type`),
  `P_BMM_SINGLE_FUNCTION_PARAMETER_OPEN` (`type` is a class parameter such as `T`),
  `P_BMM_CONTAINER_FUNCTION_PARAMETER` (`type_def`, and an optional `cardinality` that defaults to
  `0..*`), `P_BMM_GENERIC_FUNCTION_PARAMETER` (`type_def`).
- `aliases` is a `Hash<String, String>` in the P_BMM model, but the published schemas and the parser
  use a list of names, as BASE's `Any.equal` does: `"aliases": ["=", "=="]`.

## Invariants, constants and conditions

```json
"invariants": { "Name_valid": "not name.is_empty()" },
"constants": {
  "Max_tags": { "name": "Max_tags", "documentation": "…", "type": "Integer", "value": "32" }
}
```

- `invariants`, `pre_conditions` and `post_conditions` map a tag to an assertion string, which
  P_BMM treats as opaque text (usually openEHR BEL). The published schemas mostly tag invariants
  `Xxx_valid` (some `Xxx_validity`), and conditions `Pre`/`Post` or `Pre_xxx`/`Post_xxx`; a function
  with several conditions gives each its own suffix.
- A constant needs `type`, and bmm-publisher fails without one. `value` is the literal in serialised
  form: `"32"`, `"\"..\""` for a string, `"'*'"` for a character, or the name of another constant.
  P_BMM types `value` as a String; BASE also writes numbers as JSON numbers (`60`, `30.42`), which
  bmm-publisher accepts.

## Documentation text

`documentation` (and parameter `documentation`, and `item_documentations`) is AsciiDoc inline text,
written as in the published schemas: `` `CLASS_NAME` ``, `` `_attribute_` ``, a blank line written
as `\n\n`. bmm-publisher then:

- escapes `{word}` (letters, digits, `_` and `.`) and any `{` after a space, so an attribute
  reference such as `{base_release}` is printed literally; write the value instead;
- passes a same-document cross-reference `<<_x_class,X>>` through;
- escapes `|` and `<=`;
- escapes every `*` on a line that holds two or more, so they print literally (no bold), except a
  leading list marker `* `; a single `*`, as in `0..*`, is left alone.

## What the class tables show

The legacy class tables (the `docs/UML/classes` layout) leave some of the model out:

- The cardinality column shows `1` or `0` from `is_mandatory`, then the container's bounded `upper`, otherwise `1`. `items` (`1..*` members, mandatory) shows `1..1`; `ranks` (2 to 5 members,
  optional) shows `0..5`. A member lower bound never appears, so state it in `documentation` or an invariant
  when readers need it.
- A generic class heading shows `DEMO_BOX<T>` without the `conforms_to_type` constraint.
- The inheritance row names the root class only, so a closed binding such as `<Integer>` shows only
  where `documentation` states it.
- An enumeration shows no inheritance row; its items are listed under a "Constants" heading, as
  bare names for a string enumeration and as `name: Integer = value` for an integer one.
- A function row shows `1..1`, or `0..1` when `is_nullable`; its pre- and post-conditions are
  printed in the signature cell.
- The header (`schema_revision`, `schema_lifecycle_state`, `includes`) appears nowhere.

## Specification features bmm-publisher does not read

These are valid P_BMM but are lost on the way to the class tables and to the ODIN and YAML forms. Use
the alternative.

| Specification feature | What bmm-publisher does | Write instead |
|-----------------------|--------------------------|---------------|
| `P_BMM_INDEXED_CONTAINER_PROPERTY` | property of type `Any` | `P_BMM_GENERIC_PROPERTY` with `root_type: "Hash"`, and an invariant for any member count |
| `P_BMM_INDEXED_CONTAINER_TYPE`, or `index_type` on a container type | a simple type, or the container without its index | the same |
| `ancestor_defs` (generic inheritance) | ignored; a parent named only there is lost | `ancestors` with the root class (see [Classes](#classes)) |
| `type_ref` with `value_constraint` (value sets) | ignored; with no `type`, the property is `Any` | `type`, and name the value set in `documentation` |
| `is_computed`, `is_im_infrastructure`, `is_im_runtime` | ignored | describe the property in `documentation` |
| `is_override` (class) | ignored | — |
| `schema_contributors`, `archetype_*` (header) | ignored | — |
| `P_BMM_OPEN_TYPE` | read as `P_BMM_SIMPLE_TYPE` | `P_BMM_SIMPLE_TYPE` |

A misspelt key (`is_mandantory`) or `_type` is ignored in the same way, without a message.

## Reading the specification's ODIN and YAML examples

| ODIN | YAML | JSON |
|------|------|------|
| `["items"] = (P_BMM_CONTAINER_PROPERTY) < … >` | `items: !P_BMM_CONTAINER_PROPERTY` | `"items": { "_type": "P_BMM_CONTAINER_PROPERTY", … }` |
| `name = <"items">` | `name: items` | `"name": "items"` |
| `ancestors = <"Any", "ITEM">` | `ancestors: [Any, ITEM]` | `"ancestors": ["Any", "ITEM"]` |
| `is_mandatory = <True>` | `is_mandatory: true` | `"is_mandatory": true` |
| `cardinality = <\|>=1\|>` | — | `"cardinality": {"lower": 1, "upper_unbounded": true}` |
| `cardinality = <\|2..5\|>` | — | `"cardinality": {"lower": 2, "upper": 5, "upper_unbounded": false}` |
| `includes = < ["1"] = < id = <"x"> > >` | — | `"includes": {"x": {"id": "x"}}` |
