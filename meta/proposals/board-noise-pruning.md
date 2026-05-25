# Proposal — noise control for an AI-heavy board

**Status:** Draft (solutioning) — comparison-mode, not yet a recommended plan. The body enumerates approaches per dimension with pros/cons so we can pick before writing the issue.

---

## Look-first check (done)

- `ls proposals/` — no existing proposal covers board noise / pruning / staleness.
- `grep -ni "noise\|prune\|stale\|dedup\|provenance" proposals/*.md` — only incidental hits (`plugin-distribution.md`, `session-board-correlation.md`); neither addresses this concern.
- The existing rule in `.agents/CLAUDE.md` "Before starting a new initiative" partly covers the create-time gate, but does not name the failure mode (noise accumulation) and does not bind to `context/tooling/board.md` strongly enough to survive AI-heavy use.

---

## Problem

When most board writes go through an AI agent, two failure modes accumulate:

1. **Speculative or duplicate stories filed too eagerly.** The agent reads a few files, identifies a "gap", and files. Some are real; many are speculation dressed as work items, or duplicates of issues that already exist under different wording.
2. **Stale stories that no one prunes.** Real at the time, no longer real or no longer relevant, but they keep occupying board slots and skew any "what's outstanding?" view.

The two compound. The noisier the create flow, the more pruning surface there is downstream. Observed by Casper in adopter work and in our own company.

---

## Dimensions

- **A. Prevent at create time** — upstream gate.
- **B. Detect noise mid-stream** — find low-quality items after creation.
- **C. Clean up stale items** — periodic pruning of items that aged out.

Working hypothesis (to validate): **A is load-bearing**. B and C are partial recoveries that depend on A being weak. If A is tight, B and C may not be needed. Casper has signalled that C-style mechanisms (age-out, auto-archive) are not promising; this proposal records the C options for completeness but does not push them.

---

## A. Prevent at create time

### A1. Strict routing convention bound to `context/tooling/board.md` (Casper's preferred direction)

Tighten the existing "Before starting a new initiative" section in `.agents/CLAUDE.md` so the rule:

- Names the team's actual board surface explicitly, substituted in by `tools/bootstrap-claude-md.py` from `context/tooling/board.md` ("search Linear via the `linear-server` MCP using `list_issues` with these filters", not "search the board").
- Lists the exact search calls the agent must run before drafting a proposal.
- Restates the proposal-first principle at the create step: no `issue create` / `save_issue` without an approved proposal under `proposals/`.
- `/setup-awow` Step 1 (already writes `context/tooling/board.md`) gains an explicit "board read/write surface" section that the bootstrap script reads — so this is wired, not hand-edited per team.

Pros:
- Single rule, no new taxonomy.
- Already half-shipped — the stub exists; this sharpens it and binds it to `board.md`.
- Same enforcement model as the rest of awow (convention + bootstrap), no new infra.
- Stays inside the existing surfaces (`.agents/CLAUDE.md`, `context/tooling/board.md`, `/setup-awow`).

Cons:
- Still depends on the agent obeying the rule mid-session. LLMs drift, especially on long sessions.
- Doesn't address the "agent honestly believes this is a new initiative, but isn't" case — convention can't catch what the agent doesn't notice.
- Strength depends on `tools/bootstrap-claude-md.py` being real and reliable; status in v0.1 needs to be confirmed.

### A2. Mandatory look-first evidence in every proposal

Every `proposals/<name>.md` must include a `## Look-first check` block with the actual search-call output. The `session-board-correlation` proposal already does this; promote the pattern to a template (`proposals/_template.md` or `.agents/skills/user-story-template.md`).

The human approving the proposal sees the evidence before signing off; absent or empty evidence is a soft block.

Pros:
- Auditable — the search calls are in the file.
- Promotes an existing pattern; no new mechanism.
- Catches the largest noise class (duplicates) specifically.

Cons:
- Agent can still cherry-pick search terms.
- Adds friction the user might not want for small / obvious tickets — would need an explicit "trivial" exemption.

### A3. Confidence bar — write AC or don't file

Hard rule: the agent may not file an issue unless it can write acceptance criteria right now. If it can't, the work stays as a proposal until it can. Promote the "no AC, no ticket" line from style to gate.

Pros:
- Forces the agent to demonstrate the work is real before it occupies a board slot.
- AC quality is human-checkable from the proposal.

Cons:
- Agents are good at confabulating plausible AC — can paper over speculative work with realistic-sounding bullets.
- Some real tickets land without AC (spike, investigation); needs an explicit `type:spike` exemption.

### A4. Human-in-the-loop create gate (per turn)

The agent never runs `issue create` / `save_issue` without explicit user approval in the same turn ("file this"). Already partially in `.agents/CLAUDE.md` ("never write directly to the board... without human approval"); make it a hard rule with no escape, named at the create step.

Pros:
- Tightest gate. You cannot get noise if every create is approved.
- No new taxonomy, no new skill.

