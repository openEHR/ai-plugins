# Changelog

Notable changes to the plugins in this repository. The format follows [Keep a Changelog](https://keepachangelog.com), and versions refer to individual plugins (see [docs/versioning.md](docs/versioning.md)).

## openehr-specs 0.2.0 (2026-06-05)

### Added

- Subagent `spec-reviewer`: runs the full review check catalog across a whole spec document.
- Subagent `xref-auditor`: verifies `{openehr_*}` attributes and cross-spec anchors, using the Markdown twin of the target spec.
- Subagent `identifier-grounding`: fact-checks RM, AM, and BASE identifiers in a draft against the published spec.
- Commands (user-invoked): `/openehr-specs:amend`, `/openehr-specs:regen-classes`, `/openehr-specs:publish`.

### Changed

- `scripts/validate.py` also validates subagent and command frontmatter.

## openehr-specs 0.1.0 (2026-06-05)

### Added

- Seven skills for openEHR specification work: `authoring`, `content-patterns`, `amendment-record`, `review`, `governance`, `its-rest`, and `class-generation`.
- Packaging for the Claude Code and Cursor marketplaces.
