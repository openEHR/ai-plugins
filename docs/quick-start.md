# Quick start

Install the `openehr-specs` plugin and use it on a real specification repository. You review a chapter, fact-check the class names in another, add an amendment record entry, and build the HTML preview. Every change is an uncommitted edit on a throwaway branch, and the last step discards it.

The steps use Claude Code and its slash commands. To install in Cursor, follow [install.md](install.md).

## Before you start

- Claude Code, signed in.
- `git`.
- Docker, for step 6 only. Steps 1 to 5 do not need it.
- Network access to GitHub. Step 4 also reads the published specifications.

Claude Code asks permission before some actions, such as editing a file or running a command it has not been given a standing approval for; allow the ones the steps describe. Claude's wording differs between runs, so each step says what to look for.

## 1. Clone two repositories side by side

The example spec is `specifications-BASE`. `specifications-AA_GLOBAL` holds the boilerplate and reference definitions that the preview build and some review checks read, so it must sit next to it.

```bash
mkdir openehr && cd openehr
git clone https://github.com/openEHR/specifications-AA_GLOBAL.git
git clone https://github.com/openEHR/specifications-BASE.git
git -C specifications-BASE switch -c try/quick-start
```

The last command puts BASE on a throwaway branch.

## 2. Install the plugin

Start Claude Code in the `openehr` directory:

```bash
claude
```

Install the plugin from the openEHR marketplace:

```text
/plugin marketplace add openEHR/ai-plugins
/plugin install openehr-specs@openehr
```

Exit and start `claude` again from the same directory, because a newly installed plugin loads in the next session. Type `/openehr` and the slash menu lists the plugin's skills.

## 3. Review a chapter

Send this prompt:

```text
Review specifications-BASE/docs/base_types/master02-overview.adoc with the openehr-specs review checks. Report findings only, do not edit.
```

Claude applies the `review` skill and answers with a table of findings (ID, severity, location, finding) and a total line. For a single file it also lists the checks it did not run, because they need other files. When no check fails, it says so. Nothing is edited.

## 4. Fact-check class names

Send this prompt:

```text
Fact-check the class and attribute names in specifications-BASE/docs/base_types/master05-identification_package.adoc against the published openEHR specifications.
```

Claude dispatches the `identifier-grounding` subagent. It returns one row per identifier with a status: `VERIFIED`, `UNVERIFIED`, `LIKELY INVENTED`, `NEW` or `SKIPPED`. It may ask permission to fetch pages from `specifications.openehr.org`; allow it.

## 5. Add an amendment record entry

Send this prompt:

```text
/openehr-specs:amendment-record SPECBASE-999 - fix a typo in the base_types overview chapter (an exercise: the key is made up)
```

For real work, give the key of the Jira ticket.

Claude asks for the raiser name; answer with your own. It adds a new top entry to `specifications-BASE/docs/base_types/master00-amendment_record.adoc`, bumps the patch number because a typo fix is a patch change, and moves the `[[latest_issue]]` and `[[latest_issue_date]]` anchors to the new entry. Then it shows the diff and stops. It does not commit. Claude Code may ask you to approve the `git` commands it uses to read the diff; allow them.

## 6. Build the HTML preview

Make sure Docker is running, then send:

```text
/openehr-specs:publish BASE
```

The first run pulls the `ghcr.io/openehr/asciidoctor` image. The build prints `generated` and exits successfully even when it failed, so Claude compares the modification time of each `docs/*.html` file before and after, and scans the log for `ERROR` and `include file not found`. It reports where the HTML landed, or `NOT BUILT` for any file that did not change, with the errors verbatim. It may ask permission for the `stat` commands it uses.

The build rewrites the four tracked `docs/*.html` files of BASE. Do not stage them.

## 7. Discard the exercise

Exit Claude Code, then run:

```bash
git -C specifications-BASE restore .
git -C specifications-BASE switch -
git -C specifications-BASE branch -D try/quick-start
git -C specifications-BASE status --short
```

The first command discards the edits from steps 5 and 6, and the last prints nothing.

## Next

- [Prompting guide](prompting-guide.md): which prompt to use for each authoring situation.
- [Plugin README](../plugins/openehr-specs/README.md): every skill and subagent.
