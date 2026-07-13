---
name: using-awow
description: "The awow operating reflex — the compact bootstrap injected at the start of every session by the awow plugin's SessionStart hook. Defines the proactive board-linkage reflex (go to the board before any initiative; carry the hygiene call yourself; link with no ceremony), the proposal-first and approval-before-write rules, and the command catalog the agent reaches for. Read or invoke this to recall how awow expects an agent to work; the full team-specific conventions live in the repo's agent instructions (AGENTS.md)."
---

# You are working in an awow repo

awow — the Agentic Way of Working — moves the discipline of keeping the board and the knowledge current into the *session itself*, not the human. The board is the single source of truth for planning; context lives in the code, not a wiki. Your job is to keep that true as a byproduct of the work in front of you — never as a chore deferred to the end.

This is the reflex. The team's full conventions, mission, and board spec live in the repo's agent instructions (`AGENTS.md`) and `{HUB}/context/` — read them when you need the specifics.

## Where the paths point

Paths here never hardcode a location — they use three tokens. **In this repo, and in any vendored or plugin install, `{HUB}` and `{PROJECT}` both resolve to the repo root and `../../tools` to awow's bundled tools** — so `{HUB}/context/tooling/board.md` is the board pointer read at that path under the root. In a hub-connected spoke, a hub pointer tells you where `{HUB}` resolves instead. If `{HUB}` is ever unresolvable, stop and say so — never guess a location or improvise a convention.

## Go to the board before any initiative

Before you start work with a discernible outcome — a bug, a feature, a refactor, anything that would warrant a commit — go to the board first.

- **Look first.** Read `{HUB}/context/tooling/board.md` for the board pointer and read/write surface, then search for an existing ticket covering the scope. If one exists, use it; do not duplicate.
- **No match? Propose, then create.** Draft the issue under `{PROJECT}/proposals/` first, get approval, then create it on the board.
- **Move state and comment as you go.** Move to "In progress" when you start; comment on blockers and findings; close when the change lands. Never a silent state change.

Gated to *initiatives*, not every edit. A grep, a clarifying answer, a one-line typo fix the user named — no ticket. Rule of thumb: would a teammate reasonably expect to find this on the board next week? If yes, ticket; if no, just do it.

## Carry the hygiene decision yourself

Apply that rule of thumb *proactively*. Do not bounce it back as "shall I make an issue for this?" — make the call, act, and report what you did in one line. Read what the work *is* from the conversation, not from the current branch. Link to an existing item with no ceremony ("tracking this under AWOW-42"); reserve approval for *creating* a new item. As work lands, move state and drop a one-line comment unprompted.

## Draft first, land second

Iterate on the cheap artefact. A markdown file under `{PROJECT}/proposals/` is free; the board, the knowledge base, and `AGENTS.md` are expensive to change well. Never write directly to the board, the team context, or the knowledge base without human approval. Story bodies carry intent + acceptance criteria + a knowledge-base link — nothing more; status and findings go in comments; durable rationale goes in `{HUB}/context/knowledge-base/`.

## Reach for the commands

awow ships the loop as commands and skills — prefer them over improvising:

- `/setup-awow` — bootstrap or extend awow in this repo.
- `/process-workitem` — take a board item from refinement to PR.
- `/refinement-prep` — draft a feature for the next refinement.
- `/daily-checkin` — map your day to the board and execute approved updates.
- `/project-manager` — run the delivery coordination loop.
- `/project-plan` — turn a locked design into a published plan.

Invoke the relevant one before hand-rolling the same workflow. The full catalog is the awow command set (vendored: `.agents/commands/`; plugin installs: the awow plugin's commands).

## When an inner-loop engine is present

If a build engine (superpowers, spec-kit) is installed, its lifecycle skills *are* your board cues: `brainstorming` is a board moment, `verification-before-completion` gates In Review/Done, `finishing-a-development-branch` closes the ticket. Bind each transition to the skill that already fires at it — see `board-aware-development` for the full crosswalk. When the repo declares an architecture plane in `{PROJECT}/context/tooling/architecture.md`, those same lifecycle skills are also your *architecture* cues — see `architecture-aware-development` for that crosswalk. Working directly (outside `/process-workitem`), keep the board current as you fire those skills; the PreToolUse hook reminds you, but the discipline is yours.

No engine installed? awow runs on its baseline board discipline alone — nothing here misfires. superpowers is the recommended optional engine for the build step; offer it via `/setup-awow` (Step 8, surface the extras), never force it.
