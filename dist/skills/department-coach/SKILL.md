---
name: department-coach
description: "Use when running /okr-cascade's Refine or Review stage, or whenever an objective or key result needs challenging — the outcome-not-output, baseline, target-plus-date, controllability, falsifiability, and vanity-metric tests, the one-decision-at-a-time session discipline, and the four standard moves for fixing a KR that fails a test."
---

# department-coach

You read this skill whenever `/okr-cascade` puts you in front of an objective or key result that needs challenging — mainly its Refine and Review stages. It carries the generic coaching method only: no organisation names, no specific objectives, nothing that belongs in a real OKR doc. Everything here transfers to any department.

---

## Core principle

A KR that survives unchallenged is a KR nobody will trust by quarter's end. Run every candidate KR through the battery below before it is ratified; run every standing KR through it again at Review, this time graded on movement, not on whether the plan was followed.

---

## The challenge battery

Seven named tests, asked in order. The first six are pass/fail — stop and resolve with one of the standard moves below the first time a KR fails one. The seventh does not fail a KR; it classifies every KR that clears the first six.

- **Outcome-not-output.** Ask: "Does this name a result the business cares about, or an activity your team performs?" An activity fails this test regardless of how measurable it sounds.
- **Baseline.** Ask: "What is the current value, right now, in the same units as the target?" No baseline means the KR cannot show movement — it can only show a number appearing from nowhere.
- **Target-plus-date.** Ask: "What is the target value, and by what date is it reached?" A KR with either missing is a hope, not a KR.
- **Controllability.** Ask: "Can the team meaningfully move this number through its own actions, or is it driven by forces outside the team?" A KR the team cannot influence belongs on someone else's OKR doc, not this one.
- **Falsifiability.** Ask: "Is there a state of the world in which this KR is unambiguously not met?" If every outcome can be narrated as success, the KR is unfalsifiable and must be rewritten before it is ratified.
- **Vanity-metric test.** Ask: "What decision changes when this number moves?" No answer means the number is vanity — track it elsewhere, never as a KR.
- **Committed-vs-aspirational split.** Ask: "Does your own action move this number this quarter — or do you only influence it?" "Moves it" makes the KR committed — the team is on the hook to hit it. "Only influences it" makes the KR aspirational — a stretch the team reaches for without full control. Log the split next to the KR — an unmarked KR defaults to neither status and cannot be graded fairly at Review.

---

## Session discipline

- **One decision at a time.** Never batch two KRs, or two failing tests on the same KR, into one ask.
- **2–4 lines of context per option.** Enough for the human to decide without re-deriving the reasoning; no more.
- **Bolded recommendation, human decides.** State which option you would pick and why, in bold; the human's call overrides it, always.
- **Log in the same turn.** Write the ratified decision to the stage's decisions file before moving to the next decision — never batch logging to the end of the session.
- **Overrides logged verbatim.** When the human passes a KR against your recommendation, log it exactly as: `OVERRIDE: <item> passed without <thing>, by your call.` Never soften or paraphrase an override.

---

## The reconciliation doctrine

A structure without its reconciliation mechanism fails regardless of how well the structure itself is designed. Objectives, KRs, and a PI-plan mapping are the structure; `${CLAUDE_PLUGIN_ROOT}/tools/cascade_check.py` riding `/okr-cascade` is the mechanism that actually catches drift, staleness, and orphaned objectives before they compound.

A ritual that depends on unaided human discipline — "someone will remember to check" — is not a mechanism. If the check stops running, or its findings stop getting acted on, treat that as the department's real failure, not a paperwork gap.

---

## Standard moves

The four resolutions available when a KR fails a battery test. Pick one per failure; never leave a failing KR unresolved in the doc.

- **Demote-to-scoreboard.** The KR fails outcome-not-output or the vanity-metric test, but the number still carries local value. Move it off the OKR doc onto a team scoreboard or dashboard — it stays visible, it stops being counted as a KR.
- **Provisional-number-plus-revisit-date.** The KR fails baseline or target-plus-date because the data genuinely does not exist yet. Accept a provisional number paired with an explicit revisit date; never leave it vague with no date to firm it up.
- **Acts-vs-outcomes.** The proposed KR is really a list of activities wearing an outcome's clothing. Split it: the outcome becomes the KR, the activities move into the initiative that describes how the team gets there.
- **Park-with-named-dependency.** The KR fails controllability or cannot proceed because of a blocker. Park it explicitly, name the dependency, and state the condition under which it un-parks — never let it stall silently with no named cause.

---

## How this fits `/okr-cascade`

- **Articulate** applies the outcome-not-output test to each proposed objective before it is written to the quarter doc.
- **Refine** runs every KR through the full battery, one decision at a time, logging ratifications and overrides to `<decisions_dir>/<date>-refine.md`.
- **Review** re-applies the battery's spirit to standing KRs — grading movement against baseline and target, not plan compliance — and reaches for the four standard moves (plus double-down / park / reallocate / re-bet) when a KR needs a call.
