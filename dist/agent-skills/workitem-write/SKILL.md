---
name: workitem-write
description: "Use for any board item create or update — an ad-hoc make-a-ticket request or a flow's write step. The one convention-wired path: look first, cite conventions, shape, gate, write, report."
---

# workitem-write — the one path for board creates and updates

Every board item create or update routes through these six steps: a flow delegating its write step (`/daily-checkin`, `/project-plan`, `/refinement-prep`, `/process-transcript`, `/project-manager`) or an ad-hoc "make a ticket for X" mid-session. A delegating flow keeps its own discovery, templates, and flow-specific rules; this skill owns the generic write discipline. It is deliberately type-agnostic — work-type rules live in the `_workitem-archetypes/` handlers at execution time, never here at creation time.

## 1. Look first

Search the board (surface per `{HUB}/context/tooling/board.md`) before drafting anything new, along four axes: keywords from the request, named owners' assigned items, project / area scope, and recency (items updated in the last two cycles). Note match confidence: exact / likely related / weak signal.

Found coverage → link or comment with no ceremony. **Smallest board footprint wins:** comment > move > create. Creating a new item is the exception that must justify itself against the search you just ran, never the reflex.

**An absent `board.md` is a question, not a stop.** Infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess from a GitLab, Bitbucket, or Azure DevOps remote; ask. With no remote, or with `gh` absent or unauthenticated, ask once which board they use and how to reach it, and do not offer the `gh` path. Record the answer at `.awow/board-session.md` with a `session:` line and read it rather than asking twice; ignore a note whose `session:` does not match this session. Offer `/setup-awow` Step 1 to make it durable; never write `{HUB}/context/tooling/board.md` yourself.

## 2. Convention inventory

Before shaping a draft, read and apply:

- `{HUB}/context/team/conventions/REQUIRED/issue-titles.md` — title verbs and patterns
- `{HUB}/context/team/conventions/REQUIRED/labels.md` — the label taxonomy
- The board's existing projects / containers and their naming

The draft **cites** which conventions shaped it — title pattern, labels chosen, container — so the user approves against the team's rules, not your taste. Placing an item in a new container requires stating why no existing one fits.

## 3. Shape the body

- Story shape per the `user-story-template` skill; voice per `{HUB}/context/team/style/board-output.md`.
- Placement per `{HUB}/context/team/conventions/REQUIRED/output-discipline.md` Rule 2: intent + acceptance criteria → body; status, blockers, execution decisions → comment; durable rationale → `{HUB}/context/knowledge-base/`. Label every section by placement before the gate — the user approves placement, not just words.
- **No invented specifics.** A draft may not name a technology, path, endpoint, count, limit, or time window the source material or `{HUB}/context/` did not state — those are design decisions; surface them as open questions. Never fill in Owner or Cycle unless the user named them.

## 4. Gate

Creating an item, moving state, or editing a body requires explicit approval in this conversation; linking an existing item and commenting do not. Batched writes are presented as a compact summary — one line per action, drafts and cited conventions available on request — with the standard options:

```
"go"       — execute all
"skip 2,3" — execute all except listed
"review"   — walk through each
"cancel"   — no changes
```

Wait for the user. Execute only what was explicitly approved.

## 5. Write + report

Execute via the board surface, one action at a time, confirming each briefly. Re-verify each item match before touching it; if an item changed since discovery, pause and ask. Execute exactly what was approved — if ambiguity surfaces mid-execution, stop and ask; no silent changes. If an action fails, report the error and continue. Encode dependency edges when given: the board's native blocked-by relation, or a `Blocked by:` body line when the board has none.

Then report:

```
DONE
Executed: [one line each]
Skipped: [list or "none"]
Failed: [list or "none"]
Manual follow-up: [list or "none"]
```

## 6. Hygiene hooks

- **One layer at a time.** Decomposing into more than ~5 children → create the first layer only; deeper layers wait until the work reaches them.
- **Update vs. edit** (output-discipline Rule 3): body edits are reserved for scope and acceptance-criteria changes; status, progress, and findings go in comments. Never rewrite a body to "reflect the latest thinking."
