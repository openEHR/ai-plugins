---
name: governance
description: >
  Manage openEHR specification governance: releases, change requests (CR/PR), versioning, and
  lifecycle states (Planning, Development, Trial, Stable, Paused, Retired). This skill should be
  used when the user asks to create, tag, or fix a release, update release entries in
  `manifest.json`, raise or progress a CR/PR, promote a spec's status, propose a new spec, or
  explain the SEC change process. Not for amendment entries (amendment-record), pre-release
  document review (review), local previews (authoring), or clinical/archetype governance.
---

# openEHR Specification Governance

This skill covers the change process, release management, and lifecycle governance for
openEHR specifications. It is based on the official governance documents at
specifications.openehr.org/governance.

## Related Skills

- **authoring** — document scaffolding, repo layout, boilerplate structure
- **amendment-record** — detailed amendment record authoring conventions
- **review** — pre-release quality review of spec documents (the `spec-reviewer` and `xref-auditor` subagents run it across a whole spec or component)

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

The `spec_status` field in `manifest.json` and `manifest_vars.adoc` carries this state in upper case (for example `DEVELOPMENT`, `TRIAL`, `STABLE`, `PAUSED`, `RETIRED`; the full list is in `../authoring/references/manifest-spec-entry.md`). Keep both copies identical. To promote a spec, confirm that the SEC has approved the promotion, then set `spec_status` identically in both files.

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
- If the user is not an SEC member, direct them to raise a PR on the `SPECPR` tracker instead

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
- Fix releases: `Release-N.N.NvM` (e.g., `Release-1.0.4v1`) — for post-release corrections

### Steps to Create a Release

Read `references/release-checklist.md` for the full step-by-step checklist.

The high-level process:

1. **Jira** (a user task, not doable from the repo): ask the user to confirm that all CRs and PRs for the release are closed and the saved searches exist, then continue.
2. **manifest.json**: Set the release date, verify `spec_status` for each spec, ensure Jira links are correct, and prepend the next-cycle `releases` entry with an empty `date`.
3. **Git**: Create a release branch (`Release-N.N.N`), publish in release mode with the exact command in the checklist (do not use `/openehr-specs:publish`; it builds previews only), commit, and create the annotated tag. Ask the user before pushing.
4. **Webhook**: The push triggers the specifications.openehr.org server to pull and deploy.

### Steps to Fix a Release

Follow the Fix Release section of `references/release-checklist.md`.

## Creating a New Specification

New specifications are proposed via PR or CR. The SEC verifies:
- Identifier assignment (the `id` field)
- Structural placement within the specification library
- Scope consistency with existing specifications
- Component location

To scaffold the document and its `manifest.json` entry once identifier and placement are agreed,
follow the **authoring** skill ("Creating a New Specification Document").

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
