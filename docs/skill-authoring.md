# Plugin and Skill Authoring Conventions

## Naming

- **Repo**: `openehr/ai-plugins` — vendor-neutral; the GitHub org carries the "made by openEHR" branding.
- **Marketplace `name`**: `openehr` — short attribution suffix in install commands (`/plugin install openehr-specs@openehr`).
- **Plugin names**: `openehr-<domain>` (e.g. `openehr-specs`). The `openehr-` prefix is mandatory: Claude Code plugin names live in a flat global namespace, so the prefix is what disambiguates them when users have plugins from multiple sources installed.
- **Skill names**: terse activity nouns with **no** `openehr-` or `spec-` prefix (e.g. `authoring`, `review`, `governance`). Skills are automatically namespaced as `<plugin>:<skill>` (`openehr-specs:review`), so repeating the plugin's words in a skill name is redundant.
- **Command and subagent names**: the same no-prefix rule applies. Name a command for its action (`amend`, `publish`, `regen-classes`) and a subagent for its job (`xref-auditor`, `identifier-grounding`). `spec-reviewer` is the one exception and keeps its name, because renaming it would be a major bump (see [versioning.md](versioning.md)).
- Do not duplicate tooling that already exists elsewhere in the community (e.g. CKM/clinical-modeling MCP and plugins are provided by Cadasto) — plugins here cover ground the Foundation itself owns, such as specification authoring and (potentially) conformance.

## Plugin Layout

Each plugin lives under `plugins/<plugin-name>/` and must contain:

- `.claude-plugin/plugin.json`: Claude Code plugin manifest (name, version, description, author, license, keywords)
- `.cursor-plugin/plugin.json`: Cursor plugin manifest (keep name, version, and metadata in sync with the Claude manifest; declare `skills` as `./skills/`)
- `README.md`: purpose, installation, and component inventory (skills, subagents, commands)
- `skills/`: one subdirectory per skill, each with a `SKILL.md` (YAML frontmatter and markdown body) and an optional `references/` subdirectory for supplementary content

A plugin may also contain:

- `agents/`: one `<agent>.md` per subagent
- `commands/`: one `<command>.md` per user-invoked action

See [Subagent and command authoring](#subagent-and-command-authoring) below.

## Marketplace Manifest

`.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json` at the repo root list all plugins with their source paths. When adding a new plugin, add a matching entry to both `plugins` arrays.

The plugin manifests, the marketplace entries, and the release tag must all carry the same version; see [versioning.md](versioning.md).

## Skill Authoring

- `SKILL.md` files use YAML frontmatter (`name`, `description`) followed by markdown content.
- The `description` field is the always-on trigger metadata — keep it **lean (~50–75 words)**, since it sits in context every session. Follow this three-part pattern, in third person:
  1. **What + scope** — one sentence: what the skill does, anchored to the openEHR specs domain and the relevant repo (e.g. "openEHR specification documents … in `specifications-XX` repos"). This anchor is the scope limit; don't add a separate verbose "applies ONLY to … not to other standards" clause.
  2. **Triggers** — "This skill should be used when the user asks to …" with 3–5 *representative* (not exhaustive) actions/contexts. More phrases past that add length without improving triggering.
  3. **Anti-triggers** — a short "Not for …" that routes each overlapping case to the sibling skill or external plugin that owns it (e.g. archetype work → the `openehr-assistant` plugin).
- Keep skill content factual and grounded in openEHR specifications; do not invent identifiers, paths, or conventions.
- Reference files go in `references/` next to the SKILL.md; keep `SKILL.md` bodies focused (none of the current ones exceeds 300 lines) and push bulky supporting material to `references/`.
- Skill bodies that generate or review AsciiDoc must agree with the [spec style guide](spec-style-guide.md) — when changing one, check the other.

## Subagent and Command Authoring

- Choose by the nature of the work: a **skill** holds knowledge or a workflow, a **command** is an action the user starts, and a **subagent** takes on context-heavy, multi-file, or adversarial work that would otherwise fill the main context.
- Both are flat markdown files with YAML frontmatter. `scripts/validate.py` requires `name` and `description` for a subagent and `description` for a command, and checks that any `name` matches the filename.
- Mark every command `disable-model-invocation: true`, so it does not compete with knowledge skills for triggering. CI does not check this.
- Commands and subagents point to the sibling skill that holds the knowledge; they do not repeat it.
- The ~50–75 word guideline above is written for skills. Write a subagent `description` as one line: the trigger conditions, then two to four typical triggers in prose, then a pointer to a "When to invoke" section in the agent body that holds the worked scenarios. Keep `: ` and ` #` out of the plain YAML value.
- Give a subagent only the `tools` it needs. A verifier gets read-only tools; name an MCP tool under both server prefixes (`mcp__<server>__<tool>` and `mcp__plugin_<plugin>_<server>__<tool>`).
- State in the prompt what the component does when an external tool is missing. For example, `xref-auditor` marks cross-spec anchors `UNCHECKED` when it has no web access.
