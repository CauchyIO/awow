# Rubric — install-step3-conventions

Step 3 drafts the four REQUIRED conventions (issue-titles, labels, branches, output-discipline). Greenfield board → Guide mode. Script supplies `accept`/`approve` per convention.

## Wizard behaviour during the run

1. *(invariant 1)* First wizard response lists every step 0 → 9 with status markers; Steps 0–2 marked ✓, Step 3 marked ⧗.
2. Did the wizard count closed issues and announce Guide mode because the count is below 10?
3. *(invariant 8)* Did each convention land at `$SCRATCH/proposals/setup/step-3/<name>.md` first, before moving to `$SCRATCH/context/team/conventions/REQUIRED/<name>.md`?
4. Did the wizard cover all four REQUIRED conventions: `issue-titles.md`, `labels.md`, `branches.md`, `output-discipline.md`?

## Post-run state

5. All four files exist under `$SCRATCH/context/team/conventions/REQUIRED/`: `issue-titles.md`, `labels.md`, `branches.md`, `output-discipline.md`.
6. *(invariant 8)* All four drafts also exist under `$SCRATCH/proposals/setup/step-3/`.
