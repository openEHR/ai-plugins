# openEHR Specification Prose Patterns — Detailed Catalog

The seven recurring prose patterns for openEHR specification chapters, each with structure,
an AsciiDoc template, a real example, and conventions. The skill body holds the general
principles, a pattern index, and the anti-patterns table; load this file when drafting a
section to follow the relevant pattern in detail.

## Pattern 1: Package/Chapter Overview

Every chapter that describes a model package opens with this structure:

### Structure

1. **Opening paragraph** — one or two sentences stating what this package defines and its role
   within the broader specification.
2. **UML diagram** — the package diagram, centred with title.
3. **Package enumeration** — a bulleted or numbered list of sub-packages or key classes,
   each with a one-sentence description.

### Template

```asciidoc
= {Package} Package

== Overview

The `{component}.{package}` package defines {what it provides and why it exists}.

[.text-center]
.`{component}.{package}` Package
image::{uml_diagrams_uri}/{COMPONENT}-{package}.svg[id={package}_package, align="center"]

The packages are as follows:

* `{sub_package_1}`: {one-sentence description of purpose}.
* `{sub_package_2}`: {one-sentence description of purpose}.
```

### Example (from RM EHR IM)

> The figure below illustrates the package structure of the openEHR EHR information model.
>
> [figure]
>
> The packages are as follows:
> * `ehr`: this package contains the top level structure, the EHR, which consists of an
>   `EHR_ACCESS` object, an `EHR_STATUS` object, versioned data containers...
> * `composition`: the Composition is the EHR's top level "data container"...

### Key Points

- The opening paragraph is factual and declarative — no "this section describes" preamble.
- The diagram appears immediately after the opening paragraph.
- Each bullet starts with the package/class name in monospace, followed by a colon and description.

## Pattern 2: Class/Concept Semantics

When describing the semantics of a class or major concept within a package:

### Structure

1. **Purpose** — what the class represents and why it exists.
2. **Typing** — generic parameters, inheritance, key subtypes.
3. **Identification** — how instances are identified (uid, id schemes).
4. **Structure** — key attributes, their types, and what they represent.
5. **Lifecycle** — states, transitions, creation/deletion semantics.
6. **Relationships** — how this class relates to other classes in the model.
7. **Implementation notes** — practical guidance for implementors.

### Template

```asciidoc
=== {Class Name}

{One paragraph explaining what the class represents and its role in the model.}

The `_{key_attribute}_` attribute {records/identifies/contains} {what and why}.
{Further attribute descriptions as needed.}

{If the class has subtypes or generic parameters, explain the typing model.}

{If the class has lifecycle semantics, describe states and transitions.}

{If there are important relationships to other classes, explain them.}
```

### Conventions

- Refer to classes in monospace: `COMPOSITION`, `VERSION<T>`
- Refer to attributes in italic-monospace: `_uid_`, `_commit_audit_`
- When describing an attribute, use the form: "The `_attribute_` attribute {verb} {what}."
- When describing a function, use the form: "The `_function_()_` function {verb} {what}."
- Qualify attribute references with their class when ambiguous: `VERSION._uid_`, `VERSIONED_OBJECT._uid_`

### Example (from RM Common — VERSION)

> The abstract `VERSION` class defines the generic notion of a version containing some data,
> that has been committed to the repository as a member of a Contribution. Accordingly, it
> records the Contribution in the `_contribution_` attribute and the audit in `_commit_audit_`.
> A Version also knows its position in the version tree within the container. It has a version
> identifier, `_uid_`, and knows on which version in the tree it was based...

## Pattern 3: Design Rationale

Used when explaining why a design choice was made, especially when the choice is non-obvious
or departs from simpler alternatives.

### Structure

1. **State the problem or requirement** — often citing ISO standards, medicolegal needs,
   or clinical workflow requirements.
2. **Describe the chosen design** — how the model addresses the requirement.
3. **Explain what was considered and rejected** (when relevant) — and why.

### Template

```asciidoc
{The requirement or problem, often with a citation.}

{The chosen design and how it satisfies the requirement.}

{Why alternatives were not chosen (optional but valuable).}
```

### Example (from RM Common — Versioning rationale)

> As described in the Architecture Overview document, formal version control and change
> management are used in openEHR to support the construction of EHR and other repositories
> requiring the properties of consistency, indelibility, traceability and distributed sharing.

> ...medicolegal and traceability requirements mean that information cannot be literally
> removed, since it must always be possible to revert back to a previous state of the record...
> Accordingly, information can only ever be logically deleted.

### Key Points

- Cite the source of the requirement: ISO standard, GEHR specification, clinical practice.
- Use citations: `cite:[Key]` or `citenp:[Key]` for formal references.
- State facts, not opinions. "The requirement is..." not "We believe...".

## Pattern 4: Clinical/Practical Examples

Used to ground abstract model concepts in concrete real-world scenarios.

### Structure

1. **Scenario** — a brief clinical or practical situation.
2. **Mapping** — how the scenario maps to RM structures.
3. **Data illustration** — what the data would look like (optional).

### Template

```asciidoc
For example, during a patient encounter, the following might occur:

* _addition_: a new Composition is created recording the Observations...
* _modification_: the Composition containing the current medications list is updated...

These two changes together constitute a logical _change-set_, and would typically be
included in the one Contribution.
```

### Conventions

- Use italics for logical concept names: _addition_, _modification_, _change-set_.
- Use concrete clinical terms: "medication list", "blood pressure", "discharge summary".
- Keep examples clinically realistic — do not invent implausible scenarios.
- When illustrating data, use instance diagrams or bulleted structural descriptions.

## Pattern 5: Requirements Sections

Some chapters (especially in Data Types, EHR IM) have explicit requirements sections
that precede the design.

### Structure

1. **Numbered requirements** — stated as principles or needs.
2. **Discussion** — elaboration with sub-cases, often using clinical examples.

### Template

```asciidoc
=== Requirements

The sections below describe the requirements of {topic}. Two overriding principles
should be noted...

. {First principle or requirement.}
. {Second principle or requirement.}
```

### Conventions

- Use AsciiDoc ordered lists (`. item`) for numbered requirements.
- Each requirement is a factual statement of need, not a design decision.
- Requirements reference external standards or clinical practice where applicable.

## Pattern 6: Deprecated and TBD Markers

### Deprecated Content

When an element is deprecated but must remain documented for legacy compatibility:

```asciidoc
[.deprecated]
*Deprecated*: {What is deprecated} was used to {original purpose}. {What replaces it
and since when.} For legacy reasons, {it remains legal / should be supported in a basic way}.
```

### To Be Determined

When content is incomplete or a decision is pending:

```asciidoc
[.tbd]
*TBD*: {What is undetermined and why. Optionally, what approach is being considered.}
```

### Key Points

- Always use the `[.deprecated]` or `[.tbd]` role on the preceding line.
- Deprecated markers should explain both the old and new approach.
- TBD markers should be specific about what is undetermined.

## Pattern 7: Figures and Diagrams in Context

Diagrams are never standalone — they are always introduced by text and followed by explanation.

### Template

```asciidoc
{Introductory sentence referencing the figure by its cross-reference anchor.}

[.text-center]
.{Figure title}
image::{uml_diagrams_uri}/{file}.svg[id={anchor_id}, align="center"]

{Explanatory text that walks through what the figure shows.}
```

### Conventions

- Introduce the figure before it appears: "The figure below illustrates..." or
  "<<anchor_id>> illustrates..."
- Follow the figure with explanatory text — never let a figure be the last thing in a section.
- Use `width=80%` or similar for large diagrams to prevent overflow.
