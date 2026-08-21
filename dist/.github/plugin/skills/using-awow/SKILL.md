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

`{HUB}` is the team context root, `{PROJECT}` this project's; both resolve to the repo root here. In a spoke (root `AGENTS.md` frontmatter with a `hub:` key), resolve `{HUB}` as `$AWOW_HUB`, else the path recorded in the gitignored `.awow/hub.json` after its origin check — a missing or drifted link is a prompt to (re)map interactively and a loud stop headless, never a scan. Machinery reads `{HUB}` first, then `{AWOW_ROOT}` (its scripts at `{AWOW_TOOLS}`). Unresolvable `{HUB}`? Stop and say so. Several candidate installations or boards? Resolve per §Context resolution in AGENTS.md — never guess across a repo boundary.

## Board first

Before work with a discernible outcome, read `{HUB}/context/tooling/board.md` and search for an existing item; link with no ceremony. No match? Draft under `{PROJECT}/proposals/`, approve, create. Move state and comment as you go. Gated to initiatives — would a teammate expect to find it on the board next week? An absent `board.md` is one question (infer from a GitHub remote, else ask once), not a stop.

## Draft first, land second

`{PROJECT}/proposals/` is free; the board, team context, and knowledge base require approval. Story body = intent + acceptance criteria + KB link; status goes in comments; durable rationale in `{HUB}/context/knowledge-base/`.

## Route canonical knowledge

When a task reads HUB context or may create durable HUB knowledge, check
`{HUB}/context/knowledge-sources/index.md`. If it exists, use the
`knowledge-source-routing` skill. The catalog contains semantic routes and canonical URIs, never
mirrored content or machine-local paths. No match is ordinary HUB-only behavior; an external
match is read-only and must be referenced rather than copied into the HUB.

## Route to the moment

Meeting notes in hand → `/process-transcript`. A board item to execute → `/process-workitem`. A board item to create or update → the `workitem-write` skill. Day wrapping up → `/daily-checkin`. "What did we ship?" → `/daily-digest`. A locked design to sequence → `/project-plan`. Lost track of your plate → `/my-work`. Reach for the catalog in your skill listing before hand-rolling.

## Engines and rules in passing

With a build engine installed, its lifecycle skills are your board cues — see `board-aware-development` (and `architecture-aware-development` when an architecture plane is declared). When someone states how the team works, note it and offer `/update-context` once, at a completion edge.
