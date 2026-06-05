---
name: regen-classes
description: Regenerate BMM-derived class tables and UML diagrams for a component via bmm-publisher
argument-hint: "<schema-id, e.g. openehr_rm_1.2.0> [-d <dependency-schema> ...]"
allowed-tools: ["Bash", "Read", "Glob"]
disable-model-invocation: true
---

Regenerate the class documentation (class-definition tables + UML class/package diagrams) for an
openEHR component from its BMM schema using the `bmm-publisher` tool. The tool, commands, output
layouts, and how the output wires into `docs/UML/` are documented in the
`openehr-specs:class-generation` skill and its `references/bmm-publisher.md` — follow them; this
command is the action wrapper.

Arguments: `$ARGUMENTS` — the schema id (without `.bmm.json`, e.g. `openehr_rm_1.2.0`) and any
`-d <dependency-schema>` flags for cross-reference resolution (e.g. RM depends on BASE:
`openehr_rm_1.2.0 -d openehr_base_1.3.0`).

Do the following:

1. **Confirm Docker is available** (`docker --version`). If not, point the user to the local
   `bmm-publisher` dev-container path in `references/bmm-publisher.md` and stop.
2. **Determine the output target.** Default to a working directory the user can inspect (e.g.
   `./out`); ask before writing directly into a `specifications-XX` repo's `docs/UML/`.
3. **Run the generator**, mapping output ownership to the host user:
   ```bash
   docker run --rm --user $(id -u):$(id -g) \
     -v ./out:/app/output \
     ghcr.io/openehr/bmm-publisher asciidoc -v $ARGUMENTS
   ```
   Use `legacy-adoc -o <dir>` instead when the component consumes the legacy `docs/UML/classes`
   layout (per the class-generation skill).
4. **Report what was generated** (list the produced `classes/`, `effective/`, diagram SVGs) and
   remind the user that generated files are never hand-edited — change the BMM and regenerate.
5. Do not commit. If the user wants the output wired into a spec repo, follow the placement steps
   in the class-generation skill.
