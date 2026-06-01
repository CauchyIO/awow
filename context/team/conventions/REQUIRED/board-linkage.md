# Board linkage

Non-negotiable. Read at session start.

The board's job is to stay current without the developer having to *manage* it. They will still open the board — to see priorities, pick up work, get the overview — and that is fine. What they should not carry is the housekeeping decision: *"Should this be an issue? Should I make it now? Does one already exist? What state is it in?"* You carry that. This file says how.

`output-discipline.md` governs *how* to write to the board. This file governs *whether, when, and to what* you link the work in front of you.

## Rule 1 — You own the "is this worth an issue, and when" judgment

Apply the standing heuristic — *"would a teammate reasonably expect to find this on the board next week?"* — yourself, proactively, as work unfolds. Do not bounce the decision back to the user with *"shall I make an issue for this?"* Make the call, act on it, and report what you did in one line. The developer should never have to stop and wonder whether now is the moment to open a ticket.

The gate is unchanged: discernible outcomes (a bug, a feature, a refactor — anything warranting a commit) get an item; reading files, a grep, a clarifying answer, a named typo do not.

## Rule 2 — Relevance comes from the conversation, not the branch or the session

Read the unit of work from what the user is actually doing. Do **not** infer it from the current git branch — a developer may sit on one branch, or on `main`, for weeks, and forcing branch-discipline so a tool has something to read is backwards. Do not pre-load "everything assigned to me" either; that is noise, not relevance.

When an initiative surfaces, query the board *then*, scoped to that intent, to find the matching item or propose one. Just-in-time, not up-front.

## Rule 3 — Link with low ceremony

On linking to an existing item, say so in one line — *"tracking this under PROJ-42"* — and continue. Reserve a confirmation step for **creating** a new item (proposal-first still applies: draft under `proposals/`, get approval, then create). Linking to what already exists needs no ritual.

If nothing matches and the work clearly warrants an item, propose one rather than working untracked — but keep proposing lightweight, one item per real unit of work, never a parallel near-duplicate.

## Rule 4 — Keep it current as you work, unprompted

As edits and commits land, move the item's state forward ("In progress" when you start, closed when it lands) and drop a one-line comment when there is a genuine finding or blocker — without being asked. The board updates as a byproduct of the session, not as a separate chore at the end.

Bound this by `output-discipline.md`: status and progress go in **comments**, not the body; minimum useful body; durable rationale goes to the knowledge base. Currency is not licence to sprawl.

## What this is not

- **Not "never touch the board."** Developers still read it and pick up work there. What lifts is the *coordination overhead*, not the board.
- **Not silent.** Every link, creation, and state change is surfaced in one line. The developer is never guessing what you did on their behalf.
- **Not retroactive.** You are not chasing every historical untracked change into the board. The discipline applies forward, to the work in front of you.
