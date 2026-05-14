# tools/

Python scripts the team runs occasionally to keep the repo coherent. None of these are required for the agent to function day-to-day — they are housekeeping.

## Scripts

| Script | Purpose | When to run |
|---|---|---|
| `gather.py` | Mirror `.agents/` → `.claude/` + `.github/` | After edits to `.agents/` |
| `bootstrap-claude-md.py` | Generate the team's `CLAUDE.md` from the stub + answers | `/setup-awow` Step 4; also after major context changes |
| `validate-context.py` | Lint `context/` for staleness and missing required files | Quarterly, or after refactors |
| `distribute.py` | Push core updates into sibling repos (mono-repo mode) | When the team has grown into multiple repos |
| `reset-adopter-state.py` | Wipe adopter-produced artefacts to re-run the walkthrough | Maintainer iteration loop (invoked by `/awow-reset`) |

## v0.1 status

All four are **skeletons**. They document the intended shape and the operations they will perform. Real implementations land as the team encounters the friction each one resolves:

- `gather.py` becomes real when the team has more than one or two skills to mirror.
- `bootstrap-claude-md.py` becomes real when `/setup-awow` Step 4 is needed in anger.
- `validate-context.py` becomes real after the first Seed cycle when staleness becomes a real signal.
- `distribute.py` becomes real when the team has more than one repo to keep in sync.

## Convention

Each script is invokable as `python tools/<name>.py` with optional `--check` for dry-run mode where applicable.
