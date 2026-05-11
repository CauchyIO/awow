# .agents/commands/_archetypes/

Archetype handlers loaded by `process-workitem`. One file per archetype.

## What is an archetype?

A *kind of work item* that has its own validation steps, planning rules, and common pitfalls. The router prompt (`commands/seed/process-workitem.md`) classifies an incoming work item and dispatches to the matching handler here.

## Common archetypes

| Archetype | Handler addresses |
|---|---|
| `column-add` / `schema-change` | Extending a table with new columns: source validation, type matching, downstream propagation |
| `source-onboard` | Adding a new source system to the data platform |
| `bugfix` | Defect with a known symptom: reproduction, narrow fix, regression test |
| `infra-change` | Modifying infrastructure: state-file safety, ordering, idempotency |
| `doc` | Documentation updates: scope, placement, accuracy |
| `refactor` | Restructuring without behaviour change: equivalence proof, test coverage |
| `spike` | Investigation with no code deliverable: time-box, capture, decision |
| `api-change` | Public API surface: versioning, deprecation, caller enumeration |

## Adding a new archetype

When a kind of work shows up often enough to deserve its own rules:

1. Write the handler as `<archetype>.md` in this folder.
2. Register it in the router (`commands/seed/process-workitem.md` Step 1, classification list).
3. Use the handler in the next session and iterate from real output.

## Handler shape

Each handler is a markdown file with sections for: when this archetype applies, validation requirements specific to this kind of work, planning rules, common pitfalls, and validation checklist additions.
