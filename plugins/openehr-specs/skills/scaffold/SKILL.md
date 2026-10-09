---
name: scaffold
description: Initialise a specification repository, or bring an existing one up to the current standard file set (AGENTS.md, .claude settings, manifest.json, .gitignore, LICENSE, README, and in a new repository a computable/BMM schema)
argument-hint: "[component id, e.g. BASE]"
allowed-tools:
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py plan *)"
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py apply *)"
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py render *)"
  - "Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py diff *)"
  - "Bash(git init *)"
  - Read
disable-model-invocation: true
---

Install or upgrade the standard file set in the repository at the current directory: a
`specifications-XX` repo, or a new empty one. `$ARGUMENTS` may name the component. The file set, its
variables and its revision history are in `${CLAUDE_SKILL_DIR}/assets/template-set.json`;
`${CLAUDE_SKILL_DIR}/scripts/scaffold.py` (Python 3.8+, standard library only) performs the file
operations. Let the script write the managed files; edit by hand only in the cases that steps 3 and 5
name. If `python3` is missing, say so and stop. In a tool that does not expand `${CLAUDE_SKILL_DIR}`,
use the directory that holds this SKILL.md.

The set covers AsciiDoc specification repos, with an optional BMM schema. In an OpenAPI repo such as
`specifications-ITS-REST`, pin `agents`, `claude-md` and `asciidoctorconfig` (step 4): they are
AsciiDoc-specific. Pin `bmm` too when a new repo has no model.

A new repository (plan `mode` `init`) also gets `computable/BMM/<bmm_schema_id>.bmm.json` (file id
`bmm`). The script asks the local `ghcr.io/openehr/bmm-publisher` image for the schemas it bundles
and copies the highest version for the component. When the image bundles none, it writes an empty
schema: one root package `org.openehr.<name>`, no classes, BASE included for other components, and
`rm_release` equal to `first_release`. The check needs Docker and the image, and never pulls it.
Existing repositories are not offered a schema.

## Steps

1. **Plan.** Run `python3 ${CLAUDE_SKILL_DIR}/scripts/scaffold.py plan --repo .`, adding
   `--var component=<id>` when `$ARGUMENTS` names one. It writes nothing and prints JSON: `mode`,
   `repo`, `variables` (each with its source), `missing_variables`, `invalid_variables`, `files`,
   `migration_steps`, `warnings`, `todo_markers`. Confirm that `repo` is the repository root the user
   means. The modes are `init` (none of the files exist yet), `upgrade` (some do: `recorded_revision` is
   null when the repo was never scaffolded, otherwise it is older than `latest_revision` and
   `migration_path` lists the revisions to apply, in order) and `current`. If the output is
   `{"error": ...}`, show the message and stop; do not edit `.claude/scaffold.json` to get past it
   (for example "update the openehr-specs plugin" means a newer plugin scaffolded this repo).
2. **Variables.** When `status` is `needs_input`, ask for each missing or invalid variable, then plan
   again with `--var name=value`. A variable whose source is `default` or starts with `inferred` is a
   guess. Ask the user to confirm the ones that matter (`license`, `jira_project`, `bmm_schema_id`,
   `base_bmm_schema_id`, `default_branch`, `published_url`, and `first_release` only when the plan creates
   `manifest.json` or a new empty BMM schema, the files that use it) and list the rest in one line. In a
   new repository, `bmm_schema_id` comes from `inferred: bmm-publisher image` or `inferred: new empty
   schema`. Never invent a
   title, a Jira key or a filter id. Values the user confirmed earlier are recorded in
   `.claude/scaffold.json` and kept; a recorded default is not, so a BMM schema added later shows up
   as a new guess to confirm. `--overwrite` and `--pin` accept only the file ids and `agents:<region>`
   ids that `files` lists; anything else is an error.
