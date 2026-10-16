# Tracker writing: before and after

Real texts from the October 2026 SPECPR clean-up, as first written and as the skill wants them.

## Jira issue

### Before (SPECPR-510 as created, 168 words)

> **Origin:** author note removed from the generated class table by specifications-RM PR #40,
> recorded here so the topic is not lost.
>
> **Location:** EHR Extract specification, `EXTRACT_SPEC` class table, attribute `priority:
> Integer` ("Requested priority of this request to be handled by server. Priority schemes are
> likely to be local, and use values agreed by both ends.").
>
> **Note text:**
> > TBD: alternative is standard coded terms
>
> **Note:** the class table (`docs/UML/classes/org.openehr.rm.ehr_extract.extract_spec.adoc`)
> is generated from the UML model, and the mirrored `openehr_rm_*.bmm` files in
> specifications-ITS-BMM still carry the note. Whatever the decision, the UML attribute
> documentation needs the same edit, or the note will come back at the next export.
>
> **Question for Thomas Beale:** is this still an open topic, i.e. should `priority` become a
> coded value? If yes, we will turn it into a CR on the RM tracker. If no, resolve this ticket as
> Won't Do and we remove the note from the UML source.

### After (58 words)

Summary: `EHR Extract: EXTRACT_SPEC.priority as Integer or coded value?`

> `EXTRACT_SPEC.priority` is an `Integer` with locally agreed values; an author note proposed
> standard coded terms instead.
>
> Where: RM EHR Extract, `EXTRACT_SPEC.priority`; note also in the UML source and the ITS-BMM
> `openehr_rm_*.bmm` files
> Change: decide coded value or keep Integer; either way remove the note from the UML source
> Origin: specifications-RM #40

What went: the origin paragraph (one link suffices), the quoted attribute documentation (the
reader opens the class table), the two-branch instruction to the assignee (the field says who,
the Change line says what).

## Pull request

### Before (specifications-LANG #8 as opened, 95 words plus a 10-item checklist)

> Editorial: removes the leftover `TBD` author notes from the LANG specification text. Nothing
> normative changes.
>
> The notes are preserved below so each one can be picked up as a proper CR if it is still
> relevant.
>
> @wolandscat these all look like they came from you. Is any of them still an open topic? Please
> tick the ones that are and we will raise a Jira ticket for each; the rest we consider closed.
>
> - [ ] `docs/BEL/master03-language.adoc`: do we need `Integer64` and `Real64`?
> - ... (nine more)

### After (34 words)

Title: `Remove leftover TBD author notes (editorial)`

> Removes ten `[.tbd]` author notes from BEL, EL and BMM3, and one empty section heading.
> No normative change.
> Why: each note now has a SPECPR ticket (SPECPR-495 to SPECPR-503).
> Amendment record: not needed, editorial.

What went: the checklist (the tickets hold the notes), the question to the author (asked in the
tickets, where the answer is tracked).

## Jira comment

### Before (46 words)

> Thanks for the update. I had a look at the PR and I think this is now fully covered by the
> change that Sebastian approved, so from my side we can resolve this ticket as Fixed once the
> merge is done. Let me know if you disagree.

### After (14 words)

> Fixed by PR specifications-ITS-REST #133 (approved, merge pending). Resolving Fixed after merge.

## Over the cap: a proposal comment

SPECPR-446, comment of 2026-10-16, about 330 words: current state, a two-step removal
proposal, a fallback, the effect on SPECPR-493/452/456, and a question to the SEC. It got a
decision within an hour. Removing the state or the fallback would have made the question
unanswerable.

Correct handling under this skill: draft it, report "comment, 330 words, cap 40; parts: state,
proposal, fallback, impact, question", and ask the user whether to post as is or drop parts.
Post only after the answer. The posted long form keeps the one-line TL;DR first.
