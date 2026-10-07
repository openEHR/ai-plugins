# Prompting guide

Prompts for the situations that come up when you work on an openEHR specification repository with the `openehr-specs` plugin, with what each one triggers and what to check in the result. It assumes the plugin is installed ([install.md](install.md)); the [quick start](quick-start.md) walks through a first session.

The skills cover the specification sources. For archetypes, templates, AQL and terminology, use the `openehr-assistant` plugin.

In the prompts, `<XX>` is a component id such as `RM`, `BASE` or `AM`, and `<spec-id>` is the name of a directory under `docs/`. Run Claude Code from the spec repository, with two exceptions: `/openehr-specs:publish` needs the parent directory that holds all the `specifications-*` clones, and `/openehr-specs:scaffold` needs the repository root.

| Situation | Skill, subagent or command |
|-----------|----------------------------|
| [Start a new specification](#start-a-new-specification) | `authoring` |
| [Add or change a chapter, figure or link](#add-or-change-a-chapter-figure-or-link) | `authoring` |
| [Draft or improve spec prose](#draft-or-improve-spec-prose) | `content-patterns` |
| [Record a change in the amendment record](#record-a-change-in-the-amendment-record) | `amendment-record` |
| [Change a class, attribute or invariant](#change-a-class-attribute-or-invariant) | `class-generation`, `/openehr-specs:regen-classes` |
| [Review before you merge](#review-before-you-merge) | `review`, `spec-reviewer`, `xref-auditor`, `identifier-grounding` |
| [Preview the HTML](#preview-the-html) | `/openehr-specs:publish` |
| [Releases, status changes and the CR/PR process](#releases-status-changes-and-the-crpr-process) | `governance` |
| [Edit the ITS-REST API](#edit-the-its-rest-api) | `its-rest` |
| [Set up or upgrade a repository](#set-up-or-upgrade-a-repository) | `/openehr-specs:scaffold` |
| [Write a commit message](#write-a-commit-message) | the repository's `AGENTS.md` |

## What makes a prompt work

- **Name the target.** Give the repository, the spec directory or the file, so Claude does not have to ask which spec you mean.
- **Give the ticket key and your name.** The amendment record entry needs the Jira key and the raiser, and the ITS-REST entry needs the ticket, the raiser and the date. Claude asks for what is missing rather than inventing it.
- **Say whether Claude may edit.** The review skill reports findings and edits only when you ask.
- **Force a skill by typing its name.** Claude loads a skill when your request matches its description. If it does not, type `/openehr-specs:<skill>`. The three action skills (`publish`, `regen-classes`, `scaffold`) run only when you type them.
- **Read the diff.** The amendment record, class generation, `publish`, `regen-classes` and `scaffold` skills do not commit. The release steps in `governance` do, and Claude asks before it pushes.

## Start a new specification

Agree the identifier and placement with the Specifications Editorial Committee (SEC) first; it verifies both for new specs (`governance`).

```text
Create a new specification document with id <spec-id> in specifications-<XX>: manifest_vars.adoc, master.adoc, the amendment record, a preface and an overview chapter, plus its entry in manifest.json. Status is <STATUS>, copyright year <year>.
```

Use the status the SEC assigned for `<STATUS>` (for example `DEVELOPMENT`). Claude keeps `spec_status` identical in `manifest.json` and `manifest_vars.adoc`. Check that the chapter files are numbered without gaps and that `master.adoc` includes each one.

## Add or change a chapter, figure or link

```text
Add a chapter "Versioning" to the <spec-id> spec in specifications-<XX>, numbered and named to follow the existing chapters, and include it in master.adoc.
```

```text
Add the diagram docs/<spec-id>/diagrams/<file>.svg to the overview chapter as a titled figure with an id.
```

```text
Link the first mention of DV_QUANTITY in master04-<name>.adoc to the Data Types spec.
```

Cross-spec links use the `{openehr_*}` attributes from `reference_definitions.adoc`, not pasted URLs. When the attribute you need is missing, Claude adds it to `specifications-AA_GLOBAL`, which is a separate repository and a separate commit, and tells you so.

## Draft or improve spec prose

```text
Draft the Overview section for the <package> package in master03-<name>.adoc using the package overview pattern: opening paragraph, figure placeholder, then the list of classes. Use only class names that exist in the published RM.
```

```text
Rewrite this section in the design rationale pattern: the requirement, the chosen design, and the alternatives rejected. <paste or name the section>
```

The `content-patterns` skill has a catalogue of patterns, among them package overview, class semantics and design rationale. Name the one you want. It writes in the register the library uses: third person, present tense, no contractions. After drafting, ask for a fact-check of the names (see [Review before you merge](#review-before-you-merge)).

## Record a change in the amendment record

```text
/openehr-specs:amendment-record SPECRM-142 - add tags to LOCATABLE; addresses SPECPR-401
```

A plain request works as well: "Add an amendment entry for SPECRM-142 to the EHR spec."

Claude reads the current record, then asks for anything missing, usually the raiser. It picks the version bump (patch for corrections, minor for new content or semantic changes, major for a restructure), adds the entry at the top, moves the `[[latest_issue]]` and `[[latest_issue_date]]` anchors, and uses today's date unless you give one. If you made the change already, Claude checks `git status` and the diff stat first, so the entry describes what changed. It shows the diff and stops.

To put two changes under one version, say so: "same version as the top entry".

## Change a class, attribute or invariant

Class tables in `docs/UML/classes/` are generated from the BMM schema, so the change goes in the BMM and the tables are regenerated. Editing the BMM follows the repository's own `AGENTS.md`; the plugin's skills cover the generation.

```text
In the BMM for this repo, add an optional attribute <name> of type <Type> to class <CLASS>, with documentation, following this repo's AGENTS.md.
```

```text
Regenerate the class tables for <XX> from the BMM in this checkout, not the copy bundled in the publisher image. Compare with docs/UML/classes and copy over only the tables that changed.
```

Say "from this checkout". A bare schema id such as `openehr_base_1.3.0` makes the publisher use the schema bundled in its Docker image, which can lag the repository. The `class-generation` skill covers mounting your own schemas, and the repository's `AGENTS.md` may carry the exact command. Docker is required.

To see what the image's bundled schemas produce, type:

```text
/openehr-specs:regen-classes openehr_rm_1.2.0 -d openehr_base_1.3.0
```

It writes to `out/` in the working directory and places nothing in a repository, so run it from a scratch directory. Its output reflects the bundled schemas; for tables to commit, use the previous prompt.

## Review before you merge

One chapter, inline:

```text
Review docs/<spec-id>/master03-<name>.adoc against the review checks. Report findings only.
```

A whole spec directory, in an isolated context. The `spec-reviewer` subagent also takes a whole component:

```text
Run the spec-reviewer subagent on docs/<spec-id>/ and give me the findings table.
```

Links, after a large edit:

```text
Run the xref-auditor subagent on docs/<spec-id>/: every {openehr_*} attribute and <<anchor>>, and the cross-spec deep links.
```

Names, after drafting:

```text
Run the identifier-grounding subagent on master04-<name>.adoc and flag any class, attribute or function name that does not exist in the published specifications.
```

The review skill reports each finding as `ERROR`, `WARNING` or `INFO` with a `file:line` location, grouped by check category. It checks sources statically, so missing includes and images show up only in a build ([Preview the HTML](#preview-the-html)). To have Claude apply the fixes, ask: "Fix the ERRORs, leave the warnings for me."

`xref-auditor` resolves attributes against the sibling `specifications-AA_GLOBAL` checkout and uses web access only for cross-spec deep-link anchors, which it marks `UNCHECKED` without it. `identifier-grounding` checks names through the `openehr-assistant` MCP server, the published Markdown twins or the local sibling repositories, and marks what it cannot verify `UNVERIFIED`.

## Preview the HTML

```text
/openehr-specs:publish <XX>
```

The build mounts the working directory, so run it from the parent directory that holds the `specifications-*` clones. It needs Docker and the sibling `specifications-AA_GLOBAL` checkout, builds the whole component as the `development` release, and reports any file that was not rebuilt and any `ERROR` or `include file not found` line. The build rewrites the tracked `docs/*.html` files; leave them out of your commit.

## Releases, status changes and the CR/PR process

```text
Prepare Release-<N.N.N> of specifications-<XX> with the release checklist. Do the manifest.json and git steps, and stop before pushing.
```

```text
The SEC promoted my spec from Development to Trial. What changes in manifest.json and manifest_vars.adoc?
```

```text
Should this change be a problem report or a change request, and who can raise it?
```

Only SEC members create change requests; anyone can raise a problem report on the `SPECPR` tracker. The Jira steps of a release are yours, and Claude asks you to confirm them. It asks before it pushes. For a fix release it confirms with you first, because the push overwrites the deployed release. The promotion criteria are the SEC's: Claude sets the new status in both files once you confirm that the SEC approved it.

## Edit the ITS-REST API

```text
In specifications-ITS-REST, add a <resource>_<action> operation for <HTTP method> <path>. Reuse the shared parameters and responses, add or reference the schema, wire it into ehr.openapi.yaml, then bundle and validate.
```

Claude asks for the `SPECITS` ticket, the raiser and the date for the amendment record entry. Docker is needed for `make bundle` and `make validate`. The AsciiDoc documents under that repo's `docs/` (`simplified_formats`, `smart_app_launch`) follow `authoring`, not `its-rest`.

## Set up or upgrade a repository

```text
/openehr-specs:scaffold <XX>
```

Run it from the repository root, for a new, empty repository or an existing one. Claude plans first: it shows what it would create, merge or leave alone, and asks about guessed values such as the licence, Jira key and BMM schema. It writes only after you agree. It installs the standard file set, listed in the [plugin README](../plugins/openehr-specs/README.md), and records the revision in `.claude/scaffold.json` so a later run can upgrade the repository. Run it again after a plugin update. It needs `python3` and is written for Claude Code.

## Write a commit message

```text
Write the commit message for my staged changes.
```

This follows the Conventions section of the repository's `AGENTS.md`, which `/openehr-specs:scaffold` installs: `Changes for SPECXX-NN - <what changed>`. Claude takes the key from you, then from the branch name (`feat/SPECXX-42-<slug>`), and writes no key when it has none, rather than guessing.
