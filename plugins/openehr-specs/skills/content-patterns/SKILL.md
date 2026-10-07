---
name: content-patterns
description: >
  Patterns for writing openEHR specification prose (package overviews, class/concept semantics,
  design rationale, clinical examples, requirements sections, deprecated/TBD markers, and figure
  introductions) in `specifications-XX` repos. This skill should be used when the user asks how to
  phrase, draft, or improve spec prose, or about openEHR spec writing style. Not for document
  structure (use authoring), convention checks (use review), amendment records (use
  amendment-record), ITS-REST descriptions (use its-rest), or non-openEHR writing.
---

# openEHR Specification Content Patterns

Apply these recurring prose patterns when writing new chapters or sections, to match the quality
and consistency of the existing specification library. They are derived from the openEHR
specification documents in the `specifications-XX` repositories (RM, AM, BASE, LANG, PROC, SM,
QUERY, CNF, TERM, ITS-*) and the shared infrastructure in `specifications-AA_GLOBAL`.

## References

- **Prose pattern catalog**: see `references/prose-patterns.md` for the full structure,
  AsciiDoc template, real example, and conventions for each pattern indexed below.
- **Cross-reference attribute guide**: see `../authoring/references/cross-references.md` for
  how to find and use `{openehr_*}` attributes when writing cross-references in spec prose.
- **Admonitions, code blocks, tables**: see `../authoring/references/asciidoc-syntax.md` for the
  syntax of a note, a code example, or a table in a chapter.

## General Principles

- **Formal register**: third person, present tense, no contractions, no hedging.
- **Declarative facts first**: lead with what the model defines, not how the reader should interpret it.
- **Design rationale where non-obvious**: explain why, not just what.
- **Ground every claim**: reference RM classes, archetype paths, or external standards. Never invent identifiers; after drafting, dispatch the `identifier-grounding` subagent to verify each class, attribute, and function name against the published specifications.
- **Clinical examples**: use concrete clinical scenarios to illustrate abstract model concepts.

## Pattern Catalog

Pick the pattern that matches the section being written and read its detailed entry in
**`references/prose-patterns.md`**.

| # | Pattern | Use when writing… |
|---|---------|-------------------|
| 1 | Package/Chapter Overview | the opening of a chapter that describes a model package (opening paragraph → UML diagram → package/class enumeration) |
| 2 | Class/Concept Semantics | the prose for a class or major concept (purpose, typing, identification, structure, lifecycle, relationships) |
| 3 | Design Rationale | an explanation of *why* a non-obvious design choice was made (problem/requirement → chosen design → rejected alternatives) |
| 4 | Clinical/Practical Examples | a concrete clinical scenario that grounds an abstract model concept |
| 5 | Requirements Sections | an explicit numbered-requirements section preceding a design (common in Data Types, EHR IM) |
| 6 | Deprecated and TBD Markers | `[.deprecated]` or `[.tbd]` annotations for legacy or pending content |
| 7 | Figures and Diagrams in Context | any diagram — always introduced by text and followed by explanation |

## Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|-------------|-----------------|
| "This section describes..." | State what the package/class defines directly |
| "We decided to..." | "The design uses..." / "The approach taken is..." |
| Passive hedging ("it might be...") | Declarative statements ("it is..." / "this enables...") |
| Inventing class or attribute names | Reference only names found in the published RM/AM/BASE (see "Ground every claim" above) |
| Explaining every attribute of a class in prose | Class definition tables are generated (see `class-generation`); prose covers semantics and rationale |
| Orphan figures (no intro or follow-up text) | Always introduce and explain diagrams |
| Hardcoded URLs | Use `{openehr_*}` attributes from reference_definitions.adoc |
