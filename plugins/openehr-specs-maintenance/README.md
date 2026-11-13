# openEHR Specifications Maintenance

Skills for the people who maintain the openEHR specifications as a body of work, such as the Specifications Editorial Committee (SEC): housekeeping across the `specifications-XX` repositories and the SPEC* Jira projects. For writing and reviewing the specifications themselves, use the [`openehr-specs`](../openehr-specs/README.md) plugin.

## Installation

### Claude Code

From the [ai-plugins](https://github.com/openEHR/ai-plugins) marketplace:

```text
/plugin marketplace add openEHR/ai-plugins
/plugin install openehr-specs-maintenance@openehr
```

### Cursor

Add the marketplace from this repository (or a fork), then install `openehr-specs-maintenance`. See [docs/install.md](../../docs/install.md) for details.

## Skills

| Skill | Purpose |
|-------|---------|
| `sec-waiting` | Read-only reminder list for the SEC: per member, the pull request reviews requested from them and the Jira questions put to them that are still open, as a message ready to paste into Discourse (needs `python3` and a logged-in `gh`) |
| `sec-agenda` | Draft the Confluence page for the next SEC call from the standard template and carry over what the previous call left open: topics not reached, follow-ups and unchecked action items (needs the Atlassian MCP) |

## Usage

Invoke the skill as `/openehr-specs-maintenance:sec-waiting`, or ask for it ("what are we waiting on", "who owes a review"). It only reads GitHub and Jira and prints a list; it never comments, pings or posts.

Invoke `/openehr-specs-maintenance:sec-agenda <date>`, or ask for it ("draft the next SEC agenda"). It shows the draft first and creates or changes a Confluence page only when you confirm.

`sec-waiting` ships without personal data. The names it needs to ping people on Discourse, and any pinned tickets, go in a personal settings file outside this repository; see "Configuration" in the [skill](skills/sec-waiting/SKILL.md).

## Dependencies

- **`python3`** (3.8+, standard library only) runs the bundled `scripts/sec_waiting.py`.
- **`gh`** (GitHub CLI), logged in with an account that can read the `openEHR/sec` team.
- Jira is read through the public REST API without a login; restricted tickets are not seen.
- The **Atlassian MCP**: `sec-agenda` needs it, with write access to the Specifications space; without it the skill hands over the draft as text. For `sec-waiting` it is optional, used only to check pinned tickets of non-public projects.
