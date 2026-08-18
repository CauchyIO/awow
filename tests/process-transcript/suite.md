---
command: process-transcript
---

# Suite — process-transcript

Regression suite for the board-plan gate (spec:
`proposals/invoker-topology-and-board-plan.md`, Pillar 4), exercised through
`/process-transcript` — the flow with the richest gate. Every fixture board is an
inert file-based sample: items live inline in `context/tooling/board.md`, so no
live board, network, or `gh` auth is ever touched; an approved write edits the
item's row. Scenarios: `plan-gate` (grammar, `details` drill-down with
provenance, gate discipline) and `stale-move` (the pre-image re-check refuses a
move the board already outran). Setup hooks `git init` the fixture repos.
Invariants, scenarios, and fixture conventions: [README.md](README.md).
