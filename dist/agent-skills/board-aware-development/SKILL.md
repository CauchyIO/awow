---
name: board-aware-development
description: "The seam between awow's board-linkage discipline and an inner-loop build engine (superpowers, spec-kit). Rivets each board state transition onto the lifecycle skill that already fires at that moment — brainstorm → ticket, writing-plans → acceptance criteria + knowledge-base link, verification-before-completion → the gate before In Review/Done, requesting-code-review → In Review, finishing-a-development-branch → Done. Read or invoke this when a build engine is present and you are working a real initiative directly (outside /process-workitem), so the board stays current as a byproduct rather than a chore. The PreToolUse hook fires the matching one-line reminder automatically; this skill is the full crosswalk behind it."
---

# Board-aware development

awow keeps the board current; an inner-loop engine (superpowers, spec-kit) supplies the build rigor. They overlap at the lifecycle, so bind them: each board state transition rivets onto the engine skill that *already* fires at that moment. You do not "remember to update the board" — the skill invocation is the cue.

This is the **ungated path**. `/process-workitem` already owns the seam when you go through it (see `{PROJECT}/proposals/superpowers-integration-plan.md`). This skill covers the common case where you invoke an engine skill *directly* — `brainstorming`, `verification-before-completion`, `finishing-a-development-branch` — without the command. That is exactly where board tracking falls through today.

## The crosswalk

| Engine skill (the moment it fires) | Board action riveted to it |
|---|---|
| `brainstorming` (creative work starting) | This is your board moment. No ticket and it is an initiative → the brainstorm output is your `{PROJECT}/proposals/` draft → approve → create (`/feature`, `/bugfix`, `/spike`). Ticket exists → move it to **In Progress**. |
| `writing-plans` (a spec exists) | Link the plan to the ticket: intent + acceptance criteria in the body, durable rationale to `{HUB}/context/knowledge-base/`. |
| `executing-plans` / `test-driven-development` / `subagent-driven-development` | Ticket is **In Progress**; comment findings and blockers *as you go*, not at the end. |
| `systematic-debugging` | An initiative with no ticket → open one (`/bugfix`, `/incident`); the root cause goes in a comment. |
| `verification-before-completion` | Gate: do **not** move the ticket to In Review/Done until verification evidence exists. Paste the evidence into a comment. |
| `requesting-code-review` | Move the ticket to **In Review** with the "what to review" comment. |
| `finishing-a-development-branch` | Land the PR, move the ticket to **Done**, link the PR, close with a one-line outcome comment. |

## Two cleanups this resolves

- **Brainstorm and board-check are one beat.** The engine routes initiatives through `brainstorming` before planning; awow says go to the board before any initiative. Same moment — do not run them as two separate rituals. When `brainstorming` fires for an initiative, that is your board-linkage moment.
- **Verification gates the board, not just the claim.** `verification-before-completion` already blocks "it's done" without evidence. Extend the same gate to the board: In Review and Done are unreachable until that evidence exists.

## Inherit the initiative gate

This crosswalk fires only for *initiatives* — the same `using-awow` gate. A `brainstorming` over a throwaway, a `systematic-debugging` of a one-line typo fix the user named: no ticket. Rule of thumb unchanged: would a teammate reasonably expect to find this on the board next week? Enforce at the completion edge (verify / review / finish); stay whisper-thin at the start edge — awow rolled back an earlier over-anchoring (`{PROJECT}/proposals/archetypes-board-anchoring.md`), so do not turn the start of work into ceremony.

## When NOT to apply this

- No inner-loop engine is installed — `using-awow` alone governs; there is no seam to bind. superpowers is the recommended optional engine; offer it via `/setup-awow` (Step 8, surface the extras), never force it.
- The work is not an initiative — skip the board entirely.
- You are inside `/process-workitem` — that command already owns the seam; do not double-link.
