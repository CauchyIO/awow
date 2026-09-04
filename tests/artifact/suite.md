---
command: artifact
---

# Suite — artifact

Regression suite for the Word target (spec: `proposals/word-export-design.md`),
exercised through `/artifact`. Every fixture board is an inert file-based
sample: items live inline in `context/tooling/board.md`, so no live board,
network, or `gh` auth is ever touched. Scenarios: `word-default` (target asked,
docx from markdown, stock styles reported), `word-reference` (registered
reference doc applied), `pandoc-absent` (one install offer, honest report; runs
in an `env/` container without pandoc). Setup hooks `git init` the fixture
repos. Invariants, scenarios, and fixture conventions: [README.md](README.md).
