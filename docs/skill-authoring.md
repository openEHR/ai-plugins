# Plugin and Skill Authoring Conventions

## Naming

- **Repo**: `openehr/ai-plugins` — vendor-neutral; the GitHub org carries the "made by openEHR" branding.
- **Marketplace `name`**: `openehr` — short attribution suffix in install commands (`/plugin install openehr-specs@openehr`).
- **Plugin names**: `openehr-<domain>` (e.g. `openehr-specs`). The `openehr-` prefix is mandatory: Claude Code plugin names live in a flat global namespace, so the prefix is what disambiguates them when users have plugins from multiple sources installed.
- **Skill and command names**: terse activity nouns with **no** `openehr-` or `spec-` prefix (e.g. `authoring`, `review`, `governance`). Skills are automatically namespaced as `<plugin>:<skill>` (`openehr-specs:review`), so repeating the plugin's words in a skill name is redundant.
- Do not duplicate tooling that already exists elsewhere in the community (e.g. CKM/clinical-modeling MCP and plugins are provided by Cadasto) — plugins here cover ground the Foundation itself owns, such as specification authoring and (potentially) conformance.

## Plugin Layout

Each plugin lives under `plugins/<plugin-name>/` and must contain:

- `.claude-plugin/plugin.json` — Claude Code plugin manifest (name, version, description, author, license, keywords)
- `.cursor-plugin/plugin.json` — Cursor plugin manifest (keep name, version, and metadata in sync with the Claude manifest; declare `skills` as `./skills/`)
- `README.md` — purpose, installation, and skill inventory for the plugin
- `skills/` — one subdirectory per skill, each with a `SKILL.md` (YAML frontmatter + markdown body)
- Skills may have a `references/` subdirectory for supplementary content

## Marketplace Manifest

`.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json` at the repo root list all plugins with their source paths. When adding a new plugin, add a matching entry to both `plugins` arrays.

Versioning and release tagging must stay in sync across three places — see [testing.md](testing.md#releasing).

## Skill Authoring

- `SKILL.md` files use YAML frontmatter (`name`, `description`) followed by markdown content.
- The `description` field is the always-on trigger metadata — keep it **lean (~50–75 words)**, since it sits in context every session. Follow this three-part pattern, in third person:
  1. **What + scope** — one sentence: what the skill does, anchored to the openEHR specs domain and the relevant repo (e.g. "openEHR specification documents … in `specifications-XX` repos"). This anchor is the scope limit; don't add a separate verbose "applies ONLY to … not to other standards" clause.
  2. **Triggers** — "This skill should be used when the user asks to …" with 3–5 *representative* (not exhaustive) actions/contexts. More phrases past that add length without improving triggering.
  3. **Anti-triggers** — a short "Not for …" that routes each overlapping case to the sibling skill or external plugin that owns it (e.g. archetype work → the `openehr-assistant` plugin).
- Keep skill content factual and grounded in openEHR specifications; do not invent identifiers, paths, or conventions.
- Reference files go in `references/` next to the SKILL.md; keep `SKILL.md` bodies focused (existing ones run ~150–400 lines) and push bulky supporting material to `references/`.
- Skill bodies that generate or review AsciiDoc must agree with the [spec style guide](spec-style-guide.md) — when changing one, check the other.
