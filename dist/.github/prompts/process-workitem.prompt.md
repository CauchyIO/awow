---
description: "take a board work item from refinement to PR"
phase: seed
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "REQUIRED conventions drafted (Step 2 of /setup-awow)"
removes_pain: "the every-story-is-treated-the-same-regardless-of-type problem"
---

# /process-workitem — take a board work item from refinement to PR

You load a board work item, validate its inputs, plan the change, apply it, verify the result, and report back. The work-specific rules (what to validate, what to check at the end) live in the archetype handlers — read `{HUB}/.agents/commands/_workitem-archetypes/` if this repo has vendored them, otherwise `${CLAUDE_PLUGIN_ROOT}/commands/_workitem-archetypes/`. This file is the generic frame that wraps every archetype.

This is the **seed** shipped with awow v0.1 — the flow below is a sensible default, not a contract. Edit it to fit how your team actually works.

---

## Principles

- **Iterate on plans, not on production code.** The plan is cheap to change; the codebase is not.
- **Validate inputs before acting on them.** Assumed state is the most common cause of agent-driven bugs.
- **Trace work back to the story.** The work item is a user story shaped by the `user-story-template` skill. Its acceptance criteria and scope boundary define what the plan must cover and where it must stop.
- **Check in with the user before each irreversible step** — after validation, after planning, after verification.

---

## Flow

### 1. Load the work item

Resolve the ID via the team's board surface (per `{HUB}/context/tooling/board.md`), or read the local cache at `{PROJECT}/proposals/workitems/<id>.md`. Read it through the lens of `user-story-template.md`: title, body (what changes + why), tags, acceptance criteria if present, scope boundary if present, parent/children, recent comments.

Confirm to the user: title, state, number of children, the archetype you plan to route to.

**Check the dependency graph.** If the item carries `Blocked by` edges (native board links, a body `Blocked by:` line, or the `/project-plan` plan artefact), verify those predecessors are done before starting. If a blocker is open, surface it and ask whether to proceed anyway or pick an unblocked item — do not silently start work the plan says is gated.

**Stop condition.** If the story doesn't fit the template — vague title, missing tags, body that doesn't say what changes and why — stop. The fix is to repair the story against `user-story-template.md`, not to infer scope.

### 2. Classify and route

Match the story to an archetype registered in the archetype registry named above (common ones: `feature`, `bugfix`, `refactor`, `doc`; teams register others as their work demands). The archetype handler carries the work-specific rules.

**If the `_workitem-archetypes/` directory is empty** (apart from `README.md`), proceed generically: use the validation, planning, and verification rules from this file as-is, but tell the user no archetype was matched and suggest scaffolding one based on the work just classified. Capture the suggestion as a stub proposal at `{PROJECT}/proposals/archetypes/<name>.md` so the next cycle starts richer. Do not block on this — generic execution is the day-one fallback.

**If archetypes exist but none match**, the story is either too broad — split it — or a new handler is needed. Ask the user.

### 3. Validate inputs

The archetype handler says what to validate for this work type and what counts as a stop condition. Do those checks *before* any planning. Working from assumed state is the most common cause of agent-driven bugs.

If the handler doesn't specify checks, ask the user what "validated" means for this work and capture the answer back into the handler so the next run is deterministic.

Report findings to the user. If anything blocks, stop.

### 4. Plan

Draft a plan in `{PROJECT}/proposals/<work-item-id>.md` and get user approval before touching code. A workable shape:

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

Iterate on the plan with the user. Do not touch code or the board until approved.

### 5. Apply

Execute the plan. Don't drift — if scope needs to expand, raise it and amend the plan.

If your team uses output-placement tagging (story body vs. comment vs. knowledge base vs. code, per `{HUB}/context/team/conventions/REQUIRED/output-discipline.md`), respect it: a story is not allowed to absorb content that belongs in the knowledge base.

### 6. Verify

Run the checks the archetype handler defines. At minimum, for code changes: tests / build / lint pass; each AC has evidence; behaviour-affecting changes get a smoke check. Record the results in the plan's verification section.

If anything is red, stop and report.

### 7. Report

Open the PR with a link to the work item, summary of changes, and verification results. Update the work item (state + a comment recording session ID and commit SHA if the team has wired up that integrity link). Surface any manual follow-ups.

---

## Behavioural boundaries

- **Stay in scope.** The story defines it. Surface related work as separate proposals.
- **Never act on un-validated assumptions about state.**
- **The plan is the cheap-to-change artefact** — iterate there, not in production.
- **Don't gold-plate.** First story delivers the feature; observability, refactors, and docs are follow-up stories.
- **Follow the team's conventions** in `{HUB}/context/team/conventions/REQUIRED/*.md` (labels, branches, output discipline).
