---
name: department-coach
description: "The single home of the KR challenge battery — loaded by /okr-cascade (Refine, Review), /strategy-flow (Gate 2), and the bet-refinement-coach skill. Per-KR tests (outcome-not-output through gameability), objective-level tests (leading/lagging balance, commercial face), the admin-burden test for tracking mechanisms, the one-decision-at-a-time session discipline, and the standard moves for fixing what fails."
---

# department-coach

You read this skill whenever `/okr-cascade` puts you in front of an objective or key result that needs challenging — mainly its Refine and Review stages. It carries the generic coaching method only: no organisation names, no specific objectives, nothing that belongs in a real OKR doc. Everything here transfers to any department.

---

## Core principle

A KR that survives unchallenged is a KR nobody will trust by quarter's end. Run every candidate KR through the battery below before it is ratified; run every standing KR through it again at Review, this time graded on movement, not on whether the plan was followed.

---

## The challenge battery

Nine named per-KR tests, asked in order. The first eight are pass/fail — stop and resolve with one of the standard moves below the first time a KR fails one. The ninth does not fail a KR; it classifies every KR that clears the first eight.

- **Outcome-not-output.** Ask: "Does this name a result the business cares about, or an activity your team performs?" An activity fails this test regardless of how measurable it sounds.
- **Baseline.** Ask: "What is the current value, right now, in the same units as the target?" No baseline means the KR cannot show movement — it can only show a number appearing from nowhere.
- **Target-plus-date.** Ask: "What is the target value, and by what date is it reached?" A KR with either missing is a hope, not a KR.
- **Controllability.** Ask: "Can the team meaningfully move this number through its own actions, or is it driven by forces outside the team?" A KR the team cannot influence belongs on someone else's OKR doc, not this one.
- **Falsifiability.** Ask: "Is there a state of the world in which this KR is unambiguously not met?" If every outcome can be narrated as success, the KR is unfalsifiable and must be rewritten before it is ratified.
- **Vanity-metric test.** Ask: "What decision changes when this number moves?" No answer means the number is vanity — track it elsewhere, never as a KR.
- **Operationalize-fuzzy-quality.** When a KR rests on a quality word ("high standard", "excellent", "best in class"), ask: "What does good look like, and how is it measured?" The KR does not pass until the definition and the measure exist.
- **Gameability.** Ask: "Which adjacent urgent goal can silently eat this one — how would we compromise this KR without anyone noticing?" If the compromise is easy to name, redesign the KR so the compromise reads red.
- **Committed-vs-aspirational split.** Ask: "Does your own action move this number this quarter — or do you only influence it?" "Moves it" makes the KR committed — the team is on the hook to hit it. "Only influences it" makes the KR aspirational — a stretch the team reaches for without full control. Log the split next to the KR — an unmarked KR defaults to neither status and cannot be graded fairly at Review.

### Objective-level tests

Two tests asked per objective (or bet) once its KRs are drafted — they fail the *set*, not a single KR:

- **Leading/lagging balance.** Ask: "Is there at least one KR here the team can move *this* quarter?" An objective graded only on lagging outcomes gives no steering signal until it is too late to steer.
- **Commercial face.** Ask: "Where is the money line on this objective?" Every objective ties to a commercial KR, not only capability ones — an objective with no commercial face is a hobby until proven otherwise.

### The mechanism test

- **Admin-burden.** For every tracking mechanism or cadence step a KR implies, ask: "Will anyone actually do this?" It passes only when the step costs ≤5 minutes, rides an existing ritual, is agent-pre-filled where telemetry exists, and has a visible payoff for the person doing it. "No one is going to do that" is a design verdict, not an attitude problem.

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

The resolutions available when a KR fails a battery test, plus two diagnostics for arguments that loop. Pick one per failure; never leave a failing KR unresolved in the doc.

- **Demote-to-scoreboard.** The KR fails outcome-not-output or the vanity-metric test, but the number still carries local value. Move it off the OKR doc onto a team scoreboard or dashboard — it stays visible, it stops being counted as a KR.
- **Provisional-number-plus-revisit-date.** The KR fails baseline or target-plus-date because the data genuinely does not exist yet. Accept a provisional number paired with an explicit revisit date; never leave it vague with no date to firm it up.
- **Acts-vs-outcomes.** The proposed KR is really a list of activities wearing an outcome's clothing. Split it: the outcome becomes the KR, the activities move into the initiative that describes how the team gets there.
- **Park-with-named-dependency.** The KR fails controllability or cannot proceed because of a blocker. Park it explicitly, name the dependency, and state the condition under which it un-parks — never let it stall silently with no named cause. Ambitious instruments that lack tooling get the split form: a cheap version now that rides existing rituals and data, the full version next period, funded only if the cheap one proves worth it.
- **Collision-rule-plus-logged-exception.** Two KRs genuinely trade off. Never reword one softer to dodge the conflict — rule which one wins live collisions (the committed one, by default), log every win as a one-line exception (`<label>-by-exception: <reason>`), and set a tripwire: N logged exceptions force the trade-off onto the next review agenda.
- **Denominator check** *(diagnostic)*. When a KR feels misplaced or an ownership argument loops, compare counting units — which population is being counted, and which objective's redness does this number hurt? That settles "does this belong here" structurally instead of by volume of argument.
- **Instrument split** *(diagnostic)*. When a measurement discussion loops, it is usually two or three instruments argued as one. Separate them: a one-off gap assessment (kickoff and quarterly), a continuous scorecard (passive, periodic correction), and daily capture (a by-product where telemetry exists, a check-in ritual where it does not). Different questions, different cadences.

---

## Who loads this skill

`/okr-cascade` (Refine and Review), `/strategy-flow` (Gate 2, where drafted KRs face the battery), and `bet-refinement-coach` (a live board session working one bet). The battery lives here once; the callers carry their own flow and gates.

## How this fits `/okr-cascade`

- **Articulate** applies the outcome-not-output test to each proposed objective before it is written to the quarter doc.
- **Refine** runs every KR through the full battery, one decision at a time, logging ratifications and overrides to `<decisions_dir>/<date>-refine.md`.
- **Review** re-applies the battery's spirit to standing KRs — grading movement against baseline and target, not plan compliance — and reaches for the standard moves (plus double-down / park / reallocate / re-bet) when a KR needs a call. This *is* the recurring strategic review: there is no separate review command.
