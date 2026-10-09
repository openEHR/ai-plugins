# Testing and Validation

This is a pure-content repository: JSON manifests plus markdown skills (including user-only action skills) and subagents. There is no build step or package manager, and the only automated tests are for the scripts bundled with the `scaffold` and `bmm-authoring` skills. Testing means installing the marketplace locally and validating structure and skill quality.

## Local Testing

Install the marketplace from your working copy (inside a Claude Code session):

```text
/plugin marketplace add /path/to/ai-plugins
/plugin install openehr-specs@openehr
```

Then exercise the skills against a checkout of a `specifications-XX` repo: confirm each skill triggers on its documented phrases (see the `description` frontmatter) and does **not** trigger on its anti-trigger cases.

The user-only action skills (`publish`, `regen-classes`, `scaffold`) run only when you type them (`/openehr-specs:<skill>`): confirm that a plain request does not start one. Subagents are dispatched when a request matches their `description`, and you can also ask for one by name: confirm both. `publish` and `regen-classes` need Docker, and `publish` also needs a sibling `specifications-AA_GLOBAL` checkout; `scaffold` needs `python3` and writes files into the repository it runs in, so try it in an empty or scratch directory first (see the [plugin README](../plugins/openehr-specs/README.md)).

After editing skill content, reinstall (or restart the session) to pick up changes.

For Cursor, copy `plugins/openehr-specs` to `~/.cursor/plugins/local/openehr-specs`, then restart Cursor or run **Developer: Reload Window** and check **Customize** for the components. Cursor skips a symlink that points outside that folder, and Teams and Enterprise admins can turn local plugin imports off. See [Cursor's local testing steps](https://cursor.com/docs/plugins.md#test-plugins-locally).

## Validation

- **Manifest and frontmatter validation**: `python3 scripts/validate.py` (CI runs it on every PR) checks the Claude and Cursor JSON manifests, name and version sync, declared component paths, and the marketplace `owner.name`. For every skill and subagent it checks that `name` and `description` exist and that `name` matches the directory or file name. It also runs the `scaffold` template-set check (`scaffold.py check`: templates exist and render, revisions are contiguous, every revision has a migration file, and the template digest matches the latest revision), and that the `bmm-authoring`, `class-generation`, `regen-classes` and `scaffold` skills each name every repo the template set excludes from BMM work. It does not check description length, `disable-model-invocation`, the README inventories, or the release tag.
- **Script tests**: `python3 -m unittest discover -s scripts -p 'test_*.py'` (CI runs it on every PR) tests both bundled scripts in temporary directories. For `scaffold` it covers the template engine, each file strategy, variable inference, and upgrades across revisions. For the `bmm-authoring` checker it covers each finding and exit code, a clean run on the worked example, and a wrongly typed value at any node of the worked example, which must give a finding and not a traceback. Run it after changing either script, the template set, or the worked example.
- **Built-in manifest check**: `claude plugin validate plugins/openehr-specs` validates the plugin manifest; add `--strict` to treat warnings as errors.
- **Structural validation**: after creating or modifying plugin components, run the `plugin-dev:plugin-validator` agent. It checks `plugin.json`, the marketplace entry, directory layout, and frontmatter. The agent comes from the `plugin-dev` plugin, which this repo enables in `.claude/settings.json`.
- **Skill quality review**: run the `plugin-dev:skill-reviewer` agent (also from `plugin-dev`). It checks description triggering quality, progressive disclosure, and content structure.
- **Token cost**: `claude plugin details openehr-specs` shows the component inventory and projected token cost; keep skill metadata lean.

## Releasing

See [versioning.md](versioning.md) for the semver policy and release steps.
