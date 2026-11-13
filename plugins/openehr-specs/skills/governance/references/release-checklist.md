# Release Checklist

Step-by-step checklist for releasing an openEHR specification component (e.g., RM Release-1.0.4).

## Pre-Release

- [ ] All CRs allocated to this release are Resolved in Jira (resolution Fixed, Fix Version set); they are Closed only after the release
- [ ] All PRs addressed by this release are Resolved in Jira; they are Closed only after the release
- [ ] Create Jira saved searches (filters) for:
  - PRs fixed: `<jira-home>/projects/SPECPR/versions/NNNNN`
  - CRs done: `<jira-home>/projects/SPEC<COMPONENT>/versions/NNNNN`
- [ ] All specification text changes are committed
- [ ] All amendment records are updated with CR/PR references (amendment-record skill; the user can run `/openehr-specs:amendment-record`)
- [ ] All diagrams are up to date (generated ones via the class-generation skill; the user can run `/openehr-specs:regen-classes`)
- [ ] Run the `spec-reviewer` and `xref-auditor` subagents on each specification in the component; resolve all ERRORs, undefined attributes, and broken anchors

## Ballot (minor and major releases only)

- [ ] Post the ballot on the Discourse specifications forum from `ballot-post.md`: every ticket of the release linked, the development build, what changed, the closing date 30 days out
- [ ] Answer every comment in the thread; changes from the ballot take their normal path and keep the Fix Version
- [ ] Continue only after the closing date

## manifest.json Updates

- [ ] For each specification in the component:
  - [ ] Verify `spec_status` is correct (e.g., TRIAL → STABLE promotion if applicable)
- [ ] In the `releases` array:
  - [ ] Set the `date` field on the release being published (format: `YYYY-MM-DD`)
  - [ ] Verify `jira.crs` and `jira.prs` version IDs are correct
  - [ ] Prepend a new entry for the next development cycle (empty `date` = not yet released)

## Git Operations

- [ ] Ensure all changes are committed on `master`
- [ ] Create a new branch: `git checkout -b Release-N.N.N`
- [ ] Run the publisher in release mode (run git commands inside `specifications-XX` and the publisher from the parent directory; do not use `/openehr-specs:publish` here, it builds previews only):
  ```bash
  # From the parent directory:
  ./specifications-AA_GLOBAL/bin/spec_publish.sh -f -r -v -t -q -l Release-N.N.N XX
  # Or via Docker:
  docker run -u $(id -u):$(id -g) -v "$(pwd):/documents/" ghcr.io/openehr/asciidoctor Release-N.N.N XX
  ```
- [ ] Verify the published HTML output:
  - [ ] Front page shows correct release label and date
  - [ ] Preface page renders correctly
  - [ ] Cross-references resolve
  - [ ] Diagrams render
- [ ] Commit all generated output
- [ ] Create an annotated tag:
  ```bash
  git tag -a Release-N.N.N -m "XX Release N.N.N"
  ```
- [ ] Push branch and tag:
  ```bash
  git push -u origin Release-N.N.N
  git push origin Release-N.N.N  # the tag
  ```

## Post-Release

- [ ] Verify deployment at `https://specifications.openehr.org/releases/XX/Release-N.N.N/`
- [ ] Close the Resolved CRs and PRs with this Fix Version in Jira (Resolve → release → Close, see the governance skill)
- [ ] Switch back to `master`: `git checkout master`
- [ ] Post the release notes as the last reply in the ballot thread (patch release: a short post on the Discourse specifications forum)

## Fix Release (Post-Release Corrections)

If a significant error is discovered after release:

- [ ] Check out the release branch: `git checkout Release-N.N.N`
- [ ] Make corrections to source files
- [ ] Republish from the parent directory: `./specifications-AA_GLOBAL/bin/spec_publish.sh -f -r -v -t -q -l Release-N.N.N XX`
- [ ] Commit
- [ ] Add a new annotated tag: `Release-N.N.NvM` (M = previous fix number + 1)
  ```bash
  git tag -a Release-N.N.NvM -m "XX Release N.N.N fix M"
  ```
- [ ] Push commits and tag (the webhook overwrites the deployed release, so confirm with the user first)
- [ ] Merge fixes back to `master`:
  ```bash
  git checkout master
  git merge Release-N.N.N
  ```
