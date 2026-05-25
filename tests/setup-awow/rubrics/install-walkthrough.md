# Rubric — install-walkthrough

End-to-end walkthrough from a clean slate through Step 3. Fixture has `.venv/` and populated pointer stubs (Step 0 inherits) plus the GitHub board reference tree. Script supplies replies for all the wizard's "ask the user" points from Step 1 Phase 1a through Step 3.

## Step 0 — installer inherited

1. *(invariant 2)* Did you `Read $SCRATCH/setup-progress.md` (and observe it does not exist) before producing your first wizard response?
2. *(invariant 1)* In your first wizard response, did you list every step 0 → 9 with status markers, and tell the user you were resuming at Step 0?
3. *(invariant 3)* Did you avoid invoking `setup/install.sh` as a Bash call? The fixture's `.venv/` plus pointer stubs satisfy Step 0's inheritance detection; the installer must not run.
4. *(invariant 1)* Once you moved past Step 0, did you mark it as ✓ in the plan?

## Step 1 Phase 1a — wire the gh CLI surface

5. *(invariant 4)* Did you self-detect the harness ("I'm running in Claude Code") rather than infer it from a `.claude/` directory listing?
6. *(invariant 5)* Did you check for an existing board surface (read `$SCRATCH/.claude/settings.local.json` / `.mcp.json` and/or run `gh auth status`) before asking the user for a URL?
7. *(invariant 7)* When the URL `https://github.com/orgs/CauchyIO/projects/3` was given, did you infer GitHub (not refuse as unsupported)?
8. *(invariant 11)* Did you record `surface: gh-cli` somewhere in the board.md draft?

## Step 1 Phase 1b — Mode A reference walk

9. *(invariant 13)* Did you count closed issues on the board, announce the count, and tell the user you are running Mode A because the count is below 10?
10. *(invariant 8)* For each reference section walked, did its draft go to `$SCRATCH/proposals/setup/step-1/board.md` first (appended) before landing at `$SCRATCH/context/tooling/board.md`?

## Step 1 review-and-adjust gate

11. *(invariant 14)* After board.md landed at `$SCRATCH/context/tooling/board.md`, did you summarise the file in a few bullets and offer the three replies (`proceed` / `adjust <section>` / `evaluate <section>`) before advancing to Step 2?

## Step 2 — mission

12. *(invariant 8)* Did you draft `$SCRATCH/proposals/setup/step-2/mission.md` before moving it to `$SCRATCH/context/team/mission.md`?
13. Did you accept the sample mission sentence on the first try (it names audience, change, and constraint)?

## Step 3 — conventions

14. *(invariant 8)* For each of the four REQUIRED conventions (`issue-titles.md`, `labels.md`, `branches.md`, `output-discipline.md`), did the draft go to `$SCRATCH/proposals/setup/step-3/<name>.md` first?

## Post-run state

15. *(invariant 9)* `$SCRATCH/context/tooling/board.md` exists and contains the substrings `CauchyIO`, `gh-cli`, `https://github.com/orgs/CauchyIO/projects/3`.
16. *(invariant 9)* `$SCRATCH/context/tooling/board.md` contains the section headings `## State machine`, `## Hierarchy`, `## Label taxonomy`, `## Required fields`, `## Team page conventions`.
17. `$SCRATCH/context/team/mission.md` exists and contains the substring `Cauchy helps engineering teams`.
18. All four files exist under `$SCRATCH/context/team/conventions/REQUIRED/`: `issue-titles.md`, `labels.md`, `branches.md`, `output-discipline.md`.
19. `$SCRATCH/setup-progress.md` exists and shows Steps 0, 1, 2, 3 marked complete.
