# Changelog

Notable changes to the plugins in this repository. Format follows [Keep a Changelog](https://keepachangelog.com); versions refer to individual plugins (see [docs/versioning.md](docs/versioning.md)).

## openehr-specs 0.2.0 — 2026-06-05

Adds autonomous subagents and user-invoked commands around the existing seven skills:

- **Subagents** (`agents/`): `spec-reviewer` (runs the full review check catalog across a whole spec document), `xref-auditor` (verifies `{openehr_*}` attributes and cross-spec anchors, using the Markdown-twin of target specs), `identifier-grounding` (fact-checks RM/AM/BASE identifiers in a draft against the published spec).
- **Commands** (`commands/`, user-invoked): `/openehr-specs:amend`, `/openehr-specs:regen-classes`, `/openehr-specs:publish`.
- `scripts/validate.py` now also validates agent and command frontmatter.

## openehr-specs 0.1.0 — 2026-06-05

Initial release. Seven skills for openEHR specification work: `authoring`, `content-patterns`, `amendment-record`, `review`, `governance`, `its-rest`, and `class-generation`. Packaged for the Claude Code and Cursor marketplaces.
