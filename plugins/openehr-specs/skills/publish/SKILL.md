---
name: publish
description: Build a local HTML preview of an openEHR specification component with the published AA_GLOBAL publishing image
argument-hint: "<component, e.g. RM>"
allowed-tools:
  - "Bash(docker run * ghcr.io/openehr/asciidoctor *)"
  - Read
  - Glob
disable-model-invocation: true
---

Build a local HTML preview of the component named in `$ARGUMENTS` (for example `RM`, `BASE` or `AM`)
with the published `ghcr.io/openehr/asciidoctor` image. This is the preview step of the
`openehr-specs:authoring` skill: it builds a whole component as the `development` release and never
tags, commits, or deploys (that is `governance`). If `$ARGUMENTS` is empty, ask which component and
stop: the image takes exactly one.

1. Work from the parent directory that holds the sibling `specifications-AA_GLOBAL/` (the image reads
   the boilerplate and references from it) and `specifications-<component>/` checkouts. If either is
   missing, say which and stop. If `which docker` finds nothing, say Docker is required and stop.
2. Snapshot the outputs: `stat -c '%Y %n' specifications-<component>/docs/*.html` (ignore "No such
   file"; use `ls -l` where `stat -c` is unavailable).
3. Build. The entrypoint is `spec_publish.sh -f -r -v -t -q -l`, so the first argument is the release:
   ```bash
   docker run --rm -u $(id -u):$(id -g) -v "$(pwd):/documents/" ghcr.io/openehr/asciidoctor development $ARGUMENTS
   ```
4. Verify, because the build prints `generated <file>` and exits 0 even when includes are missing or
   `asciidoctor` failed. Glob `specifications-<component>/docs/*/master.adoc`: each needs a rebuilt
   `docs/<dir>.html` beside it, plus `docs/index.html` when `docs/index.adoc` exists. Repeat the `stat`
   command; a file that is missing or unchanged is `NOT BUILT`. Any `ERROR` or `include file not found`
   log line (for example `{pkg}…` class tables) also fails the build. An `INFO` line, such as a possible
   invalid bibliography reference, does not.
5. Report where the HTML landed and every error or warning verbatim. On failure, summarise the first
   actionable error and point to `authoring` (includes, attributes) or the `xref-auditor` subagent
   (cross-references). The build rewrites the tracked `docs/*.html` artefacts: tell the user, and do not
   stage them.
