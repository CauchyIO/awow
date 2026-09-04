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
provenance, gate discipline), `stale-move` (the pre-image re-check refuses a
move the board already outran), `docx-notes` (a Word input is read through a
provenance-stamped `office-ingest` sidecar, and an unchanged source is not
reconverted) and `stale-sidecar` (a hash mismatch reconverts instead of reading
the stale body). Setup hooks `git init` the fixture repos; the two Office
scenarios additionally require `uv` or `markitdown` on PATH.
Invariants, scenarios, and fixture conventions: [README.md](README.md).
