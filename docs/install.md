# Installing the openEHR Plugins

The plugins in this repository are distributed as a dual marketplace: [Claude Code](https://code.claude.com/docs/en/plugins) (`.claude-plugin/`) and [Cursor](https://cursor.com/docs/plugins) (`.cursor-plugin/`). Skill content is shared; only the manifest layer differs.

## Claude Code

### Install

Inside a Claude Code session:

```text
/plugin marketplace add openEHR/ai-plugins
/plugin install openehr-specs@openehr
```

The marketplace name is `openehr`, so installed plugins are addressed as `<plugin>@openehr`.

### Update

```text
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

Cursor installs plugins from the **Customize** page. To add this repository as a marketplace, import it as a team marketplace, which needs a Teams or Enterprise plan:

1. Open **Dashboard → Plugins & MCPs**.
2. Under **Team Marketplaces**, click **Add Marketplace**, then **Import from Repo**.
3. Paste `https://github.com/openEHR/ai-plugins`.
4. Install **openehr-specs** from **Customize**.

See the [Cursor plugin documentation](https://cursor.com/docs/plugins) for the full flow. To try a local copy, see [testing.md](testing.md#local-testing).

The repo root contains `.cursor-plugin/marketplace.json`, and each plugin under `plugins/<name>/` has its own `.cursor-plugin/plugin.json`. See [plugins/openehr-specs/README.md](../plugins/openehr-specs/README.md) for the component inventory.
