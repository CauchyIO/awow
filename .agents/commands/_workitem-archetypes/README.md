# .agents/commands/_workitem-archetypes/

Archetype handlers loaded by `process-workitem`. One file per archetype.

**This folder is where the team extends the base.** `/process-workitem` ships as a thin shell — one entry point, a generic validate → plan → verify frame, and a small set of starter archetypes covering the universal work shapes. The standing investment for whoever processes work items is *here*: capturing the discipline of each work type as it recurs, and wiring an archetype to invoke other commands/skills where that type warrants it. The shipped set is a starting point, not a closed list.

## Optional by design

Archetypes are an **enrichment layer, not a requirement**. If this folder holds only this README, `/process-workitem` runs generically — the generic frame is the day-one fallback. Archetypes store **per-type method, not per-item content**: they keep stories lean by holding reusable discipline once, instead of re-typing it into every story. An elaborately written story reduces, but never removes, their value — the method (reproduce-first, state-file safety, equivalence proof) is reusable across every story of that type.

## What is an archetype?

A *kind of work item* that has its own validation steps, planning rules, and common pitfalls. The router prompt (`commands/process-workitem.md`) classifies an incoming work item and dispatches to the matching handler here. These are reference examples — keep them generic; a team copies and edits the ones it needs.

## Common archetypes

| Archetype | Handler addresses | Status |
|---|---|---|
| `bugfix` | Defect with a known symptom: reproduction, narrow fix, regression test | **Shipped** — `bugfix.md` |
| `feature` | Net-new capability: testable AC, scope boundary, thinnest shippable slice | **Shipped** — `feature.md` |
| `refactor` | Restructuring without behaviour change: equivalence proof, test coverage | **Shipped** — `refactor.md` |
| `spike` | Time-boxed investigation, no code deliverable: capture, decide, spawn follow-ups | **Shipped** — `spike.md` |
| `incident` | Post-mortem / RCA of something that broke: timeline, root cause, remediation tickets | **Shipped** — `incident.md` |
| `infra-change` | Modifying infrastructure: state-file safety, ordering, idempotency | Example |
| `doc` | Documentation updates: scope, placement, accuracy | Example |
| `api-change` | Public API surface: versioning, deprecation, caller enumeration | Example |

The five **shipped** handlers cover the universal work shapes, so `/process-workitem` has something to dispatch to on day one. The `Example` rows are named starting points with no file behind them yet — write the ones your team actually needs, and keep them generic enough to reuse.

## Adding a new archetype

When a kind of work shows up often enough to deserve its own rules:

1. Write the handler as `<archetype>.md` in this folder.
2. Use the handler in the next session and iterate from real output.

No router edit is needed — `process-workitem` reads this folder and matches the incoming story against the handlers it finds. Keep handlers generic enough to reuse; resist encoding one-off, hyper-specific work types.

## Handler shape

Each handler is a markdown file with sections for: when this archetype applies, validation requirements specific to this kind of work, planning rules, common pitfalls, and validation checklist additions.
