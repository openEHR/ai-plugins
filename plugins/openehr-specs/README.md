# openEHR Specifications

Skills and subagents for authors working in `specifications-XX` and `specifications-ITS-REST` repositories — AsciiDoc structure, amendment records, governance, quality review, prose patterns, ITS-REST OpenAPI sources, and BMM-based class documentation generation.

## Installation

### Claude Code

From the [ai-plugins](https://github.com/openEHR/ai-plugins) marketplace:

```text
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
| `amendment-record` | Amendment record entries and release boundaries; add an entry directly with `/openehr-specs:amendment-record <SPECXX-NN[,SPECPR-NN] — summary>` |
| `content-patterns` | Prose patterns for spec chapters and sections |
| `its-rest` | ITS-REST OpenAPI YAML and operation descriptions |
| `class-generation` | Generate class tables and UML diagrams from BMM via `bmm-publisher` |

### User-only action skills

Two skills run only when you type them: they do not auto-trigger, and their descriptions stay out of the session context. Each wraps a knowledge skill: `regen-classes` uses `class-generation`, and `publish` follows the preview step in `authoring`.

| Skill | Argument | Action |
|-------|----------|--------|
| `/openehr-specs:regen-classes` | `<schema-id> [-d <dependency-schema> ...]` | Regenerate class tables and diagrams via `bmm-publisher` (needs Docker) |
| `/openehr-specs:publish` | `<component>` | Build a local HTML preview with the `AA_GLOBAL` publisher (needs a sibling `specifications-AA_GLOBAL` checkout; falls back to Docker when `asciidoctor`, `jq`, or `bc` is missing, and checks that the HTML was rebuilt) |

## Subagents

Context-isolated subagents for heavy, multi-file, or verification work, dispatched by Claude (or ask for them by name). Each says in its prompt what it does when an optional dependency is absent, for example by marking a check `UNCHECKED`.

| Subagent | Purpose | Needs |
|-------|---------|-------|
| `spec-reviewer` | Runs the full `review` check catalog across an entire spec document, returns a findings report | `specifications-XX` (+ `AA_GLOBAL` for attribute checks) |
| `xref-auditor` | Verifies every `{openehr_*}` attribute and `<<anchor>>` resolves; checks cross-spec deep-link anchors against the target's Markdown twin | `specifications-XX` (+ `AA_GLOBAL` to resolve attributes); WebFetch (optional, for cross-spec anchors) |
| `identifier-grounding` | Fact-checks every RM/AM/BASE class/attribute a draft names against the published spec; flags invented identifiers | `openehr-assistant` MCP or WebFetch (optional) |

`AA_GLOBAL` is the `specifications-AA_GLOBAL` repository, which holds the boilerplate, publishing scripts, and styles shared by all spec repos. A Markdown twin is the Markdown version of a published spec page: swap `.html` for `.md` in its URL.

## Usage

In Claude Code, each skill is namespaced by the plugin, so it is invoked as **`/openehr-specs:<skill>`**. There are three ways to reach a skill:

1. **Invoke it explicitly**: type its name, optionally with an argument:
   ```text
   /openehr-specs:authoring
   /openehr-specs:review
   /openehr-specs:class-generation
   ```
2. **Browse the group**: type `/openehr` in the slash menu to list the plugin's skills together, or fuzzy-type a name (e.g. `review`) to jump straight to it.
3. **Let it trigger automatically**: Claude loads the right skill (or dispatches the right subagent) when your request matches its description. For example, "review this openEHR spec before release" activates `review` / `spec-reviewer`, and "regenerate the class tables for specifications-BASE" activates `class-generation`, with no slash command needed. (The action skills `/openehr-specs:publish` and `/openehr-specs:regen-classes` are user-only and never auto-trigger.)

Most skills act on the spec you are working in, so run them from a checkout of a `specifications-XX` repo (or name the target spec/file in your request).

> **Note:** newly installed or edited skills become available in the **next** Claude Code session.

## License

Apache 2.0 — see [LICENSE](../../LICENSE) in the marketplace repository.
