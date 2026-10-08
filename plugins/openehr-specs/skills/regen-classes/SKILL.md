---
name: regen-classes
description: Regenerate BMM-derived class tables and UML diagrams for a component via bmm-publisher
argument-hint: "<schema-id of this repo's BMM, e.g. openehr_rm_1.2.0> [-d <dependency-schema-id> ...]"
allowed-tools:
  - "Bash(docker --version)"
  - "Bash(docker run * ghcr.io/openehr/bmm-publisher *)"
  - Read
  - Glob
disable-model-invocation: true
---

Regenerate the class tables and UML diagrams for `$ARGUMENTS` with `bmm-publisher`, from the BMM files in
the component repo at the current directory, not from the copies bundled in the image (they lag the
repos, and a run from a bundled id exits 0 while rendering the older model). The arguments are a schema
id without `.bmm.json` (for example `openehr_rm_1.2.0`) plus any `-d <dependency-schema-id>` flags (RM
depends on BASE: `openehr_rm_1.2.0 -d openehr_base_1.3.0`). The layouts and the placement into
`docs/UML/` are in the `openehr-specs:class-generation` skill; this wrapper covers generation only.

If `$ARGUMENTS` is empty, ask for the schema id and stop.

1. Run `docker --version`. If Docker is missing, say it is required (the image and its dev container
   both run on it) and stop.
2. Map each id to its file and Glob that it exists: the schema to `computable/BMM/<id>.bmm.json`, and a
   dependency `openehr_<component>_<version>` to the sibling clone's
   `../specifications-<COMPONENT>/computable/BMM/<id>.bmm.json` (component upper-cased). If one is
   missing, name it and stop; never fall back to the bundled id.
3. Write to `./out` unless the user names another target. Ask before writing into a
   `specifications-XX` repo's `docs/UML/`.
4. Pick the command by layout (step 2 of the `class-generation` workflow): `legacy-adoc -o
   /app/output/UML/classes` when the spec's chapters contain `include::{uml_export_dir}/classes/`
   (the tables land in `./out/UML/classes`), otherwise `asciidoc`. Mount each file read-only under
   `/in/`, pass the paths, and map output ownership to the host user (RM with BASE shown):
   ```bash
   docker run --rm --user $(id -u):$(id -g) \
     -v "$PWD/computable/BMM/openehr_rm_1.2.0.bmm.json":/in/openehr_rm_1.2.0.bmm.json:ro \
     -v "$PWD/../specifications-BASE/computable/BMM/openehr_base_1.3.0.bmm.json":/in/openehr_base_1.3.0.bmm.json:ro \
     -v ./out:/app/output \
     ghcr.io/openehr/bmm-publisher asciidoc -v /in/openehr_rm_1.2.0.bmm.json -d /in/openehr_base_1.3.0.bmm.json
   ```
   Add one mount and one `-d /in/<id>.bmm.json` per dependency. The `-v` log lists each file read:
   check that every one is under `/in/`.
5. List what was produced (`classes/`, `effective/`, diagram SVGs). Do not commit. Generated files are
   never hand-edited: change the BMM and regenerate. To place the output, follow the
   `class-generation` skill.
