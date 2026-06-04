# Make the board current as a byproduct of working — low-friction linkage, not state-injection

**Status:** DRAFT — awaiting approval · **Date:** 2026-05-30

## Outcome (intended)

Developers still go to the board — to see priorities, pick up work, get the overview. They always will, and that is fine. What changes is that they stop carrying the **decision burden of board hygiene**: *"Should this be an issue? Should I make it now? Does one already exist? What state is it in?"* The agent works that out for them — links what they're doing to the right work item, proposes one when nothing fits, and keeps it moving as the work lands, saying so in one line. *"Board as afterthought"* is a figure of speech for **that relief** — the housekeeping decisions fade into the background — not a claim that the board disappears or that anyone stops looking at it. This makes the mission (`README`: *"agents maintain the plan … so people can spend their time on judgement, not coordination"*) concrete for the single session: the *coordination overhead* is what lifts, not the board.

## Context

Three facts about awow today shape this:

1. **The discipline already exists, as a soft instruction.** `.agents/CLAUDE.md` → *"Before starting a new initiative … go to the board first"* (look → propose → update through the lifecycle). It is correct but **front-loaded and one-directional**: it fires at the *start* of an initiative and says little about keeping the item current *as work lands*, or about doing so with low ceremony.

2. **awow already runs a SessionStart hook.** `.claude/settings.local.json` wires `session-correlation/scripts/session_env_hook.py`, opt-in via `/setup-awow`. So an *ambient* board line is not new infrastructure — it is a sibling of an existing, accepted pattern, installed the same way.

3. **`context/tooling/board.md` is the single board pointer.** Any board access — by agent (MCP) or by script (`gh`/API) — resolves through it. A hook can read it to learn the adapter, but **a shell hook cannot call MCP**; its only query path is the CLI/API surface.

### Why not the obvious design (inject board state at session start, scoped by branch)

We explored and **rejected** "SessionStart hook injects the issues relevant to you." Two reasons, both load-bearing:

- **The signal doesn't exist yet at session start.** SessionStart fires *before* any interaction, so it cannot know what you're about to work on. Any answer is a guess from stale metadata.
- **Branch is a *convenient* signal, not a *true* one.** A dev may sit on one branch for a month, or on `main`. Scoping by branch forces branch-discipline onto the human so the *tool* has something to read — the tail wagging the dog, and it reintroduces exactly the housekeeping burden we are trying to lift. Scoping by *assignee* ("all your open issues") is the other failure mode: a firehose every session.

The true relevance signal is **the interaction itself** — what the user asks for, as it unfolds. That is semantic, and reading it is the agent's strength, not a script's.

## Thesis — split the capability by what each layer is good at

| Layer | Fires | Knows | Built as |
|---|---|---|---|
| **Ambient floor** | session start | only cheap, always-true facts (cycle deadline, open count) | deterministic hook |
| **Intent linkage** | when an initiative surfaces in the conversation | what you're actually doing | agent discipline |
| **Background reconciliation** | as edits/commits land | what changed | agent discipline |

The value lives in rows 2–3, and **neither is a hook** — they are prompt/discipline engineering, because judging "is this a new initiative, which item is it" requires reading the conversation. The hook stays whisper-thin and makes *no claim* about what you're doing, which is exactly why it is safe and cannot create friction.

