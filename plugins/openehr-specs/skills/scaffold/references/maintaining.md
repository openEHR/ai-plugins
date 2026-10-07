# Maintaining the scaffold template set

For maintainers of this plugin. Users run the `scaffold` skill; this file explains what it installs and
how to change that. Paths are relative to the skill directory
(`plugins/openehr-specs/skills/scaffold/`) unless they start with `scripts/` at the repo root.

## Layout

```
scaffold/
├── SKILL.md
├── assets/
│   ├── template-set.json        # the schema: revision, revisions, variables, files
│   └── templates/               # one template per file (and the two licence texts)
├── migrations/NNNN.json         # how to go from revision NNNN-1 to NNNN; created with revision 2
└── scripts/scaffold.py          # plan, apply, render, diff, check, seal
```

`migrations/` does not exist yet, because git does not track an empty directory. Create it with the first
migration file.

From the repo root:

- `python3 plugins/openehr-specs/skills/scaffold/scripts/scaffold.py check` validates the template set.
  `python3 scripts/validate.py` runs the same check in CI.
- `python3 -m unittest discover -s scripts -p 'test_*.py'` runs the tests (`scripts/test_scaffold.py`).

## File strategies

Each entry of `files` names a strategy, chosen by who owns the file after it is installed.

| Strategy | Used for | Behaviour |
|----------|----------|-----------|
| `seed` | `manifest.json`, `LICENSE`, `README.md` | Written once when absent, then the repo's own. Never changed. An `alternatives` list (`README.adoc`) counts as present. |
| `whole` | `.claude/CLAUDE.md` | Re-rendered on upgrade only if its hash still equals the recorded one; otherwise a `conflict`. |
| `json-merge` | `.claude/settings.json` | Adds keys and list items that are missing. Existing values always win, so a plugin set to `false` stays `false`. The descriptor remembers every template item it has offered, so an item the user removed afterwards is left out, and only items new in a later revision are added. Invalid JSON, or a top level that is not an object, is a `conflict`; `--overwrite` replaces the file with the template. |
| `ensure-lines` | `.gitignore`, `.asciidoctorconfig` | Appends missing lines with their comment header, and, like `json-merge`, leaves out a line the user removed after an earlier run. With a `key` regex, a line counts as present whatever its value (`:component: X`, and an unset `:name!:`); a differing value only produces a warning. |
| `regions` | `AGENTS.md` | Regions between `<!-- openehr-scaffold:begin ID -->` and `...:end ID -->` are managed, with a hash per region. Text outside them is the repo's. A file with no markers is `upgrade-manual`. Regions are applied independently: an `update` or `add` is written even when another region conflicts. |

`pinned` (in the descriptor, set with `--pin`) opts a file or `file:region` out for good. Regions the
user deleted are reported as `removed`, not added back; a region the descriptor never recorded is added.

**How a template change reaches repos.** Only `whole` and `regions` follow the hashes: an unmodified file
or region is updated, an edited one is reported as a `conflict`. `json-merge` and `ensure-lines` only add,
so a changed value in `claude-settings.json.tmpl`, `gitignore.tmpl` or `asciidoctorconfig.tmpl`
never propagates by itself, and neither does removing an item (a new item does, once); add a `note` step
to the migration for those. `seed` files
never change.

For every strategy, line endings (CRLF or LF) and the file mode are kept when a file is rewritten, a write goes to a temporary file that then replaces the target, and nothing is written through a symbolic link or outside the repo.

## Variables

`variables` in `template-set.json`: `required`, `default` (itself a template, may use earlier
variables), `default_if` (rules by regex on another variable), `pattern`, `choices`, `derived`
(`from` + `map`). Resolution order is explicit `--var`, then a value recorded in the repo's
descriptor as confirmed, then inference, then a recorded default, then the default. Unknown `--var`
names and empty required values are rejected.

- Inference reads `manifest.json`, `.asciidoctorconfig`, the git remote, the directory name,
  `computable/BMM`, `origin/HEAD` (for `default_branch`) and the `LICENSE` text.
- The descriptor lists which recorded values were only defaults (`defaulted`). Inference replaces those, so a
  BMM schema added to the repo later is picked up as a new guess; a value the user confirmed is kept.
- A value that fails its `pattern` is reported, not guessed: `SPEC{{component}}` is invalid for
  `ITS-REST`, so it must come from the manifest or the user.

## The descriptor in a scaffolded repo

