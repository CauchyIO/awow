---
command: migrate-to-plugin
---

# Suite — migrate-to-plugin

Regression suite for `/migrate-to-plugin` de-vendoring. Each scenario's setup
hook builds a **real vendored adopter** in the scratch: a git repo whose first
commit is the v0.9.2 starter surface archived from this repo's own history,
with two team edits committed on top — never a hand-crafted imitation. A copy
of the current `dist/` payload lands at `.awow-payload/` inside the scratch and
is passed as `--source`, so no plugin install is needed. Invariants, scenarios,
and fixture conventions: [README.md](README.md).
