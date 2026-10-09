# Rewriting README.adoc as README.md

For step 5 of the `scaffold` skill. Rewrite the AsciiDoc README as GitHub-flavoured Markdown after
`git mv README.adoc README.md`. The rewrite changes the markup only: keep every sentence, link,
listing and table, in the same order, and add nothing. When `README.md` already exists, merge the
AsciiDoc file's sections into it and remove what duplicates, without dropping content.

| AsciiDoc | Markdown |
|----------|----------|
| `= Title`, `== Section`, `=== Subsection` | `# Title`, `## Section`, `### Subsection` (one `#` per `=`) |
| `https://host/path[text]`, `link:https://host/path[text]` | `[text](https://host/path)` |
| `link:docs/x.adoc[text]`, `xref:x.adoc[text]` | `[text](docs/x.adoc)`, keeping the path relative to the repo root |
| `<<anchor,text>>` | `[text](#anchor)`, with the anchor as GitHub derives it from the heading |
| A bare URL | Unchanged (GitHub links it) |
| `*bold*`, `_italic_`, `` `code` `` | `**bold**`, `_italic_`, `` `code` `` |
| `* item`, `** nested` | `- item`, `  - nested` (two spaces per level) |
| `. step` | `1. step` |
| `----` … `----` listing, ```` ``` ```` … ```` ``` ```` | A fenced block (```` ``` ````) with the same lines |
| `[source,bash]` before a listing | The language on the fence: ```` ```bash ```` |
| `NOTE: text` (also `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`) | `> [!NOTE]` on one line, then `> text` |
| `\|===` table, `\|a \|b` rows | A pipe table, with the first row as the header row |
| `image::path[alt]` | `![alt](path)` |
| `:name: value` attributes, `{name}` uses | The value written in place of each use; the attribute lines are dropped |
| `include::file[]` | A link to the file, unless it is short enough to inline |
| `// comment` | `<!-- comment -->` |

A construct without a Markdown form keeps its text as plain prose. Tell the user which lines it
affected.

Before showing the diff, check:

- Every heading, link target and code line is still there (`git diff -M README.md` shows the rename).
- Links that pointed at `.adoc` files in the repo still resolve. The published HTML lives at
  `https://specifications.openehr.org/releases/<COMPONENT>/`, not in the repository.
- Box-drawing directory trees inside listings keep their alignment. They stay in a fenced block.
- Other files in the repo that name `README.adoc` (`AGENTS.md`, `docs/`) now name `README.md`: search
  the repo for the old name.

Why Markdown: the standard file set's target is `README.md`. GitHub renders both formats, and none of
the publishing tooling in `specifications-AA_GLOBAL` reads a component's `README.adoc`.
