---
command: daily-digest
---

# Suite — daily-digest

Regression suite for the `/daily-digest` lens. `command:` names the prompt under
`.agents/commands/` that `/test-awow` executes against each scenario's scratch
workspace. Every fixture pre-seeds `activity/<date>.json` so the snapshot reuse
check fires and no live board/code/chat surface is ever queried; the per-scenario
setup hook re-dates the frozen snapshot to the run day. Invariants, scenarios,
and fixture conventions: [README.md](README.md).
