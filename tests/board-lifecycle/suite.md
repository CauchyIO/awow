---
command: board-lifecycle
---

# Suite — board-lifecycle

Regression suite for `/board-lifecycle` project-layer governance. The fixture is
a repo with a `board.md` carrying the documented `## Lifecycle` contract and a
dated project-inventory snapshot whose entries include the two timestamp traps
(fresh-timestamp-dead, stale-timestamp-alive). No live board is ever queried:
the command is invoked with `--snapshot`. Invariants, scenario, and fixture
conventions: [README.md](README.md).
