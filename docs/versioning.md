# Versioning and Releases

Each plugin is versioned independently using [semver](https://semver.org), adapted to plugin components:

| Bump | When |
|------|------|
| **Major** | A skill, subagent, or command is removed or renamed, or its behavior or scope changes incompatibly |
| **Minor** | A skill, subagent, or command is added, or an existing one's coverage is meaningfully expanded |
| **Patch** | Typos, clarifications, and reference fixes, with no change in behavior |

## Release Steps

Pull requests do not bump versions. A maintainer runs these steps at release.

1. Bump `version` in all four places (they must agree): the plugin's `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`, and the matching entries in `.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json`.
2. Run `python3 scripts/validate.py` — checks both manifest pairs agree.
3. In [CHANGELOG.md](../CHANGELOG.md), move the entries under `## Unreleased` into a new `## <plugin> <version> (<date>)` section.
4. Commit the version bump and the changelog entry. `claude plugin tag` refuses to run on a dirty working tree unless you pass `--force`.
5. Tag the release with `claude plugin tag plugins/<name>`. It creates `{name}--v{version}` and validates only the Claude manifests; step 2 covers Cursor.
6. Push commits and the tag.

The marketplace itself is not versioned. A plugin change reaches installed copies only when the plugin's `version` changes: Claude Code compares versions to decide whether to fetch a new copy, so a push to `main` without a bump does not reach users (see [Release a new version](https://code.claude.com/docs/en/plugin-marketplaces#release-a-new-version)). Users then update as described in [install.md](install.md#update).
