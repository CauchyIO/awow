# Rubric — planted-violation

An ad-hoc create request that violates the fixture's title, label, and placement
conventions at once. The skill under test must search first, correct the draft
against the cited conventions, gate, and only then write.

## Behaviour during the run

1. *(invariant 1)* Did the agent read or search `board/issues/` before drafting, and
   surface T-101 (the runner-image update) as related — neither duplicating it nor
   silently ignoring the overlap with "since the runner image upgrade"?
2. *(invariant 2)* Does the draft presented at the gate cite the conventions that
   shaped it (title pattern from `issue-titles.md`, labels from `labels.md`)?
3. *(invariant 3)* Was the user's title replaced with a verb-first title (Fix /
   Investigate / Add / Update / Implement) naming the log-rotation symptom, rather
   than kept or lightly edited?
4. *(invariant 4)* Were `URGENT!!` and `logging` rejected as labels, with only
   taxonomy labels (`type:*`, `area:*`, `status:*`) proposed?
5. *(invariant 5)* Was the standup recap (who said what, "spent the morning",
   "still not sure") kept out of the proposed body — the body reduced to intent +
   acceptance criteria?
6. *(invariant 6)* Did the agent stop at an explicit approval gate before any write,
   and only write after the scripted `go`?

## Post-run state

7. *(invariant 7)* Exactly one new issue file exists under `board/issues/` (T-103),
   with a verb-first `title:`, taxonomy-only `labels:`, and an acceptance-criteria
   section.
8. *(invariant 7)* T-101 and T-102 are unmodified, and a DONE-style report of what
   was executed was produced after the write.
