---
name: governance
description: >
  Manage the openEHR specification governance lifecycle — releases, change requests (CR/PR), and
  lifecycle states (DEVELOPMENT/TRIAL/STABLE…). This skill should be used when the user asks to
  create or tag a release, prepare a release branch, update the manifest for a release, submit or
  manage a CR/PR, promote a spec's status, or discuss the openEHR change process or Jira workflow.
  Not for clinical/archetype governance, amendment-record authoring (use amendment-record), or
  non-openEHR release management.
---

# openEHR Specification Governance

This skill covers the change process, release management, and lifecycle governance for
openEHR specifications. It is based on the official governance documents at
specifications.openehr.org/governance.

## Related Skills

- **authoring** — document scaffolding, repo layout, boilerplate structure
- **amendment-record** — detailed amendment record authoring conventions
- **review** — pre-release quality review of spec documents

## Specification Lifecycle States

Every specification follows a formal lifecycle:

```
Planning → Development → Trial → Stable
                                    ↓
                                  Paused → Retired
```

| State | Duration | Format | Versioning | Change Management |
|-------|----------|--------|------------|-------------------|
| **Planning** | 6 months max | Wiki | 0.y.z | Informal |
| **Development** | 18 months max | Wiki | 0.y.z | Optional CRs |
| **Trial** | 2 years max | HTML + computable | x.y.z | Formal CRs |
| **Stable** | Unbounded | HTML + computable | x.y.z | Formal CRs |
| **Paused** | Unbounded | HTML + computable | paused | CRs only for state changes |
| **Retired** | Unbounded | Frozen version | n/a | None |

The Specifications Editorial Committee (SEC) reviews promotion criteria three months before
target dates. Unmet criteria may trigger a single three-month extension; subsequent failure
results in retirement.

The `spec_status` field in `manifest.json` and `manifest_vars.adoc` tracks this state.

## Versioning

openEHR uses three-part semantic versioning (`x.y.z`):

- **Patch (z)**: Error corrections and minor additions that do not change semantics
- **Minor (y)**: Significant additions that do not change existing semantics
- **Major (x)**: Semantic changes requiring potential software upgrades or data migration

Documentation-only corrections (typos, clarifications) receive a revision number update
without triggering a new release number.

## Artifact Types

### Problem Reports (PRs)

- Raised by **anyone** on the public `SPECPR` Jira tracker
- Document issues, bugs, or requirements against existing specifications
- The SEC reviews PRs every three months
- Reference format in specs: `{spec_tickets}/SPECPR-NNN[SPECPR-NNN^]`

### Change Requests (CRs)

- Created **only by SEC members** on component-specific Jira trackers (e.g., `SPECRM`, `SPECAM`)
- Each CR documents a specific modification to one or more specifications
- CRs reference the PRs they address
- Reference format in specs: `{spec_tickets}/SPECRM-NNN[SPECRM-NNN^]`

## Change Request Lifecycle

### 1. Creation
A CR requires: title, description, problem statement or PR references, affected component(s).

### 2. Acceptance
The SEC determines if the CR addresses real needs. Accepted CRs receive:
- Completion target date
- Work estimate (days)
- Assigned **Change Owner** (the component maintainer or designee)
- Priority: minor, major, or critical

### 3. Work Execution

**Minor changes** (single-document, no semantic impact):
- Edit directly on the working branch
- Generate publication formats for review

**Major changes** (cross-cutting or semantic):
- Create a development branch
- Track progress on a dedicated wiki page
- 30-day open community review period required before approval

### 4. Approval

**Minor changes:**
- Component Maintainer reviews
- Pass → commit to specification library
- Fail → one week to revise (max 3 rounds, then rejected)

**Major changes:**
- 30-day community review on Discourse specifications forum
- Assignee revises within two weeks based on feedback
- Two-thirds SEC majority vote required
- Max 3 review rounds, then rejected

### 5. Community Requirement

From Release 1.0 onward, specification changes (excluding documentation-only text updates)
must be announced on the Discourse specifications forum, and require implementation in at
least one formal software, schema, or technical expression before adoption.

## Release Process

Releases organize changes by component. The SEC defines release identifiers and delivery
dates, allocating CRs to releases.

### Release Naming

- Releases: `Release-N.N.N` (e.g., `Release-1.0.4`)
- Fix releases: `Release-N.N.NvN` (e.g., `Release-1.0.4v1`) — for post-release corrections

### Steps to Create a Release

Read `references/release-checklist.md` for the full step-by-step checklist.

The high-level process:

1. **Jira**: Close all CRs and PRs for this release. Create saved searches for the release versions.
2. **manifest.json**: Set the release date, verify `spec_status` for each spec, ensure Jira links are correct.
3. **Git**: Create a release branch (`Release-N.N.N`), publish with `-l Release-N.N.N`, commit, tag (annotated), push.
4. **Webhook**: The push triggers the specifications.openehr.org server to pull and deploy.

### Steps to Fix a Release

1. Check out the release branch
2. Make corrections to source files
3. Republish with the original release label
4. Commit and add a new annotated tag: `Release-N.N.NvN+1`
5. Push (webhook overwrites the deployed release)
6. Merge fixes back into `master`

## Creating a New Specification

New specifications are proposed via PR or CR. The SEC verifies:
- Identifier assignment (the `id` field)
- Structural placement within the specification library
- Scope consistency with existing specifications
- Component location

### Required Structure

All specifications must include:
- Front matter: identifier, version, amendments, copyright
- Introduction: purpose, related documents, status, tools, change history
- Main content
- References
- Internationalization considerations (where relevant)

### Entry Paths

1. **Mature external offering**: SEC assesses maturity; may start at Trial or Stable
2. **New development**: Starts at Planning state with 0.y.z versioning

## Roles

| Role | Responsibility |
|------|---------------|
| **SEC** (Specifications Editorial Committee) | Reviews all changes, accepts/rejects CRs, manages release allocation, promotes specs |
| **Component Maintainer** | Supervises component specs, assigns Change Owners, approves minor changes |
| **Change Owner** | Develops impact assessments, executes work, revises based on feedback |
| **Community** | Raises PRs, participates in open reviews on Discourse |
