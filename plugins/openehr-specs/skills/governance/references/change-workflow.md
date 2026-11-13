# Change workflow (SEC trial from 2026-11-09)

The Specifications Editorial Committee (SEC) approved this workflow on 2026-11-09 as a one-month
trial, until 2026-12-09. It replaces the Change Request lifecycle described on the published
[Change Process](https://specifications.openehr.org/governance/change_process) page for
specifications in Trial and Stable. The specification lifecycle and its promotion rules are not
touched. The proposal pages are on Confluence under *Spec workflow* (Specifications space,
login needed): Proposal summary, Change Process (draft revision), SEC Terms of Reference (draft
amendment).

In this file "PR" means a GitHub pull request, and "Problem Report" is written out.

## Three levels

Every change is a Fix, a Minor change, or a Change Request. Small changes are decided by
approvals on the pull request; only Change Requests go to an SEC vote.

| | Fix | Minor change | Change Request |
|---|---|---|---|
| What | A correction, or a new entry in a list meant to grow | Expectations change, but everything that conforms today still conforms | New in kind, or breaking |
| Example | Typo, schema bug, inconsistency, missing unit or term | A class changed in the BMM, a cardinality relaxed in a class table | New ADL logic, FHIR value set adoption, removed attribute |
| Ticket | Problem Report, optional | Problem Report | Change Request |
| Decided by | One SEC member approving the pull request | Two SEC members approving the pull request, then one week's notice on Discourse | SEC vote |
| Approvals to merge | One | Two | Three, confirming the text matches the vote |
| Version effect | None | None | Minor or major |

```
Fix             pull request -> one SEC approval -> merge
Minor change    pull request -> two SEC approvals -> one week's notice on Discourse -> merge
Change Request  candidate solutions -> SEC vote -> pull request -> three SEC approvals -> merge
```

## Classifying a change

1. Is it a correction, or a new entry in a list that is meant to grow (a unit, a term, a media
   type, a translation)? Yes: **Fix**.
2. Is it compatible? It changes what implementations are expected to do, but everything that
   conforms today still conforms, and it adds nothing new in kind. Yes: **Minor change**.
   No: **Change Request**.

- The size of the diff does not matter. A one-line change that tightens a cardinality is a
  Change Request.
- When in doubt, go one level up. Whoever approves confirms the level, not only the diff.
- **Escalation.** An SEC member who disagrees with the level, or with the change itself, can
  move it up a level before the merge. Nobody can block a change alone; an objection only sends
  it up, and in the end to the vote. Asking for a correction to the text is ordinary review.
- The levels apply to specifications in Trial and Stable. In Planning and Development, changes
  stay informal.

## Fix

A pull request, approved by one SEC member other than the author, then merged. A Problem
Report is optional; if there is one, merging closes it.

Qualifies: typos, formatting, broken links, rewording that does not change meaning;
inconsistencies and obvious errors where it is not in doubt which side is right; diagrams and
generated tables out of sync with their source; bugs in a schema, BMM or OpenAPI file that make
it disagree with the specification; a change to a class description; a new entry in a
terminology list meant to grow; metadata and build tooling.

Does not qualify: an inconsistency or ambiguity where it is unclear which side is right.
Picking one is a decision.

## Minor change

A Problem Report says what is missing. A pull request names it and is approved by two SEC
members other than the committer. Approving means the change is right and it is minor.

The change is then announced on the Discourse specifications forum, and for one week anybody
can veto it. A veto does not block the change; it moves it up to a Change Request. Without a
veto the pull request is merged after the week, and the Problem Report closes.

Qualifies: a change to a class in the BMM (attributes, types, functions); a cardinality
relaxed, such as mandatory to optional or `1..*` to `0..*`; a relaxed pattern or uniqueness
rule; a small optional addition that follows an existing pattern.

Does not qualify, and is a Change Request: a cardinality tightened, or a single value turned
into a list (`0..1` to `0..*`), which both break existing data; a new concept, construct or
behaviour; a new dependency on an external standard; anything else breaking.

## Change Request

For anything new in kind (new logic in ADL or AQL, FHIR value set adoption, a new class,
serialisation or specification) or breaking (removing or renaming something, changing a type,
tightening a constraint, changing a wire format, anything that needs data migration).

1. An SEC member creates the Change Request on the component tracker (`SPECRM`, `SPECAM`, ...).
   No Problem Report is needed.
2. The SEC works out one or more candidate solutions.
3. Optionally, for an impactful change, the candidates go to a 30-day ballot on Discourse.
4. The SEC votes, and with several candidates chooses one.
5. A pull request implements the result in the text and in the affected schemas, BMM or
   OpenAPI files. Three SEC members besides the author approve it, confirming the text matches
   the vote.

No impact-analysis document is required by the workflow; the effect on implementations is
part of the discussion. The Jira fields the tracker still asks for are in the governance skill.

## One change, several pull requests

A change often needs pull requests in several repositories: the specification text, the BMM, the XML and JSON schemas, the OpenAPI files. Then one of them is the **collection pull request**, normally the one with the specification text. Its description lists the other pull requests, and each of them links back to it. Approvals are given on the collection and count for all of them; the others need no approvals of their own, only a check that they match. The SEC votes once, on the Change Request, never per pull request. The pull requests are merged together, the collection last. The ticket links the collection.

## The SEC vote

Only Change Requests are voted on, in one of two ways:

- **In an SEC meeting:** at least half of the SEC members present, and two-thirds of those
  present in favour.
- **On the ticket:** two-thirds of the SEC members in favour.

A member who cannot attend can vote on the ticket, or by proxy with written confirmation. The
result is recorded on the Change Request. A change that does not pass goes back for rework, up
to three rounds.

A member with no vote and no activity on Jira or GitHub for six months is notified by the
co-chairs and moved to the SEC Expert Panel a month later, unless the member asks to stay
active. This is in the Terms of Reference draft, not in the change process.

## Releases and ballots

The SEC votes on Change Requests, not on releases. A release publishes what was already
decided and puts it in front of the community.

| | Minor or major release | Patch release |
|---|---|---|
| Contains | Change Requests, Minor changes, Fixes | Minor changes and Fixes only |
| Community ballot | Yes, 30 days | No |
| SEC vote on the release | No | No |

A ballot is 30 days on the Discourse specifications forum in which the community comments;
it does not vote. The release candidate is announced with the list of what it contains,
including the Fixes and Minor changes published in patch releases since the last ballot.
Comments can lead to new changes; each takes its normal path and can still go into the
release. Fixes are not announced one by one; a Minor change is announced once, for its week
of notice. Neither triggers a release on its own.

## Tickets and pull requests

- Problem Reports are the public way in. Any SEC member can pick one up at any time; there is
  no fixed review round.
- Pull requests carry a `fix` or `minor` label, so the SEC can list them. Any member can ask
  for one to be reverted and raised as a Change Request.
- A Fix without a Problem Report has no ticket; the pull request is the record.
- The proposal reduces the ticket states to Open, In Progress, Closed (Problem Report) and
  Open, In Progress, Review, Closed (Change Request). Jira still runs the old workflow, so
  until it is changed, walk tickets through the transitions in the governance skill
  (Resolve when merged, Close after the release).

## Open

- Traceability of Minor changes: a Change Request for the record, or GitHub release notes?
  Under evaluation in [SPECPR-518](https://openehr.atlassian.net/browse/SPECPR-518).
