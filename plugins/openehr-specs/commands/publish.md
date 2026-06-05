---
name: publish
description: Build a local HTML preview of an openEHR specification component via the AA_GLOBAL publisher
argument-hint: "<component, e.g. RM> [spec-id]"
allowed-tools: ["Bash", "Read", "Glob"]
disable-model-invocation: true
---

Produce a local HTML preview of an openEHR specification component using the shared publishing
toolchain in `specifications-AA_GLOBAL`. This is the publish step described in the
`openehr-specs:authoring` skill — this command is the action wrapper. It builds a **local preview
only**; it does not tag, commit, or deploy a release (that is the `governance` skill / release process).

Arguments: `$ARGUMENTS` — the component abbreviation (e.g. `RM`, `BASE`, `AM`) and optionally a
single spec id to limit the build.

Do the following:

1. **Locate the publisher.** Confirm a sibling `specifications-AA_GLOBAL` checkout exists next to
   the component repo (the parent directory should contain both `specifications-AA_GLOBAL/` and
   `specifications-<component>/`). If not, report what is missing and stop.
2. **Run from the parent directory** containing the `specifications-*` repos. Prefer the script,
   fall back to Docker:
   ```bash
   ./specifications-AA_GLOBAL/bin/spec_publish.sh -f -v $ARGUMENTS
   # or:
   docker run -u $(id -u):$(id -g) -v "$(pwd):/documents/" openehr/asciidoctor development $ARGUMENTS
   ```
3. **Surface the result** — report the generated HTML output location and any Asciidoctor
   warnings/errors (unresolved attributes, missing includes, missing images) verbatim, since those
   are exactly what a pre-publish check should catch.
4. If the build fails, summarise the first actionable error and suggest the relevant skill
   (`authoring` for include/attribute issues, `xref-auditor` agent for cross-reference failures).

Do not pass release flags (`-r -t -q -l Release-N.N.N`) — releasing is a governed process; use the
`governance` skill for that.
