# ai-plugins

[![validate](https://github.com/openEHR/ai-plugins/actions/workflows/validate.yml/badge.svg)](https://github.com/openEHR/ai-plugins/actions/workflows/validate.yml)
[![license](https://img.shields.io/github/license/openEHR/ai-plugins)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-marketplace-d97757)](https://code.claude.com/docs/en/plugins)
[![Cursor](https://img.shields.io/badge/Cursor-marketplace-111111)](https://cursor.com/docs/plugins)

AI-assistant plugins for openEHR — the official plugin marketplace of the [openEHR Foundation](https://openehr.org).

This repository provides AI-assisted tooling for people working on openEHR specifications — packaged as a [Claude Code](https://code.claude.com/docs/en/plugins) and [Cursor](https://cursor.com/docs/plugins) plugin marketplace. The skill content (`SKILL.md`, an open cross-tool format) is the canonical artifact; each assistant uses thin manifests (`.claude-plugin/` and `.cursor-plugin/`) around the same skills.

It is **not** a specification repository: the specifications live in the `specifications-XX` repos, and these plugins help the people who author them.

## Plugins

| Plugin | Purpose |
|--------|---------|
| `openehr-specs` | Creating, editing, and reviewing openEHR specification documents (AsciiDoc and OpenAPI/ITS-REST), specification governance, content quality and convention compliance |

## Quick Install

**Claude Code**, inside a session:

```text
/plugin marketplace add openEHR/ai-plugins
/plugin install openehr-specs@openehr
```

**Cursor** (Teams and Enterprise plans): import `https://github.com/openEHR/ai-plugins` as a team marketplace, then install `openehr-specs`.

See [docs/install.md](docs/install.md) for the Cursor steps, updates, and inspection.

## Usage

In Claude Code, skills are namespaced by the plugin and invoked as `/openehr-specs:<skill>`:

```text
/openehr-specs:authoring    # scaffold or edit a spec document
/openehr-specs:review       # pre-release quality review
/openehr-specs:governance   # release process and change requests
```

Type `/openehr` in the slash menu to list the available skills, or describe the task (for example, "review this openEHR spec before release") and Claude loads the matching skill when the request fits its description.

The plugin also ships **subagents** (`spec-reviewer`, `xref-auditor`, `identifier-grounding`) that Claude dispatches for heavy, multi-file, or verification work, and three **user-only action skills** (`/openehr-specs:regen-classes`, `/openehr-specs:publish`, `/openehr-specs:scaffold`) that run only when you type them. The [plugin README](plugins/openehr-specs/README.md) has the full inventory and invocation details.

## Documentation

- [docs/install.md](docs/install.md): installing, updating, and inspecting plugins
- [docs/testing.md](docs/testing.md): local testing and validation (contributors)
- [docs/skill-authoring.md](docs/skill-authoring.md): plugin and skill authoring conventions
- [docs/spec-style-guide.md](docs/spec-style-guide.md): style guide for openEHR specification documents
- [docs/versioning.md](docs/versioning.md): versioning and release process

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md); security concerns are handled per [SECURITY.md](SECURITY.md).

## License

[Apache 2.0](LICENSE)
