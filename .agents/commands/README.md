# .agents/commands/

Slash commands the agent can run. The files are **flat** — one `<name>.md` per command. Each command declares its adoption phase in frontmatter (`phase:`); the filesystem stays flat so commands are easy to find by name.

## Layout

| Phase (frontmatter) | When a team is ready for it | Commands |
|---|---|---|
| `seed` | Wired up by `/setup-awow` by default (first cycle) | `refinement-prep`, `process-workitem`, `process-transcript` |
| `spread` | After the first Seed cycle | `coaching-review`, `solution-design-flow`, `project-plan`, `design-system`, `artifact`, `my-work` |
| `standardise` | Once most of the team is active | `daily-checkin`, `daily-digest`, `kb-mine`, `kb-synthesize`, `update-context` |

Every command ships in the plugin payload; the phase says when a team is ready for it, not whether it is installed. `/setup-awow` Step 8 lists the Spread and Standardise commands with the pain each removes and the prerequisites each assumes.

The two underscore-prefixed subfolders are handler registries, not directly invocable commands: `_workitem-archetypes/` is loaded by `process-workitem`, and `_meeting-archetypes/` is loaded by `process-transcript`.

Two of these commands are routers: `process-workitem` dispatches to the handlers in `_workitem-archetypes/`; `process-transcript` composes every matching generic lens in `_meeting-archetypes/`, adds sparse team guidance from `context/team/meetings/`, and dispatches to a specialist command when one owns the workflow. `guides/guide-transcript-router.md` documents the transcript-routing model — it is scoped to transcript-consuming commands, not a catalogue of every prompt.

The strategy layer routes across three surfaces sharing one battery (the `department-coach` skill):

| Moment | Surface |
| --- | --- |
| Vision, no measurable goals yet | `/strategy-flow` — formation: bets → committed/aspirational KR draft |
| One bet, live board session | `bet-refinement-coach` skill — ratify numbers, red-pen bars, battery, translate round |
| The department's standing quarter machinery | `/okr-cascade` — Articulate / Refine / Translate / Review |
| Grading KRs against board movement | `/okr-cascade` Review — the recurring strategic review; there is no separate review command |

Plus the top-level meta commands:

- `setup-awow.md` — the incremental, resumable bootstrap wizard
- `update-awow.md` — the legacy vendored-tree update path (`channel: vendored`; not in the payload)

The maintainer eval runner, `/test-awow`, lives in this repo's `.claude/commands/` rather than here — it is not part of the payload.

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

Prerequisites are guidance a command surfaces when invoked out of order — a soft warning, not a hard gate.
