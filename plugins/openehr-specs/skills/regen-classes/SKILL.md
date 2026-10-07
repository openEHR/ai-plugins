---
name: regen-classes
description: Regenerate BMM-derived class tables and UML diagrams for a component via bmm-publisher
argument-hint: "<schema-id, e.g. openehr_rm_1.2.0> [-d <dependency-schema> ...]"
allowed-tools:
  - "Bash(docker --version)"
  - "Bash(docker run * ghcr.io/openehr/bmm-publisher *)"
  - Read
  - Glob
disable-model-invocation: true
---

Regenerate the class tables and UML diagrams for `$ARGUMENTS` with `bmm-publisher`. The arguments are a
schema id without `.bmm.json` (for example `openehr_rm_1.2.0`) plus any `-d <dependency-schema>` flags
(RM depends on BASE: `openehr_rm_1.2.0 -d openehr_base_1.3.0`). The layouts and the placement into
`docs/UML/` are in the `openehr-specs:class-generation` skill; this wrapper covers generation only.

If `$ARGUMENTS` is empty, ask for the schema id and stop.

1. Run `docker --version`. If Docker is missing, say it is required (the image and its dev container
   both run on it) and stop.
2. Write to `./out` unless the user names another target. Ask before writing into a
   `specifications-XX` repo's `docs/UML/`.
3. Pick the command by layout (step 2 of the `class-generation` workflow): `legacy-adoc -o
   /app/output/UML/classes` when the spec's chapters contain `include::{uml_export_dir}/classes/`
   (the tables land in `./out/UML/classes`), otherwise `asciidoc`. Generate, mapping output ownership
   to the host user:
   ```bash
   docker run --rm --user $(id -u):$(id -g) \
     -v ./out:/app/output \
     ghcr.io/openehr/bmm-publisher asciidoc -v $ARGUMENTS
   ```
4. List what was produced (`classes/`, `effective/`, diagram SVGs). Do not commit. Generated files are
   never hand-edited: change the BMM and regenerate. To place the output, follow the
   `class-generation` skill.
