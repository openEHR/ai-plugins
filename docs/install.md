# Installing the openEHR Plugins

The plugins in this repository are distributed as a dual marketplace: [Claude Code](https://docs.claude.com/en/docs/claude-code/plugins) (`.claude-plugin/`) and [Cursor](https://cursor.com/docs/plugins) (`.cursor-plugin/`). Skill content is shared; only the manifest layer differs.

## Claude Code

### Install

Inside a Claude Code session:

```
/plugin marketplace add openEHR/ai-plugins
/plugin install openehr-specs@openehr
```

The marketplace name is `openehr`, so installed plugins are addressed as `<plugin>@openehr`.

### Update

```
/plugin marketplace update openehr
/plugin update openehr-specs
```

A restart of the session is required for an update to take effect.

### Inspect

To see a plugin's component inventory (skills, commands, agents) and its projected token cost:

```bash
claude plugin details openehr-specs
```

## Cursor

Add this repository as a plugin marketplace (from **Settings → Plugins**, or your team’s documented marketplace URL), then install **openehr-specs**. The repo root must contain `.cursor-plugin/marketplace.json`; each plugin under `plugins/<name>/` has its own `.cursor-plugin/plugin.json`.

After changing skills locally, reload or reinstall the plugin so Cursor picks up updates. See [plugins/openehr-specs/README.md](../plugins/openehr-specs/README.md) for the skill inventory.

## Available Plugins

| Plugin | Purpose |
|--------|---------|
| `openehr-specs` | Creating, editing, and reviewing openEHR specification documents (AsciiDoc and OpenAPI/ITS-REST), specification governance, content quality and convention compliance |
