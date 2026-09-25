---
description: "Use when the user points at a board item — a ticket ID, issue link, or “let's pick up X” — and wants it explained, refined, planned, or carried through a code change to an opened PR."
autofire: true
argument-hint: "<item-id> [explain | refine | plan | implement]"
phase: seed
layer: team
prerequisites:
  - "A board connected (/setup-awow) — the agent can read the board; writing it is needed from refine depth on"
  - "REQUIRED conventions present, or drafted on first need"
removes_pain: "the every-story-is-treated-the-same-regardless-of-type problem"
---

# /process-workitem — take a board work item as far as the request asks

You load a board work item and carry it to the depth the user asked for: explain it, refine it, plan the change, or build it through to an opened PR. The full flow validates inputs, plans, applies, verifies, reviews, and reports. The work-specific rules (what to validate, what to check at the end) live in the archetype handlers. Build the registry by overlay: start from the shipped set — `{ANCHOR}/.agents/commands/_workitem-archetypes/` if this repo has vendored it, otherwise `${CLAUDE_PLUGIN_ROOT}/handlers/_workitem-archetypes/` — then lay `{ANCHOR}/context/team/workitem-archetypes/` (excluding `README.md`) over it, where a same-named team file replaces the shipped handler and a new name registers a new archetype. This file is the generic frame that wraps every archetype.

This is the **seed** shipped with awow v0.1 — the flow below is a sensible default, not a contract. Edit it to fit how your team actually works.

---

## Principles

- **Iterate on plans, not on production code.** The plan is cheap to change; the codebase is not.
- **Validate inputs before acting on them.** Assumed state is the most common cause of agent-driven bugs.
- **Trace work back to the story.** The work item is a user story shaped by `story-shape.md`, bundled with the `workitem-write` skill. Its acceptance criteria and scope boundary define what the plan must cover and where it must stop.
- **Check in with the user before each irreversible step** — after validation, after planning, after verification.

---

## Depth — do as much as was asked, no more

Settle the depth from the user's words before step 1, and name it in your first reply. The depth fixes which steps you run and what you may write.

| The user asks you to | Depth | Steps you run | You may write |
|---|---|---|---|
| explain, summarise, "what is PAY-42?", "is it blocked?" | `explain` | 1, then answer | nothing |
| refine, tighten, "is PAY-42 ready to pick up?" | `refine` | 1–2, then 2a | the work item, through `workitem-write` |
| plan, "how would we do PAY-42?" | `plan` | 1–4 | the plan file, and nothing else |
| implement, build, fix, pick up, "do PAY-42" | `implement` | 1–8 | code, the PR, the work item |

- **No depth named → ask.** When the request is a bare ID or link, run step 1 at `explain` depth, then ask which depth the user wants, naming the four in one line — `explain`, `refine`, `plan`, `implement` — and which of them the item itself allows. Never read a bare ID as `implement`.
- **Go deeper only on the user's word.** Finish the requested depth, offer the one next depth in one line — never a menu of depths — and stop. A yes to that offer is the request for the next depth; resume from the step you stopped at.
- **`explain` changes nothing.** Write no file, branch, plan, comment, board field, or state move — not even a state move `board.md` assigns to you.
- **At `explain` depth a problem is a finding.** Report an open blocker, a missing archetype, or a story that does not fit the template; do not stop on it and do not repair it.
- **Creating an item, or changing one field on one, is not a depth.** Run the `workitem-write` skill for that and stop.

---

## Flow

### 1. Load the work item

Resolve the ID via the team's board surface (per `{ANCHOR}/context/tooling/board.md`), or read the local cache at `{PROJECT}/proposals/workitems/<id>.md`. Read it through the lens of the story shape (`story-shape.md`, bundled with the `workitem-write` skill): title, body (what changes + why), tags, acceptance criteria if present, scope boundary if present, parent/children, recent comments.

**Resolve the target first.** Settle which installation and which board this is — including when `board.md` is absent or names several boards — with the `board-target` skill, before the first board read. Do not restate its rules here.

