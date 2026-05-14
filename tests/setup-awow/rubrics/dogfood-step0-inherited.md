# Rubric — dogfood-step0-inherited

Fixture has `.venv/` and populated `.claude/commands/` + `.github/prompts/` stubs (Step 0 inherited from a parent repo). Script supplies one reply ("current only") for the harness question. Wizard should detect Step 0 already done, skip the installer, and move into Step 1 Phase 1a.

## Wizard behaviour during the run

1. *(invariant 1)* In your first wizard response, did you list every step 0 → 9 with a status marker (✓ / ⧗ / ☐)?
2. *(invariant 2)* Did you `Read $SCRATCH/.venv` (or `ls $SCRATCH`) — or otherwise inspect — to confirm `.venv/` exists before deciding what to do about Step 0?
3. *(invariant 3)* Did you avoid invoking `setup/install.sh` as a Bash call? The fixture's `.venv/` already exists; the installer must not run.
4. *(invariant 1)* Did you mark Step 0 as ✓ (or equivalent) in the plan listing rather than ☐?
5. *(invariant 4)* When advancing to Step 1 Phase 1a, did you self-detect the harness (e.g. "I'm running in Claude Code") rather than infer it from a directory listing?

## Post-run state

6. Does `$SCRATCH/setup-progress.md` now exist with Step 0 marked complete?
7. Is `$SCRATCH/.venv/` unchanged (the installer was correctly skipped)?
