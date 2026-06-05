# Release Checklist

Step-by-step checklist for releasing an openEHR specification component (e.g., RM Release-1.0.4).

## Pre-Release

- [ ] All CRs allocated to this release are completed and resolved in Jira
- [ ] All PRs addressed by this release are resolved and closed in Jira
- [ ] Create Jira saved searches (filters) for:
  - PRs fixed: `<jira-home>/projects/SPECPR/versions/NNNNN`
  - CRs done: `<jira-home>/projects/SPEC<COMPONENT>/versions/NNNNN`
- [ ] All specification text changes are committed
- [ ] All amendment records are updated with CR/PR references
- [ ] All diagrams are up to date

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
- [ ] Run the publisher in release mode:
  ```bash
  # From the parent directory:
  ./specifications-AA_GLOBAL/bin/spec_publish.sh -f -r -v -t -q -l Release-N.N.N XX
  # Or via Docker:
  docker run -u $(id -u):$(id -g) -v "$(pwd):/documents/" openehr/asciidoctor Release-N.N.N XX
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
- [ ] Switch back to `master`: `git checkout master`
- [ ] Announce on Discourse specifications forum if appropriate

## Fix Release (Post-Release Corrections)

If a significant error is discovered after release:

- [ ] Check out the release branch: `git checkout Release-N.N.N`
- [ ] Make corrections to source files
- [ ] Republish: `./spec_publish.sh -f -r -v -t -q -l Release-N.N.N XX`
- [ ] Commit
- [ ] Add a new annotated tag: `Release-N.N.NvM` (M = previous fix number + 1)
  ```bash
  git tag -a Release-N.N.NvM -m "XX Release N.N.N fix M"
  ```
- [ ] Push commits and tag
- [ ] Merge fixes back to `master`:
  ```bash
  git checkout master
  git merge Release-N.N.N
  ```
