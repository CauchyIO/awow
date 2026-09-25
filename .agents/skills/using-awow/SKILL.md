---
name: using-awow
description: "The awow operating reflex, injected at session start: board-first discipline, the approval gates, and the route from each work moment to its awow command. Read it to recall how awow expects an agent to work."
---

# You are working in an awow repo

The board is the single source of truth for planning, and awow exists to keep it true: track your work's state there and follow the instructions kept in this repo. Keep the board current as a byproduct of the work, never a chore deferred to the end.

**Non-negotiable — these survive every rationalization:**

1. **Board before build.** If the work would warrant a commit, look at the board before the first edit — no exception for "quick", "obvious", or "I'll file it after".
2. **No unapproved writes.** Never create a board item or write to team context or the knowledge base without approval in this conversation.
3. **Own the exit.** An item you moved to In Progress leaves the session forward or back — never parked silently.

| The thought | The reality |
|---|---|
| "Small change, I'll ticket it after" | After is never. Look first. |
| "The user is in a hurry" | Linking an existing item is one line. |
| "I'll batch board updates at the end" | End-of-session updates evaporate. Move state as you go. |

## Paths

`{{ANCHOR}}` is the team context root, `{{PROJECT}}` this project's; both resolve to the repo root here. In an anchored repo (root `AGENTS.md` frontmatter with an `anchor:` key), resolve `{{ANCHOR}}` as `$AWOW_ANCHOR`, else the path recorded in the gitignored `.awow/anchor.json` after its origin check — a missing or drifted link is a prompt to (re)map interactively and a loud stop headless, never a scan. Machinery reads `{{ANCHOR}}` first, then `{{AWOW_ROOT}}` (its scripts at `{{AWOW_TOOLS}}`). Unresolvable `{{ANCHOR}}`? Stop and say so. Several candidate installations or boards? Resolve per the `board-target` skill — never guess across a repo boundary.

## Board first

Before work with a discernible outcome, settle the board with the `board-target` skill, read `{ANCHOR}/context/tooling/board.md`, and search for an existing item; link with no ceremony. No match? Draft under `{PROJECT}/proposals/`, approve, create. Move state and comment as you go. Gated to initiatives — would a teammate expect to find it on the board next week? An absent `board.md` is one question (infer from a GitHub remote, else ask once), not a stop.

## Draft first, land second

`{PROJECT}/proposals/` is free; the board, team context, and knowledge base require approval. Story body = intent + acceptance criteria + KB link; status goes in comments; durable rationale in `{ANCHOR}/context/knowledge-base/`.

## Route canonical knowledge

When a task reads ANCHOR context or may create durable ANCHOR knowledge, check
`{ANCHOR}/context/knowledge-sources/index.md`. If it exists, use the
`knowledge-source-routing` skill. The catalog contains semantic routes and canonical URIs, never
mirrored content or machine-local paths. No match is ordinary ANCHOR-only behavior; an external
match is read-only and must be referenced rather than copied into the ANCHOR.

## Route to the moment

A board item to explain, refine, plan, or build → `/process-workitem`, at the depth the user asked for. A board item to create or update → the `workitem-write` skill. Lost track of your plate → `/my-work`. A rule about how the team works, stated in passing → `/update-context`. Is this repo wired? → `/setup-awow --check`. What can awow do here, what does a command do, what next? → `/awow-help`.

With the optional `awow-workflows` plugin: meeting notes in hand → `/process-transcript`; the team wants to talk its way of working through → `/team-workshop`; day wrapping up → `/daily-checkin`; "what did we ship?" → `/daily-digest`; a locked design to sequence → `/project-plan`; vision but no measurable goals → `/strategy-flow`; one bet in a live board session → the `bet-refinement-coach` skill; the quarter's standing OKR machinery, including the recurring review → `/okr-cascade`. When one of these is absent from your skill listing, `awow-workflows` is not installed here: say so and name the plugin; do not hand-roll the flow.

Reach for the catalog before hand-rolling: your skill listing, or `{AWOW_ROOT}/context/tooling/command-catalog.md`, which lists every command and the plugin it ships in.

## Through the build

Whatever you build with — your own editing, a coding subagent, an inner-loop engine's skills — the board moves at the same four beats, and the moment itself is the cue. Gated to initiatives, like every board rule above.

- **Work starting.** Ticket exists → **In Progress**. No ticket and it is an initiative → the plan draft under `{PROJECT}/proposals/` is your board moment: approve, create, then move it.
- **Building.** Comment findings and blockers *as you go*. A blocker discovered at 10:00 and reported at 18:00 was unreported all day.
- **Claiming done.** Verification evidence exists before the item reaches **In Review** or **Done** — paste it into a comment. No evidence, no move.
- **Handing over.** **In Review** with a what-to-review comment when the PR opens; **Done** with the PR link and a one-line outcome when it lands.

Where `{ANCHOR}/context/tooling/architecture.md` declares an architecture plane, plans are checked against it — `/process-workitem` step 4 carries that check. When someone states how the team works, note it and offer `/update-context` once, at a completion edge.
