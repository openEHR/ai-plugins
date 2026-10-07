# Changelog

Notable changes to the plugins in this repository. The format follows [Keep a Changelog](https://keepachangelog.com), and versions refer to individual plugins (see [docs/versioning.md](docs/versioning.md)).

## Unreleased

### Changed

- Skills point to the matching subagents and commands: `review` explains when to review inline or dispatch `spec-reviewer`, `xref-auditor`, or `identifier-grounding`; `authoring`, `class-generation`, and `governance` mention `/openehr-specs:publish`, `/openehr-specs:regen-classes`, and `/openehr-specs:amend`.
- Skill descriptions route to sibling skills more precisely (`authoring`, `governance`, `review`, `content-patterns`, `amendment-record`, `its-rest`, `class-generation`).
- `review` reads every chapter in scope instead of a sample of two or three.
- `its-rest`: added a "Reviewing Changes" section and clearer endpoint and schema steps.
- `class-generation`: the workflow picks the command by layout and says where to place the output.
- `governance`: the release steps ask the user to confirm the Jira state and to approve the push; fix-release steps live in the release checklist.
- Subagent definitions follow the current agent-development format: a prose trigger description, a "When to invoke" section, and a "do not use" pointer to the right sibling.
- `identifier-grounding` is limited to read-only tools plus the `openehr-assistant` type-specification tools; it could previously write files.

### Fixed

- `authoring`: the `master.adoc` template includes the amendment record after the front matter, as the RM specs do; preface contents match the review checks; `PAUSED` is a listed `spec_status`; the non-existent `-a` publisher option is no longer cited.
- `authoring` references: the `manifest.json` `id` rule and the release-attribute pattern match the published specs.
- `amendment-record`: the release-boundary row is documented as labelling the entries below it, matching the template and the RM record; the checklist covers a reused version, the date, and the raiser.
- `review`: the manifest check prefix is `MAN` (was `MANIFEST`), and hardcoded URLs are reported once.
- `its-rest`: the schema `title` and file-name rules no longer contradict `file-formats.md`.
- `regen-classes` no longer sends users without Docker to a dev container that also needs Docker.
- `spec-reviewer` and `xref-auditor` find their reference files by path lookup instead of a repo-relative path.
- `identifier-grounding` counts new and skipped identifiers in its summary line.
- Plugin README: subagent dependencies and command arguments match their definitions.

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
