# Changelog

Notable changes to the plugins in this repository. The format follows [Keep a Changelog](https://keepachangelog.com), and versions refer to individual plugins (see [docs/versioning.md](docs/versioning.md)).

## Unreleased

### Added

- `scaffold` skill (user-only, `/openehr-specs:scaffold`): initialises a specification repository, or brings an existing one up to the standard file set. It installs `AGENTS.md` (the `openehr-specs@openehr` plugin table, the Docker build invocation, and commit and branch conventions built around the Jira ticket key, `Changes for SPECXX-NN - <what changed>`), `.claude/CLAUDE.md`, `.claude/settings.json` (registers the `openehr` marketplace, enables `openehr-specs` and three other plugins, and pre-approves `git add`, `git commit`, `git diff`, WebFetch on `specifications.openehr.org` and three read-only Atlassian MCP calls, as BASE, RM and ITS-REST do today), `manifest.json`, `.gitignore`, `.asciidoctorconfig`, `LICENSE` (CC BY-SA 3.0, or Apache 2.0 for `ITS-*`) and `README.md`. It plans before it writes, reads the component, title, Jira key, BMM schema and licence from the repo, and never overwrites a hand-edited file without being told to.
- The file set is versioned: `assets/template-set.json` holds a revision, the variables and a strategy per file (seed, whole, JSON merge, ensure-lines, managed regions in `AGENTS.md`), and each repo records its revision and file hashes in `.claude/scaffold.json`, so a later run calculates the migration path from the recorded revision to the latest. `scripts/scaffold.py` needs `python3` (standard library only).
- `docs/quick-start.md` (a first session, from install to an HTML preview) and `docs/prompting-guide.md` (which prompt to use for each authoring situation).

### Changed

- `publish` and `regen-classes` moved from `commands/` to `skills/` as user-only skills (`disable-model-invocation: true`). Claude Code treats `commands/` as the older format, so the plugin no longer ships that directory. The `/openehr-specs:publish` and `/openehr-specs:regen-classes` names are unchanged.
- `scripts/validate.py` also checks the `scaffold` template set (templates exist and render, revisions have migration files, the digest matches), and CI runs the unit tests in `scripts/test_scaffold.py`.
- `scripts/validate.py` no longer checks a `commands/` directory; the user-only skills are validated as skills.
- `publish`, `authoring`, and the release checklist run the published `ghcr.io/openehr/asciidoctor` image instead of `openehr/asciidoctor`, which is only the tag of a local `docker build`.
- `publish` runs only the published image; the local-script branch is gone. That branch ran `spec_publish.sh -f -v` without `-q`, so every `{pkg}` class-table include failed (70 errors on BASE, with about 80% of the table blocks missing from the HTML) while the script still printed "generated" and exited 0. The image's entrypoint passes `-q`; on BASE the same image builds with no errors. The AA_GLOBAL checkout is still required, because the boilerplate and reference definitions are read from it. `authoring` shows the image first and says to pass `-q` with a local toolchain.
- `publish` and `regen-classes` keep only the runnable steps and guardrails; the background stays in `authoring` and `class-generation`.
- `amendment-record` takes over the `amend` command: it accepts the same arguments (`argument-hint`), locates the amendment record, checks the working-tree diff, and stops after showing the diff. It no longer pre-approves `Read`, `Edit`, and `Bash` as the command did.

### Security

- `publish` and `regen-classes` no longer pre-approve every shell command while they run. `allowed-tools` was a bare `Bash`, which also covered `git commit` and `git push`. It now lists only the Docker image each skill runs, plus `docker --version` for `regen-classes`. A command that does not match a pattern asks for approval as usual.

### Fixed

- `publish` no longer lists a `[spec-id]` argument, because the publisher builds whole components. It stops and asks when `$ARGUMENTS` is empty: the image takes exactly one component, and the bare script would rebuild every sibling repo. It always builds as `development`; a `Release-N.N.N` build belongs to `governance`.
- `publish` no longer trusts the build's `generated <file>` line, which is printed and exits 0 even when `asciidoctor` failed or includes are missing. It compares output timestamps before and after the build, scans the log for `ERROR` and `include file not found` lines, and reports each HTML file that was not rebuilt. `authoring` carries the same warning for a manual build.
- `regen-classes` keeps the layout rule (`legacy-adoc` or `asciidoc`) and stops and asks when `$ARGUMENTS` is empty.
- `amendment-record`: a direct run states an assumed version bump and proceeds instead of pausing, and it stops after the diff only when invoked directly, not inside a release or authoring flow.

### Removed

- `docs/spec-style-guide.md`. Most of what it restated (register, document structure, cross-reference and figure conventions) lives in `content-patterns`, `authoring` and `review`, so it was a second copy to keep in step. The conventions that were not in a skill (admonitions, code blocks, tables) moved to `authoring/references/asciidoc-syntax.md`, which `authoring` and `content-patterns` point to.
- `/openehr-specs:amend`, folded into `amendment-record`. Use `/openehr-specs:amendment-record <SPECXX-NN[,SPECPR-NN] — summary>` or a plain request. Removing a user-facing entry point is a major change under [docs/versioning.md](docs/versioning.md); the maintainer decides the bump at release.

## openehr-specs 0.3.0 (2026-10-07)

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