Cons:
- Friction. If the user is delegating board work to the AI specifically because they want volume, demanding per-create approval defeats the point.
- The rule already exists in soft form — if it's slipping, the failure mode is interpretation, not absence. Reword rather than re-add.

### A5. Provenance label (`origin:agent`)

The "tag everything AI-filed" option. Casper's objection: humans can still interact with tagged items, so the boundary is muddy.

Pros:
- Surgical for downstream filtering (any cleanup skill targets only `origin:agent` items).
- Cheap at create time.

Cons (Casper's point):
- Humans editing AI-filed tickets blur the provenance — the label becomes a soft truth.
- Introduces a new taxonomy axis to maintain across all four board references (`linear`, `azure-devops`, `jira`, `github-issues`).
- Doesn't prevent noise, only sorts it.
- Possible replacement: use the session footer from `session-board-correlation` as the provenance signal — it's in the body, not the label, and reflects "who first filed" even after a human edits.

### A6. Drafts surface (separate inbox project)

The agent files into a `Drafts` project / inbox, never the active board. Humans promote.

Pros:
- Hard separation; the active board is human-curated.
- Active-board metrics stay clean.

Cons:
- Duplicates the purpose of `proposals/` — why have both?
- Another surface to maintain; against awow's "fewer surfaces" instinct.
- Re-introduces A4's friction in a different shape (humans now have a promote step).

---

## B. Detect noise mid-stream

### B1. Weekly digest extension

Extend `/weekly-digest` with a "recent agent-filed items, no state change in N days" section.

Pros:
- Reuses an existing skill; one extra section, no new command.
- User already runs the digest weekly.

Cons:
- Lumps activity reporting with noise-detection; user may skim past.
- Depends on a provenance signal (A5 or session-footer) to filter; otherwise surfaces human-filed items too.

### B2. Pair-review skill

A `/board-review` skill that, on demand, walks the user through recent agent-filed stories with keep / kill / promote actions.

Pros:
- Catches the noise close in time, when context is fresh.
- User-triggered, no automation risk.

Cons:
- One more skill to remember to run.
- If the user is heavy in the AI loop, they may not pause to review.

---

## C. Clean up stale items

Casper flagged C as not promising. Recording the options briefly so the rejection is on the record.

### C1. Age-out convention + manual pruning ritual

Define "stale" by movement age; surface stale items in a periodic prune skill. Rejected — Casper's concern (paraphrased): the heuristic is brittle and risks closing items that were quietly real but waiting on something the heuristic can't see.

### C2. Snooze label

A `state:snoozed` label with a wake-up date. Decoupled from staleness. Useful only if a real "not now, but real" class of items appears in practice; otherwise overkill.

### C3. Do nothing in C

Accept some board cruft as the cost of an AI-heavy create flow. If A is tight, C may be unnecessary.

---

## Open questions

1. **Is the right move just A1 + A2 — hard and explicit — and skip B and C?** That is the smallest change consistent with the existing awow design (convention + `/setup-awow` bootstrap + proposal-first).
2. **What does `/setup-awow` Step 1 need to add to `board.md`** to make A1's substitution work? Likely: the exact MCP tool names, the search-call shape, and the create-call shape, so the bootstrapped CLAUDE.md can inline them per team.
3. **Is A4 actually slipping in practice, or just being misread?** Worth tracing one heavy-board session (via `/awow-usage-coach` or `mlflow-export` + manual read) to see what the agent did before each `issue create`. If the approval was implicit but absent, the rule needs a tighter phrasing, not a new mechanism.
4. **If we want any provenance signal, does the session footer from `session-board-correlation` replace the need for A5?** It's body-anchored, harder to muddy, and that proposal is already in flight.
5. **Status of `tools/bootstrap-claude-md.py` in v0.1.** A1's enforcement depends on it. `.agents/CLAUDE.md` says it runs after `/setup-awow` Steps 0–4; need to confirm whether it's real or stub. If stub, A1 splits into two issues (implement bootstrap, then tighten the rule).
6. **Per-tool reference docs.** A1 implies the four `context/tooling/boards/<tool>/reference/` sets each need a section the bootstrap can read for the "search call" and "create call" inlining. Is that scope inside this proposal or a separate one?

---

## Suggested next step (pick one)

- **Narrow.** Commit to A1 + A2. Write the exact `.agents/CLAUDE.md` edits, the proposal template addition, and the `/setup-awow` Step 1 changes. File one issue. Smallest change, highest leverage.
- **Wide.** Decide A vs B vs C strategy first in a follow-up conversation, then write a per-approach proposal.
- **Trace-first.** Before deciding, run `/awow-usage-coach` against one heavy-board session (or a sibling repo as stand-in) to see where the agent actually generates noise. Fix what the trace shows, not what we think the failure modes are. Recommendation if forced to one — the cost of guessing wrong here is more rules nobody follows.

Casper to pick.
