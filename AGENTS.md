# ai-plugins

AI-assistant plugins for openEHR — official plugin marketplace of the openEHR Foundation.

## Repository Purpose

This repo contains AI-assistant plugins that support openEHR work — packaged as a dual Claude Code and Cursor plugin marketplace; the skill content (`SKILL.md`, an open cross-tool format) is the canonical artifact, and each assistant gets a thin manifest layer (`.claude-plugin/`, `.cursor-plugin/`) around the same skills, so further assistants can be added the same way. It is **not** a specification repository — it provides AI-assisted tooling for authors working in `specifications-XX` repos.

## Structure

```
ai-plugins/
├── .claude-plugin/marketplace.json    # Claude Code marketplace manifest
├── .cursor-plugin/marketplace.json    # Cursor marketplace manifest
├── docs/                              # Contributor and user documentation
├── scripts/validate.py                # Manifest and frontmatter validation (CI)
├── CHANGELOG.md                       # Release notes per plugin
└── plugins/<plugin-name>/             # One directory per plugin
    ├── .claude-plugin/plugin.json     # Claude Code plugin manifest
    ├── .cursor-plugin/plugin.json     # Cursor plugin manifest
    ├── README.md                      # Plugin purpose, install, and component inventory
    ├── skills/<skill-name>/           # Knowledge/workflow skills; user-only actions set disable-model-invocation: true
    │   ├── SKILL.md                   # Skill definition (YAML frontmatter + body)
    │   └── references/                # Optional supplementary content
    └── agents/<agent>.md              # Autonomous subagents (context-isolated, multi-file)
```

Current plugins: `openehr-specs` (skills, including user-only action skills, and subagents). `plugins/openehr-specs/README.md` is its inventory: update it, and the root `README.md`, whenever a component is added, removed, or renamed. `validate.py` checks neither.

## Key Conventions

- Plugin names: `openehr-<domain>` (mandatory prefix — flat global namespace); skill names: terse activity nouns with no prefix (auto-namespaced as `<plugin>:<skill>`). User-only action skills and subagents follow the same no-prefix rule (`spec-reviewer` is the one exception).
- Component choice follows the *nature of the work*: **skills** = knowledge/workflows (model- or user-invoked); **user-only action skills** (`publish`, `regen-classes`) = user-initiated actions, also in `skills/`, marked `disable-model-invocation: true` so their descriptions stay out of context and they don't compete with knowledge-skill triggering (Claude Code treats `commands/` as the older format, so new actions are skills); **subagents** (`agents/`) = context-heavy, multi-file, or adversarial work that would otherwise pollute the main context. Action skills and agents reference their sibling knowledge skill rather than duplicating it.
- Skill `description` frontmatter is lean (~50–75 words): one what+scope sentence → a few representative triggers → short "Not for …" anti-triggers routing to the right sibling/plugin.
- Keep each `SKILL.md` body a lean overview (quick-reference + pointers); push bulky detail (tables, templates, format specs) into `references/` so it loads only on demand.
- Versions must stay in sync across both plugin manifests (`.claude-plugin/` and `.cursor-plugin/`), both marketplace entries, and the release tag (`{name}--v{version}`).
- Pull requests do not bump versions: add changelog lines under `## Unreleased`, and a maintainer bumps at release. A push without a bump never reaches installed copies, because Claude Code compares versions.
- Never invent identifiers, paths, class names, or conventions — ground everything in published openEHR specifications. To verify, read the spec's Markdown twin: take any `specifications.openehr.org/...page.html` URL and swap `.html` → `.md`.
- Do not duplicate community tooling (e.g. CKM/clinical modeling is covered by Cadasto's plugins); this repo covers ground the Foundation owns.

Full details: [docs/skill-authoring.md](docs/skill-authoring.md)

## Development

Pure-content repository (JSON manifests + markdown skills) — no build step, package manager, or test suite.

- **Validation**: `python3 scripts/validate.py` (Claude + Cursor manifests, version sync, required skill/agent frontmatter fields, component paths — runs in CI; it does not check description length, inventories, or the release tag)
- **Local testing**: [docs/testing.md](docs/testing.md); **versioning/releases**: [docs/versioning.md](docs/versioning.md)
- **End-user installation**: [docs/install.md](docs/install.md)
- **Generating/editing AsciiDoc for `specifications-XX` repos**: follow [docs/spec-style-guide.md](docs/spec-style-guide.md); skill bodies must agree with it — when changing one, check the other.

## Component Dependencies

The skills are pure content; the subagents and the `publish` and `regen-classes` action skills rely on external tools and degrade
gracefully when one is absent (each says so in its prompt):

- **`spec-reviewer`, `xref-auditor`** — need a `specifications-XX` checkout and (for attribute resolution) the sibling `specifications-AA_GLOBAL`.
- **`xref-auditor`, `identifier-grounding`** — use **WebFetch** to read spec Markdown twins (`.html` → `.md`); `identifier-grounding` additionally prefers the **`openehr-assistant` MCP** (`type_specification_get`) when connected, falling back to the twin.
- **`regen-classes`** — needs **Docker** (`ghcr.io/openehr/bmm-publisher`).
- **`publish`** — needs a sibling `specifications-AA_GLOBAL` checkout; it runs `bin/spec_publish.sh`, falls back to the published `ghcr.io/openehr/asciidoctor` Docker image when `asciidoctor`, `jq`, or `bc` is missing, and stops when Docker is missing too. It checks that each HTML output was rebuilt, because the script reports success even when it built nothing.

None are bundled (the `openehr-assistant` MCP is interactively authenticated, not redistributable); document them, don't assume them.

## Relationship to Other Repos

- **`specifications-AA_GLOBAL`**: shared infrastructure (boilerplate, publishing scripts, styles) consumed by all spec repos
- **`specifications-XX`**: individual component repos (RM, AM, BASE, etc.) where specs live
- Changes to this repo never touch those repos. The plugins do edit them (for example the `authoring` and `amendment-record` skills), but only when a user runs them inside a checkout.

## Git

- Remote: `https://github.com/openEHR/ai-plugins`
- Main integration branch: `main`
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org): `type(scope): summary` (e.g. `feat(openehr-specs): add conformance skill`) — see [CONTRIBUTING.md](CONTRIBUTING.md)
