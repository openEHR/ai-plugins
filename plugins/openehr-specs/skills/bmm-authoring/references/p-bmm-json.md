# P_BMM JSON — format reference

The openEHR BMM schemas in `specifications-XX/computable/BMM/*.bmm.json` are JSON serialisations of
the `P_BMM_*` classes of the
[BMM Persistence specification](https://specifications.openehr.org/releases/LANG/development/bmm_persistence.html)
(LANG). The specification shows its examples in ODIN, and says JSON with type markers may be used
instead. Its class tables (chapter "Persistence Model") are the normative list of attributes; this
reference was checked against the development version linked here. This
reference describes the JSON form that the published schemas use and that
[`bmm-publisher`](https://github.com/openEHR/bmm-publisher) reads, through its parser library
[`cadasto/openehr-bmm`](https://github.com/Cadasto/openehr-bmm). Where the specification and the
toolchain differ, both are stated.

`assets/openehr_demo_0.1.0.bmm.json` is a complete worked example that has one of each construct.
It passes `scripts/check_bmm.py` and renders with `bmm-publisher`.

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
- [Reading the specification's ODIN examples](#reading-the-specifications-odin-examples)

## The file

- One file per component release, named after its schema id: `<rm_publisher>_<schema_name>_<rm_release>.bmm.json`,
  for example `openehr_rm_1.2.0.bmm.json`.
- The working copy is in the component's `specifications-XX` repo under `computable/BMM/`. A push
  there updates [`specifications-ITS-BMM`](https://github.com/openEHR/specifications-ITS-BMM), which
  publishes the JSON and the ODIN and YAML forms it generates from it. Never edit the ITS-BMM copies.
- Every key that holds a map of named things (`packages`, `class_definitions`, `properties`,
  `functions`, `parameters`, `constants`, `generic_parameter_defs`) is keyed by the item's own
  `name`. bmm-publisher uses `name` and ignores the key, so a key that differs from `name` goes
  unnoticed.

## Header

`P_BMM_SCHEMA` and its parent `BMM_SCHEMA_CORE` define the header. bmm-publisher refuses a file that
lacks a field marked *yes*; the specification alone requires those marked *yes (spec)*.

| Field | Required | Value |
|-------|----------|-------|
| `bmm_version` | yes (spec) | `"2.4"` in every published schema, and what bmm-publisher writes |
| `rm_publisher` | yes | `"openehr"` |
| `schema_name` | yes | lower-case component name: `base`, `rm`, `am`, `lang`, `term` |
| `rm_release` | yes | 3-part release, `"1.2.0"`; part of the schema id and the file name |
| `schema_revision` | yes | `<rm_release>.<build>`, for example `"1.2.0.2"`. Increase the build number with every change: ITS-BMM expects each schema change to bump it |
| `schema_lifecycle_state` | yes | the specification defines no value set. Published schemas use `"stable"`; for an unreleased schema, use the lower-case lifecycle state of the specification (`development`, `trial`; see the `governance` skill) |
| `schema_description` | yes | one sentence |
| `schema_author` | yes | the published schemas use `Name <email>`; ask the user who to name |
| `includes` | no | see below |
| `packages` | yes | see below |
| `primitive_types` | no | class definitions of primitive types; only BASE has them |
| `class_definitions` | yes (spec) | all other class definitions |

`BMM_SCHEMA_CORE` also defines `schema_contributors` and the archetype hints
`archetype_parent_class`, `archetype_data_value_parent_class`, `archetype_rm_closure_packages` and
`archetype_visualise_descendants_of`. bmm-publisher does not read them, so they are absent from
every generated output, including the ODIN and YAML forms.

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
- Each specification document of a component has one top-level package,
  `org.openehr.<schema_name>.<package>`, and its `master.adoc` sets `:pkg:` to that name plus a
  dot: RM has `org.openehr.rm.common`, `org.openehr.rm.ehr` and more, BASE has
  `org.openehr.base.base_types`, `org.openehr.base.foundation_types` and
  `org.openehr.base.resource`, TERM has `org.openehr.term.terminology`. Sub-packages group the
  classes as the document's chapters do.
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
  position. The persistence model requires `String` or `Integer` among the `ancestors`.

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
- **Generic arguments** bind in the order the root class declares its `generic_parameter_defs`, and
  each must conform to that parameter's `conforms_to_type`; neither is checked by bmm-publisher.
  BASE declares `FUNCTION<ARGS, RESULT>`, so a function taking two strings and returning a Boolean
  is `FUNCTION<TUPLE2<String, String>, Boolean>`.
- **`default`** (single properties) gives a default value, `false` or `"active"` for example; the
  table shows it as `{default = …}`.

## Types

A type is a class name (`"type": "String"`) or a type object. The rules for type objects:

- Directly inside a property or parameter, `type_def` has **no** `_type`; its kind follows from
  the property's `_type`.
- Everywhere else (a function `result`, an entry of `generic_parameter_defs`, a nested `type_def`
  inside a container type) the object **must** carry `_type`, or it is read as a simple type.

| `_type` | Keys |
|---------|------|
| `P_BMM_SIMPLE_TYPE` | `type` |
| `P_BMM_CONTAINER_TYPE` | `container_type`, then either `type` (a name) or `type_def` (a nested type object) |
| `P_BMM_GENERIC_TYPE` | `root_type`, then `generic_parameters` (a list of names) or `generic_parameter_defs` (nested type objects keyed by parameter name), with one entry per parameter of the root class |

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

A container type with neither `type` nor `type_def` renders as `List<Any>`.

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
  `post_conditions`, `aliases` (list of names), `is_abstract`, `is_nullable`.
- `result` is a type object with `_type`. A procedure returns `{"_type": "P_BMM_SIMPLE_TYPE", "type": "void"}`.
- `is_nullable: true` on a function means it may return `Void` (the table shows `0..1`); on a
  parameter it makes the parameter optional. Without it, every parameter shows as mandatory (`[1]`).
- Parameter kinds mirror the property kinds: `P_BMM_SINGLE_FUNCTION_PARAMETER` (`type`),
  `P_BMM_SINGLE_FUNCTION_PARAMETER_OPEN` (`type` is a class parameter such as `T`),
  `P_BMM_CONTAINER_FUNCTION_PARAMETER` (`type_def` and a **required** `cardinality`: bmm-publisher
  fails without one), `P_BMM_GENERIC_FUNCTION_PARAMETER` (`type_def`).

## Invariants, constants and conditions

All three are part of `P_BMM_CLASS` and `P_BMM_FUNCTION` in the specification's class tables, though
its syntax chapter does not show them.

```json
"invariants": { "Name_valid": "not name.is_empty()" },
"constants": {
  "Max_tags": { "name": "Max_tags", "documentation": "…", "type": "Integer", "value": "32" }
}
```

- `invariants`, `pre_conditions` and `post_conditions` map a tag to an expression string. The
  published schemas mostly tag invariants `Xxx_valid`, pre-conditions `Pre_xxx` and
  post-conditions `Post_xxx`.
- A constant needs `type`, and bmm-publisher fails without one. `value` is the value as source
  text: `"32"`, the name of another constant, `"\"..\""` for a string, `"'*'"` for a character.

## Documentation text

`documentation` (and parameter `documentation`, and `item_documentations`) is AsciiDoc inline text,
written as in the published schemas: `` `CLASS_NAME` ``, `` `_attribute_` ``, a blank line written
as `\n\n`. bmm-publisher then:

- escapes `{…}`, so an attribute reference such as `{base_release}` is printed literally; write the
  value instead;
- passes a same-document cross-reference `<<_x_class,X>>` through;
- escapes `|` and `<=`, and every `*` on a line that holds two or more, so they print literally (no
  bold);
- leaves a single `*` alone, so `0..*` is safe.

## What the class tables show

The legacy class tables (the `docs/UML/classes` layout) leave some of the model out:

- The cardinality column shows `1` or `0` from `is_mandatory`, then the container's bounded `upper`, otherwise `1`. `items` (`1..*` members, mandatory) shows `1..1`; `ranks` (2 to 5 members,
  optional) shows `0..5`. A member lower bound never appears, so state it in `documentation` or an invariant
  when readers need it.
- A generic class heading shows `DEMO_BOX<T>` without the `conforms_to_type` constraint.
- The inheritance row names the root class only, so a closed binding such as `<Integer>` shows only
  where `documentation` states it.
- An enumeration shows no inheritance row; its items are listed under a "Constants" heading, with
  an empty value column when there are no `item_values`.
- A function row shows `1..1`, or `0..1` when `is_nullable`; its pre- and post-conditions are
  printed in the signature cell.
- The header (`schema_revision`, `schema_lifecycle_state`, `includes`) appears nowhere.

## Specification features bmm-publisher does not read

These are valid P_BMM but are lost on the way to the class tables and to the ODIN and YAML forms. Use
the alternative.

| Specification feature | What bmm-publisher does | Write instead |
|-----------------------|--------------------------|---------------|
| `P_BMM_INDEXED_CONTAINER_PROPERTY` / `_TYPE` (`index_type`) | property of type `Any` | `P_BMM_GENERIC_PROPERTY` with `root_type: "Hash"`, and an invariant for any member count |
| `ancestor_defs` (generic inheritance) | ignored; the class has no parent | `ancestors` with the root class (see [Classes](#classes)) |
| `type_ref` with `value_constraint` (value sets) | ignored; with no `type`, the property is `Any` | `type`, and name the value set in `documentation` |
| `is_computed`, `is_im_infrastructure`, `is_im_runtime` | ignored | describe the property in `documentation` |
| `is_override` (class) | ignored | — |
| `model_name`, `schema_contributors`, `archetype_*` (header) | ignored | — |
| `P_BMM_OPEN_TYPE` | read as `P_BMM_SIMPLE_TYPE` | `P_BMM_SIMPLE_TYPE` |

A misspelt key (`is_mandantory`) or `_type` is ignored in the same way, without a message.

## Reading the specification's ODIN examples

| ODIN | JSON |
|------|------|
| `["items"] = (P_BMM_CONTAINER_PROPERTY) < … >` | `"items": { "_type": "P_BMM_CONTAINER_PROPERTY", … }` |
| `name = <"items">` | `"name": "items"` |
| `ancestors = <"Any", "ITEM">` | `"ancestors": ["Any", "ITEM"]` |
| `is_mandatory = <True>` | `"is_mandatory": true` |
| `cardinality = <\|>=1\|>` | `"cardinality": {"lower": 1, "upper_unbounded": true}` |
| `cardinality = <\|2..5\|>` | `"cardinality": {"lower": 2, "upper": 5, "upper_unbounded": false}` |
| `includes = < ["1"] = < id = <"x"> > >` | `"includes": {"x": {"id": "x"}}` |
