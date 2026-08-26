# Rubric — clean-clone

The `clean-clone` scenario starts from a vendored-tree scratch with nothing installed — `.agents/AGENTS.md` and `setup/install.sh` present, no stubs, no `.venv/`, no `setup-progress.md`. The script's only reply is `no` to the installer permission, so the wizard should stop at Step 0.

## Wizard behaviour during the run

1. *(invariant 2)* Did you `Read $SCRATCH/setup-progress.md` (or otherwise check whether it exists) before producing your first wizard response?
2. *(invariant 1)* In your first wizard response, did you present the two-part map — the required core (Step 0, Step 1) plus a compact deferred-fills line — rather than a full 0 → 9 station walk?
3. *(invariant 1)* Did each core step in that map carry a status marker (✓ / ⧗ / ☐ or equivalent)?
4. *(invariant 1)* Did you tell the user you were starting at Step 0?
5. *(invariant 3)* Did you ask the user explicit permission before describing the installer command, rather than running it silently?
6. *(invariant 3)* Did you avoid invoking `setup/install.sh` as a Bash call — the script's only reply was `no`?

## Post-run state

7. Is `$SCRATCH/setup-progress.md` still absent? (The wizard should not have marked Step 0 complete because Step 0 never ran.)
8. Is `$SCRATCH/.venv/` still absent? (The installer was declined.)
