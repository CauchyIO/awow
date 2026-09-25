---
command: process-workitem
gate: release
---

# Suite — process-workitem

Regression suite for `/process-workitem`, the core command that reads a board item and
carries it as far as the user asked: explain, plan, or build through to a PR. Three
scenarios, one per depth, on one hermetic fixture: a file-based board
(`board/issues/*.md`, declared in `context/tooling/board.md`), filled REQUIRED
conventions, and a two-file Python service whose open item T-102 is a small feature. No
live board, network or `gh` is ever touched. Invariants, scenarios and fixture
conventions: [README.md](README.md).
