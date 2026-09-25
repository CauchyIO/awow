---
teams_root: teams
read_scope: context/team, context/quarterly, context/company
decisions_dir: context/department/decisions
stale_after_days: 28
---

# Department — paths & wiring

Where the department teams registry, OKRs, and governance decisions live. The cascade-check and
commands resolve these locations **from here**, so a team can relocate them without
editing every contract. This file is at a fixed path; its *contents*
are what a team edits.

## Resolution rule (for agents)

Read this file before acting on the department layer. Commands and cascade-check write the default
paths inline for readability; **if the frontmatter above declares a different `teams_root`,
`read_scope`, `decisions_dir`, or `stale_after_days`, those override the inline
literals.** Cross-references *within* department folders (e.g. `teams.md` → individual team
submodules) are relative and move with the folder, so they need no resolution.
