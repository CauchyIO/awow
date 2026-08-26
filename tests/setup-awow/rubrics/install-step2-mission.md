# Rubric — install-step2-mission

Step 2 drafts a short team profile (what the team works on, for whom, tech stack; mission line optional) from board and repo observation. This fixture's scratch offers nothing to observe — no manifests, no reachable board items — so the wizard must fall back to asking. Script supplies the profile, then `approve` to land it.

## Wizard behaviour during the run

1. *(invariant 1)* First wizard response lists every step 0 → 9 with status markers; Steps 0 and 1 marked ✓, Step 2 marked ⧗.
2. Did the wizard attempt observation first (or recognise there was nothing to observe) and then ask the fallback question — what the team works on and in what stack — rather than demanding a one-sentence mission?
3. *(invariant 8)* Did the wizard draft mission.md under `$SCRATCH/proposals/setup/step-2/mission.md` before moving it to `$SCRATCH/context/team/mission.md`?
4. Did the wizard accept the supplied profile on the first try, without iterating on the mission line's quality?

## Post-run state

5. `$SCRATCH/context/team/mission.md` exists and contains the substring `Cauchy helps engineering teams`.
6. *(invariant 8)* `$SCRATCH/proposals/setup/step-2/mission.md` also exists (the draft was kept, not deleted, after landing).
