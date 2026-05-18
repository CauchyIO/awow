# Rubric — dogfood-step2-mission

Step 2 asks for the team's mission in one sentence. Script supplies dogfood's actual mission line, then `approve` to land it.

## Wizard behaviour during the run

1. *(invariant 1)* First wizard response lists every step 0 → 9 with status markers; Steps 0 and 1 marked ✓, Step 2 marked ⧗.
2. Did the wizard ask "What is your team's mission, in one sentence?" (or close paraphrase) before producing any draft?
3. *(invariant 8)* Did the wizard draft mission.md under `$SCRATCH/proposals/setup/step-2/mission.md` before moving it to `$SCRATCH/context/team/mission.md`?
4. Did the wizard accept the dogfood mission sentence on the first try (it names audience, change, and constraint, so the "refuse anything trivial" rule should not fire)?

## Post-run state

5. `$SCRATCH/context/team/mission.md` exists and contains the substring `Cauchy helps engineering teams`.
6. *(invariant 8)* `$SCRATCH/proposals/setup/step-2/mission.md` also exists (the draft was kept, not deleted, after landing).
