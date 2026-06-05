# Contributing

Thank you for helping improve the openEHR AI plugins. This repository is maintained by the openEHR Foundation; contributions are welcome from the whole community.

## Ways to Contribute

- **Report a skill bug** — a skill triggering wrongly, producing incorrect guidance, or contradicting the openEHR specifications: open a [skill bug issue](https://github.com/openEHR/ai-plugins/issues/new?template=skill-bug.md).
- **Propose a new skill or plugin** — open a [proposal issue](https://github.com/openEHR/ai-plugins/issues/new?template=proposal.md) **before** writing content. New plugins are a Foundation scope decision: they must cover ground the Foundation owns (specification authoring, conformance, ...) and must not duplicate existing community tooling.
- **Improve existing content** — fixes and refinements can go straight to a pull request.

## Development Setup

```bash
git clone https://github.com/openEHR/ai-plugins
```

Test your changes by installing the marketplace locally — see [docs/testing.md](docs/testing.md).

## Conventions

- Plugin/skill structure and naming: [docs/skill-authoring.md](docs/skill-authoring.md)
- AsciiDoc style for spec-related content: [docs/spec-style-guide.md](docs/spec-style-guide.md)
- Versioning and releases: [docs/versioning.md](docs/versioning.md)
- Ground everything in the published [openEHR specifications](https://specifications.openehr.org) — never invent class names, attributes, paths, or identifiers.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org): `type(scope): summary`

- **Types**: `feat` (new skill or capability), `fix` (incorrect skill content/behavior), `docs`, `chore`, `ci`
- **Scope**: the plugin or skill affected, e.g. `feat(spec-authoring): add conformance skill`, `fix(its-rest): correct build pipeline paths`

## Pull Request Process

1. Branch from `main`.
2. Run the validation script locally: `python3 scripts/validate.py`
3. If you changed plugin content, bump the plugin version per [docs/versioning.md](docs/versioning.md) and update [CHANGELOG.md](CHANGELOG.md).
4. Test skill triggering locally ([docs/testing.md](docs/testing.md)).
5. Open the PR and complete the checklist in the template. CI must pass.

By contributing, you agree that your contributions are licensed under the [Apache 2.0 License](LICENSE).

## Code of Conduct

All participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
