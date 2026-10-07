---
name: publish
description: Build a local HTML preview of an openEHR specification component via the AA_GLOBAL publisher
argument-hint: "<component, e.g. RM>"
allowed-tools:
  - "Bash(./specifications-AA_GLOBAL/bin/spec_publish.sh *)"
  - "Bash(docker run * ghcr.io/openehr/asciidoctor *)"
  - Read
  - Glob
disable-model-invocation: true
---

Build a local HTML preview of the component named in `$ARGUMENTS` (for example `RM`, `BASE` or `AM`)
with the publisher in `specifications-AA_GLOBAL`. The publisher builds a whole component, not a single
spec. This is the preview step of the `openehr-specs:authoring` skill. It never tags, commits, or
deploys a release; that is the `governance` skill.

If `$ARGUMENTS` is empty, ask which component and stop: without one, the script rebuilds every sibling
`specifications-*` repo.

The script prints `generated <file>` and exits 0 even when `asciidoctor` is missing or failed. Confirm
the outputs (steps 2 and 4) instead of trusting that line.

1. Work from the parent directory that holds the sibling `specifications-AA_GLOBAL/` and
   `specifications-<component>/` checkouts. If either is missing, say which and stop. Run
   `which asciidoctor jq bc`: the script needs all three. If one is missing, name it and use the Docker
   fallback in step 3; if `which docker` finds nothing either, report both and stop.
2. Snapshot the outputs: `stat -c '%Y %n' specifications-<component>/docs/*.html` (ignore "No such
   file"; use `ls -l` where `stat -c` is unavailable).
3. Build:
   ```bash
   ./specifications-AA_GLOBAL/bin/spec_publish.sh -f -v $ARGUMENTS
   # fallback when a tool is missing:
   docker run -u $(id -u):$(id -g) -v "$(pwd):/documents/" ghcr.io/openehr/asciidoctor development $ARGUMENTS
   ```
4. Verify. Glob `specifications-<component>/docs/*/master.adoc`: each needs a rebuilt
   `docs/<dir>.html` beside it, plus `docs/index.html` when `docs/index.adoc` exists. Repeat the `stat`
   command. A file that is missing, or whose time did not change, was not built: list each as
   `NOT BUILT` and report the build as failed.
5. Report where the HTML landed and every Asciidoctor warning or error verbatim (unresolved
   attributes, missing includes, missing images). On failure, summarise the first actionable error and
   point to `authoring` (includes, attributes) or the `xref-auditor` subagent (cross-references).

Never pass a release label (`-l Release-N.N.N`); releasing belongs to `governance`.
