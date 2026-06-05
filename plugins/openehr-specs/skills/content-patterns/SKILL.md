---
name: content-patterns
description: >
  Patterns for writing production-quality openEHR specification prose — overviews, class/concept
  semantics, design rationale, and clinical examples — in `specifications-XX` repos. This skill
  should be used when the user asks how to phrase or improve spec prose, draft a package/class
  description, write a design-rationale or semantics section, or asks about openEHR spec writing
  style. Not for creating or scaffolding the document or its structure (use authoring), amendment
  records (use amendment-record), or non-openEHR writing.
---

# openEHR Specification Content Patterns

This skill captures the recurring prose patterns found across all openEHR specification
documents in the `specifications-XX` repositories (RM, AM, BASE, LANG, PROC, SM, QUERY,
CNF, TERM, ITS-*), derived from the existing library and its shared infrastructure in
`specifications-AA_GLOBAL`. Apply them when writing new chapters or sections to match the
quality and consistency of the existing specification library. They do not apply to
non-openEHR specifications or general technical documentation.

## References

- **Prose pattern catalog**: see `references/prose-patterns.md` for the full structure,
  AsciiDoc template, real example, and conventions for each pattern indexed below.
- **Cross-reference attribute guide**: see `../authoring/references/cross-references.md` for
  how to find and use `{openehr_*}` attributes when writing cross-references in spec prose.

## General Principles

- **Formal register**: third person, present tense, no contractions, no hedging.
- **Declarative facts first**: lead with what the model defines, not how the reader should interpret it.
- **Design rationale where non-obvious**: explain why, not just what.
- **Ground every claim**: reference RM classes, archetype paths, or external standards. Never invent identifiers.
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
| Inventing class or attribute names | Only reference names from the published RM/AM/BASE |
| Explaining every attribute of a class in prose | Class definition tables are auto-generated; prose covers semantics and rationale |
| Orphan figures (no intro or follow-up text) | Always introduce and explain diagrams |
| Hardcoded URLs | Use `{openehr_*}` attributes from reference_definitions.adoc |
