---
name: publish
description: Build a local HTML preview of an openEHR specification component via the AA_GLOBAL publisher
argument-hint: "<component, e.g. RM>"
allowed-tools: ["Bash", "Read", "Glob"]
disable-model-invocation: true
---

Build a local HTML preview of the component named in `$ARGUMENTS` (for example `RM`, `BASE` or `AM`)
with the publisher in `specifications-AA_GLOBAL`. The publisher builds a whole component, not a single
spec. This is the preview step of the `openehr-specs:authoring` skill. It never tags, commits, or
deploys a release; that is the `governance` skill.

If `$ARGUMENTS` is empty, ask which component and stop: without one, the script rebuilds every sibling
`specifications-*` repo.

1. Run from the parent directory that holds the sibling `specifications-AA_GLOBAL/` and
   `specifications-<component>/` checkouts. If either is missing, say which and stop.
   ```bash
   ./specifications-AA_GLOBAL/bin/spec_publish.sh -f -v $ARGUMENTS
   # fallback when the script cannot run:
   docker run -u $(id -u):$(id -g) -v "$(pwd):/documents/" openehr/asciidoctor development $ARGUMENTS
   ```
2. Report where the HTML landed and every Asciidoctor warning or error verbatim (unresolved
   attributes, missing includes, missing images). On failure, summarise the first actionable error and
   point to `authoring` (includes, attributes) or the `xref-auditor` subagent (cross-references).

Never pass a release label (`-l Release-N.N.N`); releasing belongs to `governance`.
