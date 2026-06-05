# Versioning and Releases

Each plugin is versioned independently using [semver](https://semver.org), adapted to skill content:

| Bump | When |
|------|------|
| **Major** | Skill removed/renamed, or its behavior/scope changes incompatibly |
| **Minor** | New skill added, or existing skill's coverage meaningfully expanded |
| **Patch** | Typos, clarifications, reference fixes — no behavior change |

## Release Steps

1. Bump `version` in all four places (they must agree): the plugin's `.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`, and the matching entries in `.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json`.
2. Run `python3 scripts/validate.py` — checks both manifest pairs agree.
3. Add an entry to the repo-level [CHANGELOG.md](../CHANGELOG.md).
4. Tag: `claude plugin tag plugins/<name>` — creates `{name}--v{version}` (validates the Claude pair only).
5. Push commits and the tag.

The marketplace itself is not versioned — users always get the current `main`.
