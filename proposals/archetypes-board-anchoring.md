# Anchor work-item archetypes to board types and the creation flow

**Status:** proposed · **Date:** 2026-05-25

## Context

`_workitem-archetypes/` holds type-specific handlers (`bugfix`, and templates for `refactor`, `infra-change`, `spike`…) that `/process-workitem` dispatches to. Three observations surfaced while reviewing the structure:

1. **Archetypes are already optional** — `/process-workitem` Step 2 degrades to a generic validate/plan/verify frame when the folder is empty. Only `bugfix.md` ships. This is correct but **undocumented as a deliberate design property**; a reader sees a folder of handlers and assumes they're required.
2. **Archetype value is orthogonal to story quality.** A story carries the *what* (intent, AC, scope). An archetype carries the *method for that class of work* (bugfix → reproduce-first + regression test; infra-change → state-file safety, ordering, idempotency). Archetypes are DRY storage for per-type method, so stories stay lean — directly the `removes_pain` of `/process-workitem` ("every-story-treated-the-same-regardless-of-type").
3. **The archetype vocabulary and the board's type vocabulary are parallel but unlinked.** The `boards/` refs express work-type as a `type:` tag (`type:bug`, `type:documentation`; Azure: *"usually redundant with work-item type, optional"*), while the hierarchy axis (Epic/Feature/Story/Task) is *level*, not type. `/process-workitem` classifies by reading the story's **prose** (`bugfix.md` matches trigger words: *fix, bug, broken, regression*), not a board field. Nothing connects the archetype name to `type:bug` or to ADO's native Bug work-item-type. `/refinement-prep` (creation) has no concept of archetypes at all.

## Thesis — archetypes are the team's primary extension surface

`/process-workitem` is intentionally a **thin base**: one entry point, a generic validate → plan → verify frame, and a single shipped archetype (`bugfix`). The design intent is that the base is *not* where teams invest — `_workitem-archetypes/` is. The standing work for whoever processes items is **growing and refining their own archetypes**: capturing the discipline of each work type as it recurs, and letting an archetype **invoke other parts** of the stack (a verify pass, the design-system command, a board-skill automation) when that type of work warrants it.

This makes the command a "one entry, routed to the right type" shell whose value compounds with team-authored archetypes. It is the clearest example in awow of *the base ships minimal; the team extends it where their work actually differs.* Every change below should reinforce that the archetype folder is the **invitation to extend**, not a closed set.

## Proposal — three staged changes, smallest first

### Stage 1 — Document optionality, purpose, and the extension invitation (small; do first)

Sharpen `_workitem-archetypes/README.md` and `/process-workitem` so the design is explicit:

- Archetypes are an **enrichment layer, not a requirement**; generic execution is the day-one fallback.
- They store **per-type method, not per-item content** — they keep stories lean by holding reusable discipline once. An elaborate story reduces, but does not remove, their value.
- **This folder is where the team extends the base.** Say it plainly: the shipped `bugfix` is a starting point; the processing role's ongoing investment is authoring archetypes for the work types this team actually sees, and wiring them to invoke other commands/skills where useful.

No behaviour change. Pure documentation so the optionality, the trade-off, and the extension intent are legible without reading the prompt body.

### Stage 2 — Anchor archetypes to the board `type:` field (medium)

Today classification infers type from prose. Instead, let it **read the board** first and fall back to inference:

- Establish the convention that an archetype name corresponds to the board's work-type signal: the `type:<archetype>` tag (Linear/Jira/ADO) or the native work-item-type where the board has one (ADO "Bug").
- `/process-workitem` Step 2: read the work item's `type:` tag / work-item-type; if it names a registered archetype, route to it directly. Only fall back to trigger-word inference when the field is absent or ambiguous, and offer to stamp the field once classified.
- Record the mapping in the `boards/<tool>/reference/labels.md` (and `hierarchy.md` for ADO's Bug type) so `board.md` captures, per team, which `type:*` values map to which archetypes.

Result: the two vocabularies converge. Classification becomes a field read, not a guess; the board stays the source of truth for type.

**Open question for Stage 2:** for ADO specifically, do we map `bugfix` to a `type:bug` *tag* on a User Story (awow's current stance), or to ADO's native *Bug work-item-type*? The references currently prefer the tag and treat L3 as User Story / PBI. Picking the native type would diverge from that and needs a deliberate call.

### Stage 3 — Make archetypes two-sided so creation uses them too (larger; design)

Extend the archetype file shape from execution-only to **creation + execution**:

- *Creation rules:* what makes a *complete* item of this type (bug → repro steps, expected vs. actual; infra → blast radius, rollback). `/refinement-prep` reads these and checks drafts against them, on top of its current type-agnostic quality bar.
- *Execution rules:* the validation/planning/pitfall sections `/process-workitem` already consumes.

Both routers then share one type vocabulary: `/refinement-prep` stamps the type and enforces type-specific completeness at creation; `/process-workitem` reads it at execution. Requires a handler-shape change and updates to both commands — propose as its own follow-up once Stage 2 lands.

## Demo — show "extend the base by authoring an archetype" (open)

This is the cleanest use case to demo: a team meets a new work type, authors an archetype for it, and watches `/process-workitem` route to it. The compelling beat is the *authoring*, not the processing.

**Blocker:** a board-driven demo of `/process-workitem` needs committed issues to route, and we are not currently committing issues to a board. So the archetype choice for the demo is undecided on purpose. Candidate directions, none chosen yet:

- **Self-referential:** treat awow's own maintenance work (e.g. the recent flatten / rename) as the work items, and author an archetype (`prompt-change`? `repo-restructure`?) for them.
- **Dogfood proposals as items:** the `dogfood/proposals/` set could seed realistic items to classify.
- **Authoring-only demo:** show writing a new archetype and dry-running classification against a sample story, sidestepping the need for a live board.

Resolve the demo once we decide whether (and where) issues get committed. Tracked here so it isn't lost; not gating Stages 1–3.

## Sequencing

Stage 1 is safe to land now. Stage 2 is the substantive value (vocabularies converge) and depends on a per-board mapping decision. Stage 3 is a separate design effort gated on Stage 2. The demo depends on the issue-committing decision, independent of all three stages.

## Out of scope

- Renaming any archetype or command.
- Changing the hierarchy (Epic/Feature/Story/Task) model.
- Auto-creating board items of any type without approval.
