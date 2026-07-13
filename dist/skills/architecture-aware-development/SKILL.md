---
name: architecture-aware-development
description: "The seam between awow's lifecycle and the architecture plane — ratified ADRs, solution-design records, and durable pattern notes, consulted through a KB agent. The sibling of board-aware-development: it rivets a KB-alignment action onto each inner-loop lifecycle moment — brainstorming → prior-art reuse, writing-plans → align + flag governed tasks, executing → re-check the flagged tasks. Opt-in and config-gated: it does nothing unless the repo declares an architecture plane in {PROJECT}/context/tooling/architecture.md. Read or invoke this when a build engine is present, that pointer exists, and you are forming a plan — so the plan reuses settled decisions and does not silently contradict a ratified ADR. The PreToolUse hook fires the matching one-line reminder automatically; this skill is the full crosswalk behind it."
---

# Architecture-aware development

awow keeps the agent honest against the **board plane** (`board-aware-development`) — *what* to build.
This is the second plane: *how we have already decided to build* — ratified ADRs, solution-design
records, durable pattern notes. In repos that run a retrieval agent over that knowledge, it is queryable
in one call. Bind it to the lifecycle the same way: each design/plan moment rivets onto a KB-alignment
action.

This is **opt-in and config-gated.** It does nothing unless the repo declares an architecture plane.

## Plane check first (graceful no-op)

Read `{PROJECT}/context/tooling/architecture.md`. It names the plane:

```
adr_dir:      <path to ratified decisions, may be empty>
pattern_dir:  <path to durable pattern notes, may be empty>
kb_agent:     <retrieval tool handle, e.g. an ask_brain-style MCP — or "none">
strictness:   stop-and-surface | warn-only
```

- **No pointer** → do nothing, silently. (The hook will not even nudge.)
- **`kb_agent: none`** → fall back to reading the named `adr_dir` / `pattern_dir` directly; nothing on
  disk → no-op.
- **Never invent** an ADR or pattern that is not there.

## The crosswalk

| Engine skill (the moment) | Architecture action |
|---|---|
| `brainstorming` | **Prior-art probe**, folded into the existing "go to the board" beat — *not* a second ritual. Ask the KB agent: does an ADR / design / pattern already cover this? If yes, reuse or extend it rather than designing from scratch. Keep it light; the start edge stays whisper-thin. |
| `writing-plans` | **Align + flag.** Query the governing ADRs/patterns with a query built from the plan's *domain nouns* (specificity is the biggest lever on recall), then flag the specific plan tasks that touch governed surfaces. |
| `executing-plans` / `subagent-driven-development` / `test-driven-development` | **Re-check the flagged tasks only** — carried by the plan, not a blind per-task query. |

Completion-edge skills (`verification-before-completion`, `requesting-code-review`,
`finishing-a-development-branch`) stay board-only — architecture alignment is a design/build concern.

## On what you find

- **Conflict** with a ratified ADR or established pattern → **do not proceed silently.** Surface it
  concretely — the ADR id + file path + the specific contradiction — and seek human reconciliation. This
  is a *disposition*, not a technically enforced gate; `strictness: warn-only` downgrades it to a
  warning the human can wave through.
- **Alignment** → cite **"checked against: [the ADRs/patterns you actually retrieved]"**. Never write
  "no conflicts found" — that falsely implies completeness. The citation claims *scope of check*, not a
  global guarantee. A retrieval miss is possible: this reduces architecture-blindness, it does not
  eliminate it.

## Query tooling

Use the cheap retrieval call (e.g. `ask_brain`) for the prior-art probe and the per-part re-checks.
Escalate to the deeper, server-synthesised call (e.g. `ask_brain_ultra`) for the single plan-time
alignment, or whenever the cheap evidence is thin/ambiguous on a *potential conflict* — do not stop, or
wave through, on weak evidence.

## When NOT to apply this

- No `{PROJECT}/context/tooling/architecture.md` pointer — there is no plane to consult; stay silent.
- No inner-loop engine installed — there is no lifecycle seam to bind.
- The work is not an initiative — skip it, like the board check.
- You are inside `/process-workitem` — that command owns the seam; do not double-apply.
