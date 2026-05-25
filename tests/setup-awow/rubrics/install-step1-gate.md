# Rubric — install-step1-gate

After `board.md` lands at `$SCRATCH/context/tooling/board.md`, the wizard must enter the review-and-adjust gate and refuse to advance to Step 2 until the user types `proceed`. Script supplies one reply: `proceed`.

## Wizard behaviour during the run

1. *(invariant 14)* Did the wizard summarise the landed `board.md` in a few bullets (surface, state machine, hierarchy, label prefixes, fields, any divergence entries) before asking the gate question?
2. *(invariant 14)* Did the wizard explicitly offer `proceed` / `adjust <section>` / `evaluate <section>` as the three accepted replies?
3. *(invariant 14)* On receiving `proceed`, did the wizard advance to Step 2 (and not silently skip the gate)?
4. *(invariant 8)* Was `$SCRATCH/context/tooling/board.md` already in place before the gate prompt (Phase 1b should have landed it)?
