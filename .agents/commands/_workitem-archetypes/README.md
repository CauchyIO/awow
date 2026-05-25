# .agents/commands/_workitem-archetypes/

Archetype handlers loaded by `process-workitem`, and read by `refinement-prep` at creation time. One file per archetype.

**This folder is where the team extends the base.** `/process-workitem` ships as a thin shell — one entry point, a generic validate → plan → verify frame, and a single starter archetype (`bugfix`). The standing investment for whoever processes work items is *here*: capturing the discipline of each work type as it recurs, and wiring an archetype to invoke other commands/skills where that type warrants it. The shipped set is a starting point, not a closed list.

## Optional by design

Archetypes are an **enrichment layer, not a requirement**. If this folder holds only this README, `/process-workitem` runs generically — the generic frame is the day-one fallback. Archetypes store **per-type method, not per-item content**: they keep stories lean by holding reusable discipline once, instead of re-typing it into every story. An elaborately written story reduces, but never removes, their value — the method (reproduce-first, state-file safety, equivalence proof) is reusable across every story of that type.

## What is an archetype?

A *kind of work item* that has its own validation steps, planning rules, and common pitfalls. The router prompt (`commands/process-workitem.md`) classifies an incoming work item and dispatches to the matching handler here. An archetype is **two-sided**: `refinement-prep` reads its creation-completeness rules when a story is drafted, and `process-workitem` reads its execution rules when the story is picked up.

## Common archetypes

| Archetype | Handler addresses | Status |
|---|---|---|
| `bugfix` | Defect with a known symptom: reproduction, narrow fix, regression test | **Shipped (v0.1)** — `bugfix.md` |
| `column-add` / `schema-change` | Extending a table with new columns: source validation, type matching, downstream propagation | Example |
| `source-onboard` | Adding a new source system to the data platform | Example |
| `infra-change` | Modifying infrastructure: state-file safety, ordering, idempotency | Example |
| `doc` | Documentation updates: scope, placement, accuracy | Example |
| `refactor` | Restructuring without behaviour change: equivalence proof, test coverage | Example |
| `spike` | Investigation with no code deliverable: time-box, capture, decision | Example |
| `api-change` | Public API surface: versioning, deprecation, caller enumeration | Example |

`bugfix.md` ships as the day-one starter so `/process-workitem` has something to dispatch to. The rest are listed as starting points — write the ones your team actually needs.

## Adding a new archetype

When a kind of work shows up often enough to deserve its own rules:

1. Write the handler as `<archetype>.md` in this folder, with the frontmatter contract below.
2. Map its `board_type` to the team's concrete board signal in `context/tooling/board.md` (`## Archetype mapping`), if the team tags work-type on the board.
3. Use the handler in the next session and iterate from real output.

No router edit is needed — `process-workitem` globs this folder and builds the registry from frontmatter at runtime. The filesystem is the registry, the same way `process-transcript` discovers its specialists.

## Frontmatter contract

```yaml
---
archetype: <name>          # the handler's identity
board_type: <work-type>    # abstract work-type; concrete board signal is mapped per team in board.md
triggers: [<word>, ...]    # title/body words used for prose inference when no board type signal is present
when-not: "<one line: which neighbouring archetypes this work is NOT, and where to route instead>"
---
```

`process-workitem` resolves the archetype by reading the board's work-type signal first (via the `board.md` mapping), and falls back to `triggers` / `when-not` inference only when no signal is present.

## Handler shape

Each handler is a markdown file with sections for: when this archetype applies, **creation completeness** (what makes a story of this type complete — read by `refinement-prep`), validation requirements specific to this kind of work, planning rules, common pitfalls, and validation checklist additions.
