# Changelog

Notable changes to the plugins in this repository. The format follows [Keep a Changelog](https://keepachangelog.com), and versions refer to individual plugins (see [docs/versioning.md](docs/versioning.md)).

## Unreleased

### Added

- `bmm-authoring` skill: write a component's BMM schema (the P_BMM JSON in `computable/BMM/`) from scratch, or change one. It covers the header and its conventions, `includes`, how packages set the class-table file names, every class, property, type and function kind, invariants and constants, documentation text, what the legacy class tables do not show, and the persistence-spec features `bmm-publisher` does not read (indexed containers, `ancestor_defs`, `type_ref` value sets), with the form to write instead. It ships a worked example (`assets/openehr_demo_0.1.0.bmm.json`) and a read-only checker, `scripts/check_bmm.py` (standard-library Python 3.8+), that reports what `bmm-publisher` accepts without a message: a misspelt or missing `_type`, a misspelt key such as `is_mandantory`, a key that differs from its `name`, a class in no package, an upper limit without `"upper_unbounded": false`, a container without an element type, wrong generic parameter counts, a generic argument that does not conform to its parameter's `conforms_to_type`, unresolved type names (with `-d` for the included schemas), and more. CI runs its unit tests (`scripts/test_check_bmm.py`).
- `scaffold` template set revision 3: a new repository also gets `computable/BMM/<id>.bmm.json` (file id `bmm`, strategy `bmm-seed`).
  - The script lists the schemas the local `ghcr.io/openehr/bmm-publisher` image bundles (`docker run --pull never`, so nothing is downloaded) and copies the highest version for the component.
  - When the image bundles none, it writes an empty schema `openehr_<component>_<first_release>`. The schema has one root package `org.openehr.<name>`, no classes, and BASE in `includes` for other components. bmm-publisher refuses a schema without a package.
  - Without Docker or the image the file is reported as `blocked` and the other files are still written; `--var bmm_schema_id=<id>` creates the empty schema anyway.
  - Existing repositories are not offered a schema; `--overwrite bmm` asks for one.
  - Derived variables can take a regex group (`match` + `group`), which gives the new `bmm_schema_name` and `bmm_rm_release`.

### Changed

- `class-generation` and `authoring` send changes to the class model itself to `bmm-authoring`.
- `docs/prompting-guide.md`: the class-change prompts name `bmm-authoring` and the checker, and a prompt for a new component's schema is added.

## openehr-specs 0.5.0 (2026-10-08)

### Changed

- `class-generation` and `regen-classes` generate from the component repo's own BMM file and its sibling dependencies, mounted under `/in/` and passed by path. A bare schema id loads the copy bundled in the `bmm-publisher` image, which lags the repos and rendered an older model without any error; mounting a directory over `/app/resources` hid the bundled dependencies. `regen-classes` stops when a file is missing instead of falling back to an id.
- `scaffold` template set revision 2: the `AGENTS.md` build region no longer says the repo has no build tooling, and its class-table command loads the sibling BASE BMM with `-d` (new variable `base_bmm_schema_id`, inferred from the `specifications-BASE` clone), so links to BASE types resolve. A new `AGENTS.md` gets a `TODO(scaffold)` marker for the repo's own tooling, and `.claude/CLAUDE.md` says repo guidance belongs in `AGENTS.md` outside the regions. Existing repos upgrade on the next `/openehr-specs:scaffold` run.
- `scaffold` asks to confirm `first_release` only when it creates `manifest.json`, the one file that uses it, and its rules say where `/init`-style guidance goes.
- `amendment-record` covers changes without a Jira ticket: no invented or placeholder key, an offer to raise one, an entry without a reference otherwise, and none when the author says none is needed.
- `authoring` reference `manifest-spec-entry.md`: the expressions example shows the current `ITS-BMM-<COMPONENT>` url expression and `ITS-BMM-BASE` dependency (as in RM) instead of the retired MagicDraw `uml` expressions.

## openehr-specs 0.4.0 (2026-10-07)

### Added

- `scaffold` skill (user-only, `/openehr-specs:scaffold`): initialises a specification repository, or brings an existing one up to the standard file set: `AGENTS.md` (plugin table, Docker build invocation, Jira-key commit and branch conventions), `.claude/CLAUDE.md`, `.claude/settings.json`, `manifest.json`, `.gitignore`, `.asciidoctorconfig`, `LICENSE` and `README.md`. It plans before it writes, reads the component, title, Jira key, BMM schema and licence from the repo, and never overwrites a hand-edited file without being told to. Needs `python3`.
- `scaffold`: `.claude/settings.json` registers the `openehr` marketplace, enables `openehr-specs` and three other plugins, and pre-approves `git add`, `git commit`, `git diff`, WebFetch on `specifications.openehr.org` and three read-only Atlassian MCP calls, as BASE, RM and ITS-REST do today.
- `scaffold`: the file set is versioned. `assets/template-set.json` holds a revision, and each repo records its revision and file hashes in `.claude/scaffold.json`, so a later run upgrades the repo along the recorded migration path.
- `authoring` reference `asciidoc-syntax.md`: admonition, code-block and table conventions, linked from `authoring` and `content-patterns`.
- `docs/quick-start.md` (a first session, from install to an HTML preview) and `docs/prompting-guide.md` (which prompt to use for each authoring situation).

### Changed

- `publish` and `regen-classes` moved from `commands/` to `skills/` as user-only skills (`disable-model-invocation: true`). Claude Code treats `commands/` as the older format, so the plugin no longer ships that directory. The `/openehr-specs:publish` and `/openehr-specs:regen-classes` names are unchanged.
- `amendment-record` takes over the `amend` command: it accepts the same arguments (`argument-hint`), locates the amendment record, checks the working-tree diff, and stops after showing the diff. It no longer pre-approves `Read`, `Edit`, and `Bash` as the command did.
- `publish`, `authoring`, and the release checklist run the published `ghcr.io/openehr/asciidoctor` image instead of `openehr/asciidoctor`.
- `publish` runs only the published image. The local-script branch is gone because it omitted `-q`, so every `{pkg}` class-table include failed. The `specifications-AA_GLOBAL` checkout is still required. `authoring` says to pass `-q` with a local toolchain.
- `publish` and `regen-classes` keep only the runnable steps and guardrails; the background stays in `authoring` and `class-generation`.
- `scripts/validate.py` also checks the `scaffold` template set (templates exist and render, revisions have migration files, the digest matches) and no longer checks a `commands/` directory. CI runs the unit tests in `scripts/test_scaffold.py`.

### Removed

- `/openehr-specs:amend`, folded into `amendment-record`. Use `/openehr-specs:amendment-record <SPECXX-NN[,SPECPR-NN] — summary>` or a plain request. Removing a user-facing entry point is a major change under [docs/versioning.md](docs/versioning.md); it is released as a minor bump because the plugin is below 1.0.
- `docs/spec-style-guide.md`. The admonition, code-block and table conventions moved to `authoring/references/asciidoc-syntax.md`; the rest was already in `content-patterns`, `authoring` and `review`.

### Fixed

- `publish` no longer lists a `[spec-id]` argument, because the publisher builds whole components. It stops and asks when `$ARGUMENTS` is empty and always builds as `development`; a `Release-N.N.N` build belongs to `governance`.
- `publish` no longer trusts the build's `generated <file>` line, which is printed even when `asciidoctor` failed or includes are missing. It compares output timestamps before and after the build, scans the log for `ERROR` and `include file not found`, and reports each HTML file that was not rebuilt. `authoring` carries the same warning.
- `regen-classes` keeps the layout rule (`legacy-adoc` or `asciidoc`) and stops and asks when `$ARGUMENTS` is empty.
- `amendment-record`: a direct run states an assumed version bump and proceeds instead of pausing, and it stops after the diff only when invoked directly, not inside a release or authoring flow.

### Security

- `publish` and `regen-classes` no longer pre-approve every shell command while they run. `allowed-tools` was a bare `Bash`, which also covered `git commit` and `git push`. It now lists only the Docker image each skill runs, plus `docker --version` for `regen-classes`.

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
