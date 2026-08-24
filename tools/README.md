# tools/

Python scripts the team runs occasionally to keep the repo coherent. None of these are required for the agent to function day-to-day — they are housekeeping.

## Scripts

| Script | Purpose | When to run |
|---|---|---|
| `gather.py` | Build `.agents/` into the plugin payloads under `dist/` and `dist-telemetry/` | After edits to `.agents/`; `--check` runs in CI |
| `bootstrap-claude-md.py` | Generate the team's `CLAUDE.md` from the stub + answers | `/setup-awow` Step 4; also after major context changes |
| `validate-context.py` | Lint `context/` for staleness and missing required files | Quarterly, or after refactors |
| `distribute.py` | Push core updates into sibling repos (mono-repo mode) | When the team has grown into multiple repos |
| `session_timeline.py` | Build an interactive timeline + meta-analysis of a project's Claude Code sessions from `~/.claude/projects/` logs (no tracing needed) | Via `project-timeline`; see `guides/guide-session-timeline.md` |

`session_timeline.py` ships with `session_timeline_template.html` (the self-contained view it fills) and is **real, not a skeleton** — stdlib-only, Claude Code only.

## v0.1 status

`gather.py` is real — it is the payload build CI depends on. The rest are **skeletons**: they document the intended shape and the operations they will perform, and real implementations land as the team encounters the friction each one resolves:

- `bootstrap-claude-md.py` becomes real when `/setup-awow` Step 4 is needed in anger.
- `validate-context.py` becomes real after the first Seed cycle when staleness becomes a real signal.
- `distribute.py` becomes real when the team has more than one repo to keep in sync.

## Convention

Each script is invokable as `python tools/<name>.py` with optional `--check` for dry-run mode where applicable.
