# .agents/commands/

Slash commands the agent can run, organised by adoption phase.

## Layout

| Subfolder | Phase | When the team adopts it |
|---|---|---|
| `seed/` | Phase 2 (first cycle) | Wired up by `/setup-awow` by default |
| `spread/` | Phase 3 (after first Seed cycle) | Opt-in via `/awow-add <command>` |
| `standardise/` | Phase 4 (most of team active, governance in place) | Opt-in via `/awow-add <command>` |
| `_archetypes/` | Phase-agnostic | Handlers loaded by `process-workitem` |

Plus four top-level meta commands:

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
  - "Step 0 of /setup-awow complete (board MCP wired)"
  - "Team has shipped at least one Seed cycle"
removes_pain: "the <specific friction this command removes> problem"
---
```

`/awow-add` reads prerequisites and warns when a command is invoked out of order. Soft warning, not hard gate.