`.claude/scaffold.json`: `template_set`, `revision`, `variables` (everything resolved at install time,
so an upgrade does not ask again), `files` (`sha256` for `whole`, per-region hashes for `regions`) and
`pinned`. The hashes are what tell "unmodified since scaffolded" from "edited by hand".

It lives in `.claude/` because `manifest.json` is the repo's own file, read by the publisher, and a merge would reformat it and put hashes into every diff; a root-level dot file would add clutter. It is committed.

## Changing the set

1. **Before the first release that contains this skill**, edit revision 1 and run `scaffold.py seal`.
2. **After it ships**, any change to a template, a variable or a `files` entry needs a new revision:
   - raise `revision`, append an entry to `revisions` (`revision`, `released`, `summary`, empty `digest`);
   - create `migrations/NNNN.json` for it, even when it has no steps;
   - run `scaffold.py seal`.

   `check` fails when the digest of the templates, variables and files does not match the latest
   revision, when revisions have gaps, or when a migration file is missing or malformed. That is what
   keeps old repos upgradable.

Migration file:

```json
{
  "from": 1,
  "to": 2,
  "steps": [
    { "op": "rename", "from": ".old/path", "to": ".new/path" },
    { "op": "delete", "path": "docs/obsolete.adoc", "file_id": "obsolete" },
    { "op": "note", "text": "Add the new `foo` key to manifest.json by hand." }
  ]
}
```

`rename` moves a file when the source exists and the target does not. `delete` removes a file only when
its hash equals the `sha256` recorded for `file_id`, which only `whole` files have; for any other file it
is skipped. `note` is shown to the user as a manual step. A new required variable needs no step: the next
plan asks for it.

## Where the conventions come from

Surveyed on 2026-10-07 across the `specifications-*` clones (18 with a git directory).

- **Standard files.** `AGENTS.md`, `.claude/*` and `.asciidoctorconfig` exist only in some repos. BASE and
  RM have identical `.claude/settings.json` and `.gitignore`. Five repos (AM, BASE, LANG, RM, TERM) have
  an identical `.asciidoctorconfig` apart from `:component:`; PROC adds `:diagrams_uri:`.
- **README.** Every clone has one: `README.adoc` in 15, `README.md` in 3 (LANG, ITS, ITS-BMM). The seed
  target is `README.md`, as requested; `alternatives` keeps it from duplicating an existing
  `README.adoc`.
- **Licence.** Two families: CC BY-SA 3.0 (12 repos, byte-identical) and Apache 2.0 (the `ITS-*` repos).
  The texts in `assets/templates/` are copies of BASE's and ITS-REST's `LICENSE`.
- **Default branch.** `master` in all 18 clones.
- **Commit messages.** Of 2,988 non-merge commits (up to 300 per repo), 968 name a `SPEC*` ticket. In BASE,
  RM and AM, the models for the template, the leading `Changes for SPECXX-NN - <text>` form is by far the
  most common (154 commits against 24 with the key last), and BASE's `AGENTS.md` documents it. Across the
  nine key-heavy repos (those three plus QUERY, ITS-REST, ITS-XML, PROC, LANG, TERM) the trailing
  `<text> (SPECXX-NN)` form is more common (333 against 221) and newer (median December 2022 against
  December 2019), driven by QUERY and the ITS repos. The template makes the leading form primary and says
  the trailing form is understood. About 2,000 commits carry no key at all.
- **Not verified for every repo:** "do not stage regenerated `docs/*.html`" comes from BASE's practice (its
  commits are source-only) and the note in its `AGENTS.md` that the HTML is a build artefact.

## Known limits

- AsciiDoc specification repos only, with an optional BMM schema. An OpenAPI repo (`specifications-ITS-REST`,
  built with `make`) needs its own variant of `AGENTS.md`; until then, pin `agents`, `claude-md` and
  `asciidoctorconfig` there.
- One BMM schema per repo. When several are found (AM has 1.4.0 and 2.4.0, LANG has three) the highest
  version is used and a warning lists the others; pass `--var bmm_schema_id=<id>` to choose.
- `json-merge` rewrites the file with two-space indentation when it adds something, and any rewrite drops
  a byte-order mark. `.gitignore` is matched line by line: negations (`!x`) and anchoring are not
  understood, so a user who negates a pattern the template adds should pin the file.
- Region markers must start a line. A marker shown inside a fenced code block is still read as a marker,
  so do not quote them in `AGENTS.md`.
- Migration steps run before files are planned, so a dry `plan` shows file actions for the tree as it is
  now; `apply` re-plans after the steps.