Confirm to the user: title, state, number of children, the archetype you plan to route to.

**Check the dependency graph.** If the item carries `Blocked by` edges (native board links, a body `Blocked by:` line, or a plan artefact written by `awow-workflows`' `/project-plan`), verify those predecessors are done before starting. If a blocker is open, surface it and ask whether to proceed anyway or pick an unblocked item — do not silently start work the plan says is gated.

**Stop condition (`plan` and `implement` depth).** If the story doesn't fit the template — vague title, missing tags, body that doesn't say what changes and why — stop. The fix is to repair the story against the story shape — offer `refine` depth — not to infer scope.

### 2. Classify and route

Match the story to an archetype registered in the overlaid registry built above (common ones: `feature`, `bugfix`, `refactor`, `doc`; teams register others in `{ANCHOR}/context/team/workitem-archetypes/` as their work demands). The archetype handler carries the work-specific rules.

**If the registry is empty** (apart from `README.md`), proceed generically: use the validation, planning, and verification rules from this file as-is, but tell the user no archetype was matched and offer, in one line, to scaffold one based on the work just classified as a stub proposal at `{PROJECT}/proposals/archetypes/<name>.md`. Write the stub only on the user's yes — it is never part of the depth's own writes; once the team approves it, it lands in `{ANCHOR}/context/team/workitem-archetypes/` so the next cycle starts richer. Do not block on this — generic execution is the day-one fallback.

**If archetypes exist but none match**, the story is either too broad — split it — or a new handler is needed. Ask the user, and proceed generically meanwhile; offer the stub as above and write nothing for it without a yes.

### 2a. Refine — `refine` depth only

Repair this one item against `story-shape.md`, bundled with the `workitem-write` skill: a title that says what changes, a body that says what and why, acceptance criteria, a scope boundary. Right-size it so a single session can ship a working PR — 1–5 files, 2–3 sentences to describe, five or fewer acceptance criteria — and propose a split when it fails.

Surface a missing specific as an open question; do not invent it. Write the repaired item through the `workitem-write` skill, whose board plan shows the before and the after.

Refine the item in hand only. Breaking a feature or a brief into several stories is `/refinement-prep` in the optional `awow-workflows` plugin; when it is absent from your skill listing, say so and name the plugin.

### 3. Validate inputs

The archetype handler says what to validate for this work type and what counts as a stop condition. Do those checks *before* any planning. Working from assumed state is the most common cause of agent-driven bugs.

If the handler doesn't specify checks, ask the user what "validated" means for this work and capture the answer into the team's copy of the handler under `{ANCHOR}/context/team/workitem-archetypes/` (creating it from the shipped one if needed) so the next run is deterministic.

**Stay inside this repo and its anchor.** Read `{PROJECT}`, `{ANCHOR}` and the board the `board-target` skill resolved, and nothing else: no other checkout on this machine, no sibling directory, no board's document library, however promising. A document the story references that is not in those places is a finding to report — "the design doc is not in this repo or the anchor" — never a search.

Report findings to the user. If anything blocks, stop.

### 4. Plan

Write the plan to `{PROJECT}/proposals/<work-item-id>.md` — at `plan` depth that file is what the user asked for, so write it without asking first, and never leave the plan in chat only. Get the user's approval of the plan before touching code. A workable shape:

```markdown
# <Work-item ID> — <title>

**Archetype:** <name>
**Status:** PROPOSAL — awaiting approval

## Story anchor
- What changes / why (one line)
- Acceptance criteria the plan covers
- Out-of-scope items

## Plan
- `path/to/file.ext` — what changes (function / section name; line range only when it sharpens intent)
- `path/to/new.ext` — new file, summary of contents
- Story body / comments / knowledge base writes, if any

## Risks
- <risk> — <mitigation>

## Verification
- Command, manual check, AC mapping
```

The plan should be **specific enough that another developer could execute it without ambiguity** — not specific as ceremony. Granularity that lets a reader find the right spot is enough; line numbers go stale during iteration.

**The architecture plane — only where one is declared.** Read `{ANCHOR}/context/tooling/architecture.md`. No such file → skip this paragraph silently; say nothing. It names the plane:

```
adr_dir:      <path to ratified decisions, may be empty>
pattern_dir:  <path to durable pattern notes, may be empty>
kb_agent:     <retrieval tool handle, e.g. an ask_brain-style MCP — or "none">
strictness:   stop-and-surface | warn-only
```

Query the governing decisions and patterns with the plan's *domain nouns* — specificity is the biggest lever on recall — through `kb_agent`, or by reading the named `adr_dir` / `pattern_dir` when it is `none`. Nothing on disk is a no-op. **Never invent** an ADR or pattern that is not there. Then:

- **Flag** the specific plan tasks that touch a governed surface, in the plan itself — step 5 re-checks those and no others.
- **Conflict** with a ratified decision or established pattern → do not proceed silently. Surface it concretely — the id, the file path, the specific contradiction — and seek human reconciliation. `strictness: warn-only` downgrades this to a warning the user can wave through.
- **Alignment** → cite **"checked against: <the decisions and patterns you actually retrieved>"**. Never write "no conflicts found": that claims a completeness retrieval cannot give you. The citation states the scope of the check, not a guarantee.

Iterate on the plan with the user. Do not touch code or the board until approved.

At `plan` depth the approved plan is the deliverable: stop here. When you ask for approval, say what it does — you set the plan file's status to `APPROVED`, and it becomes what `implement` depth builds from; approval writes nothing to the board.

### 5. Apply

When work starts, move the item to In Progress through the `workitem-write` skill, with a dated comment naming the branch and the approved plan. Every state move carries its comment.

Execute the plan with the harness's own coding capability — yourself, or a coding subagent when the harness offers one. Hand over the approved plan and the story's acceptance criteria, never the bare ID.

Don't drift — if scope needs to expand, raise it and amend the plan. Re-check the tasks step 4 flagged against the architecture plane as you reach them — those only, carried by the plan, never a blind per-task query.

If your team uses output-placement tagging (story body vs. comment vs. knowledge base vs. code, per `{ANCHOR}/context/team/conventions/REQUIRED/output-discipline.md`), respect it: a story is not allowed to absorb content that belongs in the knowledge base.

### 6. Verify

Run the checks the archetype handler defines. At minimum, for code changes: tests / build / lint pass; each AC has evidence; behaviour-affecting changes get a smoke check. Record the results in the plan's verification section.

If anything is red, stop and report.

### 7. Review

Review the full diff before you deliver it. Use the harness's code-review capability when it has one; otherwise read the diff yourself against the plan, the acceptance criteria, and the team's conventions.

Fix what the review finds, or list it as a follow-up. Record in the plan who or what reviewed and what it found; write `not reviewed` when no review ran.

Never call code reviewed because its tests pass. This review comes before hand-off and does not replace the team's review of the PR.

### 8. Report

Open the PR with a link to the work item, summary of changes, verification results, and the review record from step 7. Update the work item through the `workitem-write` skill — the state move (agent-owned where `board.md` says so, gated otherwise) and a comment recording session ID and commit SHA if the team has wired up that integrity link. Surface any manual follow-ups.

---

## Behavioural boundaries

- **Stay at the requested depth.** The user's words set it; only the user deepens it.
- **Stay in scope.** The story defines it. Surface related work as separate proposals.
- **Never act on un-validated assumptions about state.**
- **Never read outside this repo, its anchor and its board.** A missing reference is a finding, not a hunt across the machine.
- **The plan is the cheap-to-change artefact** — iterate there, not in production.
- **Don't gold-plate.** First story delivers the feature; observability, refactors, and docs are follow-up stories.
- **Follow the team's conventions** in `{ANCHOR}/context/team/conventions/REQUIRED/*.md` (labels, branches, output discipline).
