# .agents/commands/

Slash commands the agent can run. The files are **flat** — one `<name>.md` per command. Each command declares its adoption phase in frontmatter (`phase:`); the filesystem stays flat so commands are easy to find by name.

## Layout

| Phase (frontmatter) | When the team adopts it | Commands |
|---|---|---|
| `seed` | Wired up by `/setup-awow` by default (first cycle) | `refinement-prep`, `process-workitem`, `process-transcript` |
| `spread` | Opt-in via `/awow-add <command>` (after first Seed cycle) | `coaching-review`, `solution-design-flow`, `project-plan`, `design-system`, `artifact`, `my-work` |
| `standardise` | Opt-in via `/awow-add <command>` (most of team active) | `daily-checkin`, `daily-digest`, `kb-mine`, `kb-synthesize`, `update-context` |

The two underscore-prefixed subfolders are handler registries, not directly invocable commands: `_workitem-archetypes/` is loaded by `process-workitem`, and `_meeting-archetypes/` is loaded by `process-transcript`.

Two of these commands are routers: `process-workitem` dispatches to the handlers in `_workitem-archetypes/`; `process-transcript` composes every matching generic lens in `_meeting-archetypes/`, adds sparse team guidance from `context/team/meetings/`, and dispatches to a specialist command when one owns the workflow. `guides/guide-transcript-router.md` documents the transcript-routing model — it is scoped to transcript-consuming commands, not a catalogue of every prompt.

Plus the top-level meta commands:

- `setup-awow.md` — the incremental, resumable bootstrap wizard
- `awow-add.md` — promote a Spread/Standardise command into the active set
- `awow-status.md` — report current phase and readiness signals
- `awow-reset.md` — wipe adopter-produced state so the walkthrough can be re-run end-to-end (maintainer iteration loop)

## Phase frontmatter

Every command declares its phase and prerequisites:

```yaml
---
phase: seed | spread | standardise
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "Team has shipped at least one Seed cycle"
removes_pain: "the <specific friction this command removes> problem"
---
```

`/awow-add` reads prerequisites and warns when a command is invoked out of order. Soft warning, not hard gate.
