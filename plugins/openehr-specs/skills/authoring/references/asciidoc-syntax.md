# AsciiDoc syntax conventions

Conventions shared by the `specifications-XX` repositories for three elements that no other reference
defines: admonitions, code blocks and tables. Read this file when adding a note, a code example or a
table to a chapter. Match the spec you are editing if it differs.

## Admonitions

Start the paragraph with the standard Asciidoctor label: `NOTE:`, `WARNING:` or `IMPORTANT:`.

```asciidoc
NOTE: The identifier is opaque to clients.
```

`NOTE:` is by far the most common in the specs. `WARNING:` and `IMPORTANT:` appear rarely.

## Code blocks

Formal code, such as a grammar, a query or source code, uses a `[source, <language>]` line and a
dashed delimiter:

```asciidoc
[source, ebnf]
--------
identifier = letter , { letter | digit } ;
--------
```

The RM, AM, LANG and QUERY specs use this form; the languages in use include `ebnf`, `sql` and `java`.
Informal examples, such as a short list of values, use a triple-backtick fence.

## Tables

A table starts with a `[cols="..."]` line and a `|===` delimiter. Add `options="header"` when the first
row is a header row:

```asciidoc
[cols="1,6,2,2", options="header"]
|===
|Issue|Details|Raiser|Completed
|1.0.0|Initial writing.|A Author|01 Jan 2020
|===
```

Use `1a` or `2a` in `cols` when a cell needs AsciiDoc block content such as a list. Class definition
tables are generated from the BMM; do not write them by hand (`class-generation` skill).

## Conventions defined elsewhere

| Element | Where |
|---------|-------|
| Class and type names in monospace; attribute names in italic monospace | `review` checks ADOC-01 and ADOC-02 |
| `[.tbd]` and `[.deprecated]` markers | `review` checks ADOC-04 and ADOC-05; `content-patterns` pattern 6 |
| Bibliographic citations (`cite:[Key]`, `citenp:[Key]`) | `review` check ADOC-06 |
| Links to other specs and external standards (`{openehr_*}`, `{iso_8601}`) | `cross-references.md` |
| Figures and UML diagrams | `authoring` ("Diagrams"); `review` FIG checks |
