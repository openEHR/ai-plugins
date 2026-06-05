---
name: amend
description: Add an amendment-record entry to the current openEHR spec (version bump + Jira refs + anchor move)
argument-hint: "<SPECXX-NN[,SPECPR-NN] — one-line summary of the change>"
allowed-tools: ["Read", "Edit", "Bash"]
disable-model-invocation: true
---

Add a new entry to the amendment record of the openEHR specification being worked on. The
amendment-record conventions (anchors, Jira keys, release boundaries, version-bump rules) are
defined in the `openehr-specs:amendment-record` skill and its `references/conventions.md` — follow
them; this command is the action wrapper.

Arguments: `$ARGUMENTS` — the Jira CR/PR reference(s) and a short description of the change
(e.g. `SPECRM-142 — add tags to LOCATABLE; addresses SPECPR-401`).

Do the following:

1. **Locate the amendment record.** Find the relevant `master00-amendment_record.adoc`. If the
   spec directory is ambiguous, ask which spec; if a single spec is in scope, use it.
2. **Read it** to learn the current top issue number, format (`[cols=...]`), and raiser style.
3. **Classify the version bump** from the change description (patch = corrections/clarifications,
   minor = new content/sections, major = restructuring) per the amendment-record skill's rubric.
   If unclear, state your assumption and proceed.
4. **Optionally inspect the diff** for context: `git -C <repo> diff` (and `git status`) to see what
   actually changed, so the entry describes it accurately.
5. **Insert the new entry at the top** of the table (immediately after the header row):
   - Move the `[[latest_issue]]` and `[[latest_issue_date]]` anchors onto this new entry.
   - Format Jira references as `{spec_tickets}/SPECXX-NN[SPECXX-NN^]: <description>`; link any PRs
     it addresses ("Addresses {spec_tickets}/SPECPR-NN[SPECPR-NN^]").
   - Use today's date in `dd Mon yyyy` form (ask if the date is uncertain — do not guess a date).
   - If this is the first entry after a release, add the `4+^h|*XX Release N.N.N*` boundary row below it.
6. **Show the diff of the change** and stop. Do not publish or commit.

Keep the Details cell concise and specific — state what changed, not why (the Jira ticket holds the rationale).
