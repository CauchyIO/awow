---
skill: workitem-write
---

# Suite — workitem-write

Planted-fixture suite for the `workitem-write` skill — the first suite that drives a
skill rather than a command (`skill:` frontmatter, resolved to
`.agents/skills/workitem-write/SKILL.md`). The fixture is a hermetic file-based board
(`board/issues/*.md`, declared in the fixture's `context/tooling/board.md`) with
filled REQUIRED conventions, so no live board surface is ever queried. The skill has
no argument surface: script line 1 is the user's opening ad-hoc request, and later
lines answer the gate. Invariants, scenarios, and fixture conventions:
[README.md](README.md).
