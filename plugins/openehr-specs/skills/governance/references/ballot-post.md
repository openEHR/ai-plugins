# The ballot post

Every minor and major release goes to a 30-day community ballot before it is published (see
`change-workflow.md`, "Releases and ballots"). The ballot is one post on the Discourse
specifications forum, written from the template below. The community comments; it does not
vote. Patch releases get no ballot.

Fill the template from Jira: the Fix Versions on the tickets are the list of what the release
carries (`fixVersion = "<Component> Release x.y.z"` on `SPECPR`, the matching version on the
component tracker). Link every ticket. Link the development build, not a branch.

## Template

```
[Ballot] <Component> Release <x.y.z>: comments until <date>

The SEC is preparing <Component> Release <x.y.z>. This is the 30-day community ballot: read it,
try it against your implementation, and comment by <date>. Comments, not votes; every comment
gets an answer in this thread.

**What is in it**
- Change Requests: [<SPECXX-nnn> <title>](<url>), ...
- Minor changes: [<SPECPR-nnn> <title>](<url>), ...
- Fixes: [all tickets in this release](<Jira release page>), including patch releases <x.y.1, x.y.2>
  published since the last ballot

**Where to read it**
- Development build: https://specifications.openehr.org/releases/<COMPONENT>/development/
- What changed since Release <previous>: <amendment records of each document, or the release
  view once the Antora site has one>

**How to comment**
- Reply here, or raise a Problem Report on SPECPR and link it in this thread.
- Each comment takes its normal path as a Fix, Minor change or Change Request, and can still go
  into this release.

After <date> the SEC answers the comments here, makes the resulting changes, and publishes the
release. The release notes follow in this thread.
```

## After the ballot

- Answer every comment in the thread, with the ticket or pull request it led to, or why not.
- Changes from the ballot take their normal path (Fix, Minor change, Change Request) and keep
  the same Fix Version.
- Publish the release (release-checklist.md), then post the release notes as the last reply.

## How other communities do it

| Community | Review period | What is published | Where comments go |
|---|---|---|---|
| HL7 FHIR | Ballot cycle, about 30 days | The continuous-integration build plus a list of what changed; one tracker item per comment | Jira; every negative comment is reconciled with the commenter |
| W3C | Candidate Recommendation review, usually four weeks or more | The specification with a "Changes since" appendix and a diff-marked version | GitHub issues of the specification repository |
| IETF | Last Call, two weeks (four for individual submissions) | The draft with a "Changes since" section and an rfcdiff against the previous version | The last-call mailing list |

All three have a fixed period, a list or diff of what changed, a tracker for comments, and an
answer to each comment. openEHR has the period and the tracker; the diff view is the gap:
[antora-openehr #57](https://github.com/openEHR/antora-openehr/issues/57).
