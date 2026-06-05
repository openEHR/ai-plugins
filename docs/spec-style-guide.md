# openEHR Specification Document Style Guide

This style guide describes the conventions of the *target* `specifications-XX` repos that the skills operate on — not this repo's own files. Skill bodies must agree with it: when changing one, check the other.

When generating or editing AsciiDoc content for any `specifications-XX` repo, follow these conventions. They are consistent across all components (RM, AM, BASE, QUERY, SM, PROC, LANG, CNF, TERM, ITS-*).

## Tone and Register

- Formal, precise, impersonal technical prose. Third person or passive voice throughout ("The class defines...", "Content is committed...", "This specification describes...").
- Present tense for describing model semantics and design; past tense only for historical context or amendment records.
- No contractions (use "does not", not "doesn't"). No colloquialisms, no hedging ("perhaps", "maybe").
- Clinical and standards-aware: assume the reader is a software engineer or informatician who understands object-oriented modelling.

## Structural Patterns

- **Preface** (`master01-preface.adoc`) always follows a fixed structure: Purpose, Related Documents, Status, Feedback, Conformance (optional), Tools (optional), Changes from Previous Versions (optional).
- **Chapter files** start with a `= Chapter Title` heading and typically open with an Overview subsection.
- **Package/chapter flow**: Overview first (introduces package purpose, typically with a UML diagram), then requirements or design rationale, then detailed semantics. Class description tables (when present) are auto-generated from UML/BMM — do not hand-write them.
- **Amendment record** (`master00-amendment_record.adoc`): most-recent-first table, release boundaries marked with `4+^h|*XX Release N.N.N*` rows, Jira ticket references using `{spec_tickets}/SPECXX-NNN[SPECXX-NNN^]` syntax.

## AsciiDoc Conventions

- **Class/type names** are monospaced: `` `COMPOSITION` ``, `` `DV_TEXT` ``, `` `VERSIONED_OBJECT<T>` ``
- **Attribute names** are italicised inside underscores: `` `_uid_` ``, `` `_value_` ``, `` `_commit_audit_` ``
- **Cross-references to other specs** use attributes from `reference_definitions.adoc`: `{openehr_rm_common}[Common IM^]`, `{openehr_rm_data_types}#dv_quantity[DV_QUANTITY^]`
- **External standards** are linked via predefined attributes: `{iso_8601}[ISO 8601^]`, `{snomed_ct}[SNOMED CT^]`, `{rfc4880}[IETF RFC 4880^]`
- **Figures** use `[.text-center]` with a title line (`.Title`) followed by `image::` with `id=`, `align="center"`, and optional `width=`
- **UML diagrams**: `image::{uml_diagrams_uri}/RM-*.svg[...]`; hand-drawn diagrams: `image::{diagrams_uri}/*.png[...]` or `.svg`
- **TBD markers**: `[.tbd]` role followed by `*TBD*: (description)`
- **Deprecated markers**: `[.deprecated]` role followed by `*Deprecated*: (explanation)`
- **Admonitions**: use `NOTE:`, `WARNING:`, `IMPORTANT:` standard Asciidoctor admonitions
- **Bibliographic citations**: `cite:[Key]` or `citenp:[Key]` (in-text); bibliography rendered with `bibliography::[]`
- **Code blocks**: use `[source, language]` with `--------` delimiters for formal code; triple backticks for informal examples
- **Tables**: use `[cols="...", options="header"]` followed by `|===` block syntax

## Writing Principles

- Lead with **what** the model defines, not how the reader should understand it. State facts declaratively.
- Explain **design rationale** where non-obvious: why a class exists, why an alternative was rejected.
- Use **concrete examples** (clinical scenarios, data instances) to illustrate abstract concepts.
- When describing class semantics, address: typing, identification, lifecycle, relationships to other classes, and implementation notes.
- **Never invent** class names, attribute names, terminology codes, archetype paths, or RM types. Always ground in the published openEHR specifications.
