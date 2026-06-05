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
└── plugins/<plugin-name>/             # One directory per plugin
    ├── .claude-plugin/plugin.json     # Claude Code plugin manifest
    ├── .cursor-plugin/plugin.json     # Cursor plugin manifest
    ├── README.md                      # Plugin purpose, install, and skill inventory
    └── skills/<skill-name>/
        ├── SKILL.md                   # Skill definition (YAML frontmatter + body)
        └── references/                # Optional supplementary content
```

Current plugins: `openehr-specs` (spec authoring, review, governance, content patterns, amendment records, ITS-REST, BMM class generation).

## Key Conventions

- Plugin names: `openehr-<domain>` (mandatory prefix — flat global namespace); skill names: terse activity nouns with no prefix (auto-namespaced as `<plugin>:<skill>`).
- Skill `description` frontmatter is lean (~50–75 words): one what+scope sentence → a few representative triggers → short "Not for …" anti-triggers routing to the right sibling/plugin.
- Keep each `SKILL.md` body a lean overview (quick-reference + pointers); push bulky detail (tables, templates, format specs) into `references/` so it loads only on demand.
- Versions must stay in sync across both plugin manifests (`.claude-plugin/` and `.cursor-plugin/`), both marketplace entries, and the release tag (`{name}--v{version}`).
- Never invent identifiers, paths, class names, or conventions — ground everything in published openEHR specifications. To verify, read the spec's Markdown twin: take any `specifications.openehr.org/...page.html` URL and swap `.html` → `.md`.
- Do not duplicate community tooling (e.g. CKM/clinical modeling is covered by Cadasto's plugins); this repo covers ground the Foundation owns.

Full details: [docs/skill-authoring.md](docs/skill-authoring.md)

## Development

Pure-content repository (JSON manifests + markdown skills) — no build step, package manager, or test suite.

- **Validation**: `python3 scripts/validate.py` (Claude + Cursor manifests, version sync, skill frontmatter, component paths — runs in CI)
- **Local testing**: [docs/testing.md](docs/testing.md); **versioning/releases**: [docs/versioning.md](docs/versioning.md)
- **End-user installation**: [docs/install.md](docs/install.md)
- **Generating/editing AsciiDoc for `specifications-XX` repos**: follow [docs/spec-style-guide.md](docs/spec-style-guide.md); skill bodies must agree with it — when changing one, check the other.

## Relationship to Other Repos

- **`specifications-AA_GLOBAL`**: shared infrastructure (boilerplate, publishing scripts, styles) consumed by all spec repos
- **`specifications-XX`**: individual component repos (RM, AM, BASE, etc.) where specs live
- Plugins in this repo help authors work in those repos but do not modify them directly

## Git

- Remote: `https://github.com/openEHR/ai-plugins`
- Main integration branch: `main`
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org): `type(scope): summary` (e.g. `feat(spec-authoring): add conformance skill`) — see [CONTRIBUTING.md](CONTRIBUTING.md)
