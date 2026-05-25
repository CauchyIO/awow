---
archetype: bugfix
board_type: bug
triggers: [fix, bug, broken, regression, incorrect, fails, crashes, wrong, missing, swallowed, flaky]
when-not: "Missing capability rather than broken behaviour → feature. 'Improve' or 'rework' with no named defect → refactor."
---

# bugfix — archetype handler

A defect with a known symptom. The fix is narrow; the test that catches the regression is the durable artefact.

This is a **starter archetype** shipped with awow v0.1. Edit it to match how your team actually triages and fixes bugs.

The frontmatter above is the matching contract `/process-workitem` and `/refinement-prep` read: `board_type` joins this handler to the team's board work-type (mapped in `context/tooling/board.md`), and `triggers` / `when-not` are the prose-inference fallback when no board type signal is present.

---

## When this archetype applies

The story names a current, reproducible-or-reportable misbehaviour: wrong output, wrong state, wrong error, crash, missing event. If the story names a missing capability rather than broken behaviour, route to `feature` instead.

Trigger words in the title or body: *fix*, *bug*, *broken*, *regression*, *incorrect*, *fails*, *crashes*, *wrong*, *missing*, *swallowed*, *flaky*.

If the story says "improve" or "rework" without naming an incorrect behaviour, it is probably a `refactor`, not a `bugfix`.

---

## Creation completeness (used by /refinement-prep)

The three inputs under **Validation requirements** below are also the bar for a *complete bug story*. When `/refinement-prep` drafts a bug, check the draft carries all three — reproduction, expected-vs-actual, blast radius — and surface any gap as an open question rather than drafting around it. Capturing them at creation is what lets `/process-workitem` route and plan without bouncing the story back to refinement.

---

## Validation requirements

Before drafting a plan, confirm three things. If any are missing, stop and ask.

1. **Reproduction.** A concrete way to trigger the bug — a failing test, a curl command, a reproduction note, or a stack trace from a real incident. "Sometimes it happens" is not a reproduction.
2. **Expected vs actual.** What the system *should* do, written next to what it *currently* does. If only "actual" is in the story, the team has not decided what "fixed" means yet — go back to refinement.
3. **Blast radius.** Which surface is affected (one endpoint, one screen, one job)? If "everything is broken," the story is too big or the diagnosis is wrong; split or re-investigate.

**Do not start coding from a story that lacks any of these.** A plan built on a guessed repro fixes the wrong thing.

---

## Planning rules

- **The fix is the smallest change that makes the reproduction pass.** No surrounding cleanup, no refactor, no observability uplift. Anything tangential becomes a follow-up story.
- **Write the regression test first** (or the manual repro check, when an automated test is not possible). If the test still passes after a deliberate revert of the fix, the test is not testing the bug — fix the test before fixing the code.
- **Name the root cause in the plan**, not just the symptom. If the root cause is uncertain, the plan's first step is a spike to confirm it — not a code change.
- **Surface adjacent risk without acting on it.** If the bug suggests other latent issues ("this null check is missing in three other call sites"), record them as follow-up proposals in the plan's *Risks* section. Do not expand scope.

---

## Common pitfalls

| Pitfall | Symptom | What to do instead |
|---|---|---|
| Fixing the symptom, not the cause | The same bug returns next sprint under a slightly different shape | Trace from symptom back to the first wrong state; fix there |
| Bundling cleanup with the fix | PR diff is large; reviewer can't separate fix from refactor | Land the fix; open a separate proposal for the cleanup |
| No regression test | The bug returns without anyone noticing | Add the smallest test that would have caught it |
| Plan says "fix the bug" with no root cause | The agent guesses; the fix is brittle | The plan must name *why* the wrong behaviour happens, not just *that* it does |
| Marking "won't fix" silently | Story closed without explanation; same bug reopened next quarter | If the team decides not to fix, record the rationale in the knowledge base, then close |

---

## Verification checklist (additions for this archetype)

In addition to the generic verification from `process-workitem` step 6:

- [ ] The regression test (or manual repro) fails on the pre-fix commit and passes on the fix commit.
- [ ] No unrelated tests changed.
- [ ] The PR description quotes the root cause in one sentence.
- [ ] Acceptance criteria reference observable behaviour, not "the code now does X" implementation detail.
- [ ] Adjacent risks surfaced in the plan's *Risks* section have follow-up proposal stubs, or are explicitly accepted.
