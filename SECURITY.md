# Security Policy

## Threat Model

This repository distributes **AI-assistant instruction content** (plugins and skills). The relevant security concerns are therefore content-integrity and supply-chain issues rather than classic software vulnerabilities:

- **Malicious or manipulative skill content** — instructions in a `SKILL.md` (or its `references/`) designed to make an AI assistant exfiltrate data, execute harmful commands, or act against the user's interest (prompt injection via skill content).
- **Manifest tampering** — a `plugin.json` or `marketplace.json` pointing at unexpected sources or misrepresenting plugin identity.
- **Typosquatting** — plugin or skill names crafted to impersonate official openEHR plugins.
- **Malicious external references** — skill content linking to harmful or impersonating external resources.

## Reporting a Vulnerability

Please **do not** open a public issue for security-sensitive reports.

- Use GitHub's private vulnerability reporting: **Security → Report a vulnerability** on this repository.
- Alternatively, contact the repository maintainers directly.

You can expect an acknowledgement within 7 days. Confirmed issues are fixed in a new plugin release and noted in the [CHANGELOG](CHANGELOG.md).

## Supported Versions

Only the **latest released version** of each plugin (latest `{name}--v{version}` tag) is supported. Users should keep plugins updated via their assistant's update mechanism (e.g. `/plugin update` in Claude Code).

## Out of Scope

- Vulnerabilities in Claude Code or other AI assistants themselves — report to the respective vendor (e.g. [Anthropic](https://www.anthropic.com/security)).
- Issues in the openEHR specifications — raise via the [openEHR Jira](https://openehr.atlassian.net/) (SPEC* projects).
