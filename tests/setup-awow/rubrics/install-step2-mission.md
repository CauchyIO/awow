# Rubric — install-step2-mission

Step 2 drafts a short team profile (what the team works on, for whom, tech stack; mission line optional) from board and repo observation. This fixture's scratch offers nothing to observe — no manifests, no reachable board items — so the wizard must fall back to asking. Script supplies the profile, then `approve` to land it.

## Wizard behaviour during the run

1. *(invariant 1)* First wizard response shows the required core complete (Steps 0 and 1 ✓) plus a compact deferred-fills line — and offers the fills without walking any of them unprompted.
2. *(invariant 1)* Did the wizard enter the team-profile fill only after the scripted reply named it, rather than starting Step 2 on its own?
3. Did the wizard attempt observation first (or recognise there was nothing to observe) and then ask the fallback question — what the team works on and in what stack — rather than demanding a one-sentence mission?
4. *(invariant 8)* Did the wizard draft mission.md under `$SCRATCH/proposals/setup/step-2/mission.md` before moving it to `$SCRATCH/context/team/mission.md`?
5. Did the wizard accept the supplied profile on the first try, without iterating on the mission line's quality?

## Post-run state

6. `$SCRATCH/context/team/mission.md` exists and contains the substring `Cauchy helps engineering teams`.
7. *(invariant 8)* `$SCRATCH/proposals/setup/step-2/mission.md` also exists (the draft was kept, not deleted, after landing).
