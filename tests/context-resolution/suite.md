---
command: my-work
---

# Suite — context-resolution

Regression suite for §Context resolution (spec: `proposals/context-resolution.md`),
exercised through `/my-work` — the lightest board-touching command (read-only board
sweep). Every fixture board is an inert file-based sample: items live inline in the
board spec files, so no live board, network, or `gh` auth is ever touched. Scenarios
cover the four shapes from the spec — index-form `board.md`, a monorepo with two
context trees, a nested unscaffolded repo, a workspace root over sibling repos —
plus the invoker-profile rungs (`profile-default`, `profile-vs-explicit`).
Setup hooks `git init` the fixture repos (fixtures cannot track `.git/` directories).
Invariants, scenarios, and fixture conventions: [README.md](README.md).
