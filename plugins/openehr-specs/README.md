# openEHR Specifications

Skills for authors working in `specifications-XX` and `specifications-ITS-REST` repositories — AsciiDoc structure, amendment records, governance, quality review, prose patterns, ITS-REST OpenAPI sources, and BMM-based class documentation generation.

## Installation

### Claude Code

From the [ai-plugins](https://github.com/openEHR/ai-plugins) marketplace:

```
/plugin marketplace add openEHR/ai-plugins
/plugin install openehr-specs@openehr
```

### Cursor

Add the marketplace from this repository (or a fork), then install `openehr-specs`. See [docs/install.md](../../docs/install.md) for details.

## Skills

| Skill | Purpose |
|-------|---------|
| `authoring` | Create and edit AsciiDoc specification documents and manifests |
| `review` | Pre-release quality and convention review |
| `governance` | Releases, change requests, and lifecycle states |
| `amendment-record` | Amendment record entries and release boundaries |
| `content-patterns` | Prose patterns for spec chapters and sections |
| `its-rest` | ITS-REST OpenAPI YAML and operation descriptions |
| `class-generation` | Generate class tables and UML diagrams from BMM via `bmm-publisher` |

## Usage

Each skill is namespaced by the plugin, so it is invoked as **`/openehr-specs:<skill>`**. There are three ways to reach a skill:

1. **Invoke it explicitly** — type the command, optionally with an argument:
   ```
   /openehr-specs:authoring
   /openehr-specs:review
   /openehr-specs:class-generation
   ```
2. **Browse the group** — type `/openehr` in the slash menu to list all seven skills together, or fuzzy-type a skill name (e.g. `review`) to jump straight to it.
3. **Let it trigger automatically** — Claude loads the right skill when your request matches its description. For example, "review this openEHR spec before release" activates `review`, and "regenerate the class tables for specifications-BASE" activates `class-generation` — no command needed.

Most skills act on the spec you are working in, so run them from a checkout of a `specifications-XX` repo (or name the target spec/file in your request).

> **Note:** newly installed or edited skills become available in the **next** Claude Code session.

## License

Apache 2.0 — see [LICENSE](../../LICENSE) in the marketplace repository.
