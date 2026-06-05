# Testing and Validation

This is a pure-content repository — JSON manifests + markdown skills. There is no build step, package manager, or automated test suite. Testing means installing the marketplace locally and validating structure and skill quality.

## Local Testing

Install the marketplace from your working copy (inside a Claude Code session):

```
/plugin marketplace add /path/to/ai-plugins
/plugin install openehr-specs@openehr
```

Then exercise the skills against a checkout of a `specifications-XX` repo: confirm each skill triggers on its documented phrases (see the `description` frontmatter) and does **not** trigger on its anti-trigger cases.

After editing skill content, reinstall (or restart the session) to pick up changes.

For Cursor, add your working copy as a local plugin marketplace and reload the plugin after changes — see [install.md](install.md#cursor).

## Validation

- **Manifest/skill validation** — `python3 scripts/validate.py` (also run by CI on every PR): checks Claude and Cursor JSON manifests, name/version sync, declared component paths, marketplace `owner.name`, and SKILL.md frontmatter.
- **Structural validation** — after creating or modifying plugin components, run the `plugin-dev:plugin-validator` agent: checks `plugin.json`, marketplace entry, directory layout, and frontmatter.
- **Skill quality review** — run the `plugin-dev:skill-reviewer` agent: checks description triggering quality, progressive disclosure, and content structure.
- **Token cost** — `claude plugin details openehr-specs` shows the component inventory and projected token cost; keep skill metadata lean.

## Releasing

See [versioning.md](versioning.md) for the semver policy and release steps.
