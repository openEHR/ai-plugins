## Summary

<!-- What does this PR change, and why? -->

## Checklist

- [ ] `python3 scripts/validate.py` passes
- [ ] Skill triggering tested locally in Claude Code (see [docs/testing.md](../docs/testing.md))
- [ ] Cursor install tested locally when plugin or manifest content changed (see [docs/install.md](../docs/install.md#cursor))
- [ ] Both marketplaces updated when plugin metadata changed: `.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json` (plus matching `plugin.json` files under `plugins/<name>/`)
- [ ] Plugin version bumped and [CHANGELOG.md](../CHANGELOG.md) updated (if plugin content changed)
- [ ] Content grounded in published openEHR specifications — no invented identifiers