This keeps the build light (most of it is words, not code), portable (discipline works in IDE-Copilot too, where hooks don't reach), and impossible-to-slow-you-down (the heavy part runs *as* you work, not before you start).

## Proposal — three stages, smallest first

### Stage 1 — Sharpen the board-linkage discipline (small; pure prose; do first)

The whole value, expressed as instruction. `output-discipline.md` is the wrong home — it governs *how to write a body*, not *whether/when to create and link an item*. So this lands as a new durable convention, `context/team/conventions/REQUIRED/board-linkage.md`, with the operative copy added to the *"Before starting a new initiative"* block in `.agents/CLAUDE.md` (which `bootstrap-claude-md.py` + `gather.py` propagate once `/setup-awow` runs — a follow-up, since bootstrap is a v0.1 skeleton today). Both written in agent-directive voice (`.agents/skills/agent-directive-voice.md` — second-person imperative). The rules:

- **You own the "is this worth an issue, and when" judgment — not the developer.** The existing heuristic (*"would a teammate reasonably expect to find this on the board next week?"*) is yours to apply proactively as work unfolds. Do not push the decision back to the user with *"shall I make an issue for this?"* — make the call, act on it, and tell them what you did. The developer should never have to stop and wonder whether now is the moment to open a ticket.
- **Relevance comes from what the user asks, not from the branch or the session.** Do not infer the unit of work from the current branch — a developer may sit on one branch, or on `main`, for weeks. Read intent from the conversation.
- **Link just-in-time and scoped.** When a discernible initiative surfaces, query the board *then* — scoped to that intent — to find the matching item or propose one. Do not pre-load the board; do not pull "everything assigned to me."
- **Surface it in one line, low ceremony.** On linking or proposing, tell the user briefly — *"tracking this under AWOW-42"* — and move on. No menu, no confirmation ritual unless creating a new item.
- **Keep it current as you work (the new half).** As edits and commits land, move the item's state forward and drop a one-line comment when there is a finding or blocker — *without being asked*. The board updates as a byproduct. (Bounded by the existing `Board output rules`: minimum useful body, status → comment, durable → knowledge base.)

No new code, no behaviour gated on tooling, works in every harness including IDE-Copilot. This is the floor and the bulk of the value.

### Stage 2 — Ambient board line via SessionStart hook (small; deterministic; opt-in)

A new opt-in `board-state` capability, built as a sibling of `session-correlation`:

- **Script:** `.agents/skills/board-state/scripts/board_state_hook.py`. Reads the pointer from `board.md`, makes **one** cheap query (current cycle + its end date, count of the user's open items), emits a single line via the SessionStart `additionalContext` contract. Platform-detect the JSON shape (`hookSpecificOutput.additionalContext` for Claude Code, top-level `additionalContext` for Copilot CLI, `additional_context` for Cursor) so it is portable beyond Claude Code.
- **No per-issue fetch, no branch logic, no semantic guessing.** Exactly one ambient line: *"Cycle 7 ends Fri (6d) · 3 of your issues open."*
- **Background + bounded.** `async: true` so it never blocks the turn; hard timeout (~3s); on miss, emit nothing or cache.
- **Cache** to gitignored `.awow/board-cache.json`, 15-min TTL — the matcher fires on `startup|clear|compact`, so repeated `/clear` must not hammer the API.
- **Fail *visible*, never silent.** On error, inject `<board-state error="…">` rather than nothing — satisfies the global no-silent-failure rule and surfaces a broken token instead of pretending all is well.
- **Opt-in only**, wired during `/setup-awow` (or later via `/awow-add`), like tracing and `session-correlation`. Off by default.

### Stage 3 — Intent reinforcement via UserPromptSubmit (optional; add only if needed)

Only if Stage-1 discipline proves leaky in real sessions (the agent forgets to link mid-flow): a `UserPromptSubmit` hook that fires per message and injects a small deterministic nudge **only** when the message carries an initiative signal — or, if it literally contains a board key (`AWOW-\d+`), enriches *that one item* JIT. This is reinforcement of Stage 1, not a replacement, and it is Claude-Code-specific. Do not build it day-one; let observed behaviour justify it.

### Stage 3b — Skill-invocation reinforcement via PreToolUse (built; reinforces Stage 1 at the lifecycle seam)

`UserPromptSubmit` (Stage 3) fires on *every* message and must *guess* whether an initiative is present. When the repo also runs an inner-loop engine (superpowers, spec-kit — see [[superpowers-integration-plan]]), there is a strictly sharper trigger: the engine's lifecycle skills. A `PreToolUse` hook matching the `Skill` tool fires at a **precise, deterministic, semantic moment** — `brainstorming` (work starting), `verification-before-completion` and `finishing-a-development-branch` ("something is done") — with no guessing and no per-message firehose. This is the "when planning/spec is made; when something is done" seam made concrete.

- **Script:** `hooks/board-linkage-check.py` (+ `hooks/board-linkage-check` bash wrapper), registered as `PreToolUse` with `matcher: "Skill"`. Maps each engine lifecycle skill to its board transition (the crosswalk lives in the `board-aware-development` skill) and injects a one-line reminder via `hookSpecificOutput.additionalContext`.
- **Non-blocking, by construction.** It emits context only and never denies the call — honouring the rollback lesson from [[archetypes-board-anchoring]]: reinforce at the *completion* edge (verify / review / finish), stay whisper-thin at the *start* edge. No hard gate on any skill.
- **Scoped to adopted repos.** Silent unless `.agents/AGENTS.md` exists under `CLAUDE_PROJECT_DIR`, so enabling the plugin in a non-awow repo injects nothing.
- **Fails visible, never silent.** A malformed payload is logged to stderr with context, then the hook exits 0 so the tool call is unaffected.

Why this is better than Stage 3 here: it does not pay the per-message cost, it cannot misfire on non-initiative chatter, and it is tied to the exact lifecycle event awow wants to hook. Stage 3 (UserPromptSubmit) remains the fallback for repos with **no** engine, where there is no skill invocation to key on. Validate the same way: keep it if the board moves from these moments without the user naming a ticket; cut it if traces show the reminders ignored as noise.

## Cross-cutting constraints

- **Public-repo safety (REQUIRED).** The Stage-2 query returns private issue IDs/titles. The hook must never write to a tracked path — cache only to gitignored `.awow/`. The `pre-push` leak scan backstops, but untracked-by-construction is the first line of defence. (Per `.agents/CLAUDE.md` → *"private session data must never be committed"*.)
- **Portability is layered.** Stage 1 reaches every harness; Stages 2–3 enhance Claude Code / Copilot CLI / Cursor; IDE-Copilot degrades gracefully to the floor.
- **Board pointer is authoritative.** The hook reads `board.md` for the adapter; it does not hardcode a board. Reference impl: GitHub `gh` (cheapest to prototype) or Linear API (the real board), one adapter first.

## How we'll know it's right (and when to roll back)

awow's own history says measure, then cut what overdoes it (see [[archetypes-board-anchoring]], rolled back after traces showed it was too much). Validate against the trace stack:

- **Stage 1 success:** items get linked/advanced from conversation without the user naming a ticket, and without a wall of confirmation friction.
- **Stage 2 success:** the ambient line is *read* (referenced in-session) rather than ignored noise. If it's noise, cut it — Stage 1 stands alone.
- **Stage 3** ships only if traces show Stage-1 linkage being dropped mid-session.

## Open decisions

1. **First board adapter for Stage 2** — `gh`/GitHub Issues (fast prototype) vs. Linear API (real board).
2. **Stage-2 default** — ship disabled and offer in `/setup-awow`, or skip the hook entirely until Stage 1 is observed in the wild.