3. **Review.** Summarise the `files` by action and ask before applying. Show the `detail` of every
   `merge`, `conflict` and `exists` entry (a `LICENSE` that differs from the standard text) and every
   `warnings` entry.
   - `create`, `merge`, `update`: the script writes. For `.claude/settings.json`, say what it grants:
     the `openehr` marketplace, four enabled plugins, pre-approved `git add`, `git commit` and
     `git diff`, WebFetch on `specifications.openehr.org`, and three read-only Atlassian MCP calls.
     If the user wants the `git add` and `git commit` rules gone, remove them from the file after
     applying: later runs leave out what the user removed, and add only what a newer revision
     introduces.
   - `create` for `bmm`: say from its `detail` whether the schema is copied from the image or new and
     empty.
   - `blocked` (only `bmm`): the image could not be checked, and `detail` says why. Offer to start
     Docker, or to run `docker pull ghcr.io/openehr/bmm-publisher` (a large download; ask first), and
     plan again. Or create the empty schema the `detail` names with `--var bmm_schema_id=<id>`. Applying
     anyway writes the other files without a schema; `--overwrite bmm` adds one later.
   - `exists`, `exists-alternative` (for example `README.adoc`), `unchanged`, `pinned`, `skipped` (no BMM
     schema is offered to an existing repository; `--overwrite bmm` asks for one): nothing to do.
     A `conflict` whose `detail` says the file is a symbolic link cannot be resolved with `--overwrite`:
     the user has to replace the link first.
   - `conflict`: `detail` says whether the file was edited since it was scaffolded or simply differs.
     Show the difference with `diff --repo . --file <id>` (repeat the `--var` options), then ask:
     keep it, take the template (`--overwrite <id>`), or leave it alone for good (`--pin <id>`). In
     `AGENTS.md`, each entry of `files[].regions` has its own action and id: use it as
     `--overwrite agents:<region>` or `--pin agents:<region>`. Regions marked `update` or `add` are
     written even when another region conflicts; `removed` means the user deleted the region, and
     nothing is done.
   - `upgrade-manual`: `AGENTS.md` exists without scaffold regions. Print the template with
     `render --repo . --file agents` (repeat the `--var` options), compare it with the file, and offer
     to edit the file so the shared sections sit between the
     `<!-- openehr-scaffold:begin <id> -->` markers, or to pin it.
   - `migration_steps`: show them, with each `note` as a manual step. The file actions shown are for
     the tree as it is now; `apply` re-plans after running the steps and returns each step's `result`.
   - Nothing but `unchanged`, `exists`, `exists-alternative`, `pinned` and `skipped`, and no
     `migration_steps`: report "up to date" and stop.
   - A directory that is not a git repository: offer `git init -b <default_branch>`; if git itself is
     missing, say so.
4. **Apply.** Run the same command with `apply`, repeating the `--var` options and adding the
   `--overwrite` and `--pin` options the user chose. Check that the output has `applied: true`;
   `status: needs_input` means nothing was written. The script never changes an existing seed file
   (`manifest.json`, `LICENSE`, `README.md`, a BMM schema), never rewrites a hand-edited file or region without
   `--overwrite`, and records the revision, variables and file hashes in `.claude/scaffold.json`.
5. **Finish.** List `written`. For each `todo_markers` entry (a `TODO(scaffold)` comment in
   `AGENTS.md`), offer to fill it from the repo's content and delete the comment once it is filled.
   When `manifest.json` was created, point out that its `specifications` list starts empty (skill
   `openehr-specs:authoring`). When an empty BMM schema was created, point out that classes go into it
   (skill `openehr-specs:bmm-authoring`, which also checks it) and the class tables are generated
   from it (skill `openehr-specs:class-generation`); until then
   bmm-publisher warns about the empty package. Do not commit; if the user asks for a commit message, follow the
   Conventions section of the repo's `AGENTS.md`.

## Rules

- Text between `<!-- openehr-scaffold:begin <id> -->` and `<!-- openehr-scaffold:end <id> -->` belongs
  to the template and is replaced on upgrade while it is unmodified. Text outside the markers belongs
  to the repo and is never touched.
- To keep a region different in one repo, pin it (`--pin agents:<region>`; to unpin, remove it from
  `pinned` in `.claude/scaffold.json`). Changing what a region says for every repo is a change to the
  plugin's template set.
- Run the skill again later to upgrade: the recorded revision is compared with the latest.
- Repository-specific guidance, such as what `/init` would write into a root `CLAUDE.md`, goes into
  `AGENTS.md` outside the regions. `.claude/CLAUDE.md` only imports `AGENTS.md`; a second `CLAUDE.md`
  would duplicate it.

To change the template set, add a revision, or understand a file strategy, read
`${CLAUDE_SKILL_DIR}/references/maintaining.md`.
