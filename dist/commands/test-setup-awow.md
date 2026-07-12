---
description: "deprecated alias"
phase: maintenance
prerequisites: []
removes_pain: "wording-change-broke-the-wizard regressions caught only by manual walkthrough"
channel: vendored
---

# /test-setup-awow [<scenario>] — deprecated alias

> **Maintainer-only command.** If you templated this repo and are not maintaining awow itself, delete this file and the `tests/` directory.

This command is a deprecated alias. Run the generalised runner instead, passing through any scenario and flags you were given:

```
/test-awow setup-awow [<scenario>] [--keep]
```

Follow [`test-awow.md`](test-awow.md) end to end — suite `setup-awow` resolves the wizard via `tests/setup-awow/suite.md`. Do not reimplement the old six-phase protocol from memory; the eight-phase protocol in `/test-awow` supersedes it.
