---
description: "Use when the user asks what they should work on, what is pending or waiting on them, or says they have lost track of the board and want to get oriented before starting a block of work."
phase: spread
prerequisites:
  - "A board connected (/setup-awow) — the agent can read the board"
removes_pain: "the what-am-I-actually-needed-on-right-now problem"
---

# /my-work — what the board says you need to act on

Read the board through one lens: **what needs *you*, now.** You run this to get oriented at the start of a block of work, or any time the board has drifted out of your head ("I'm lost, what's pending on me?").

This is the *inbound, personal* view. It is distinct from its two neighbours in the optional `awow-workflows` plugin — name them only as that plugin's commands, since a core-only install does not have them:

- `/daily-checkin` (`awow-workflows`) — *outbound*: you narrate what you did, it updates the board.
- `/daily-digest` (`awow-workflows`) — *team-wide*: what the whole team shipped.
- `/my-work` — *inbound, personal*: what the board is asking of you.

Read-only by default. You triage; you do not silently mutate the board.

## Inputs

- Optional: a person (name or board handle) to run it for. Default: the current user — read `{PROJECT}/.awow/profile.json` (`board_identity`) first, else `{ANCHOR}/context/tooling/board.md` (board identity) or the git identity.
- Optional: a scope — a single project/team. Default: everything assigned to you.

## Flow

### 1. Resolve "me"

Determine whose work to pull. Read `{PROJECT}/.awow/profile.json` first; if the board identity is still ambiguous, ask once and offer to record it in the profile — do not guess across users.

### 2. Pull assigned work

**Resolve the target first.** Settle which installation and which board this is — including when `board.md` is absent or names several boards — with the `board-target` skill, before the first board read, and announce `targeting board: <name>` when it resolved without asking.

Query **the one board `board-target` resolved** (surface per `{ANCHOR}/context/tooling/board.md`) for items assigned to that person that are open — filter out done and canceled states in the query itself, never after fetching. When `board.md` lists several boards, the work the user named settles which — `app/` work means the board whose scope covers `app/`. Report that board's items and no other's: an item on another board is not "your work" for this run, not even as a side note. Never sweep every board because the ask was broad. When `board.md` declares a board-team filter for a shared board, scope the query to the filter. Pull enough to triage: title, state, priority, due date, last-update time, parent, and whether the item is blocked or in review. Do not pull full descriptions in the list query; read one item's description only when a signal in step 4 needs it.

### 3. Group by what it needs from you — not by raw status

Do not dump a status list. Re-group into action buckets. **Every item you pulled appears exactly once**, in the bucket that says what to do about it — a blocked In Progress item goes under Waiting, with its staleness as a flag on that line, not a second entry under In flight. Every `<n>` is the number of items listed under that heading — count the IDs you print, never estimate. A line that stands for several items names every ID it covers.

An item not assigned to the user may appear only when it blocks the user's own work and nobody holds it; put it under **Waiting**, never under Needs you now, and label it on its line — *not assigned to you — blocks <ID>* — so it is never read as theirs.

- **Needs you now** — In Review awaiting *your* review, blocked-on-you, overdue, or high-priority Todo. These are the things that move only if you act. An overdue item goes here even when it is also blocked: it needs you to chase or re-plan it; note the blocker on its line.
- **In flight** — your In Progress items. Flag any that are **stale** (no update in N working days; default 3) — these are the ones quietly stuck.
- **Waiting** — blocked on someone else or an external dependency, and your own items In Review that wait on someone else's review. Name what each is waiting on — the reviewer, or `no reviewer set` — so you know whom to chase rather than what to do.
- **Next up** — the top three of your Todo / Backlog, each with its title, by priority — or, when the board sets no priorities, by the pick order `board.md` records (cycle, then last update) — so you know what surfaces when the current work clears. Close the group with one line for the rest — `+<n> more: <every ID>` — so no pulled item goes unnamed.

### 4. Surface the signals, briefly

Call out, in one line each: overdue items, stale In Progress, anything In Review aging without a reviewer, and any item assigned to you that has no parent or no acceptance criteria (it will stall when picked up). Flag missing acceptance criteria only after reading that item's full description; a truncated or summary read is no evidence, so leave the signal out.

### 5. Offer to act — never act silently

End with a short list of concrete follow-ups you *could* take (move a stale item back to Todo, comment a nudge on an aging review, close something already done). Take none without explicit approval — this command reads the board; it does not rewrite it on its own.

## Output template

```markdown
# Your work — <date>

<one sentence: what needs you now, or that nothing does — it names only items under Needs you now>

## Needs you now (<n>)
- **<ID>** <title> — <why it needs you: review / blocked-on-you / overdue / high-pri> <link>

## In flight (<n>)
- **<ID>** <title> — <state>, last moved <when> <⚠ stale if applicable>

## Waiting (<n>)
- **<ID>** <title> — waiting on <person / dependency> <⚠ stale if applicable>
- **<ID>** <title> — not assigned to you — blocks <ID>, nobody holds it
- **<ID>** <title> — in review, waiting on <reviewer | no reviewer set>

## Next up (<n>)
- **<ID>** <title> — <priority>
- +<n> more: <ID>, <ID>, …

## Signals
- <overdue / stale / unparented / no-AC call-outs, one line each>

## I could (with your go-ahead)
- <concrete board action> — <which item>
```

## Anti-patterns

- **Don't echo the board.** A flat list of every assigned issue is the problem this command exists to solve, not the output. If you are not re-grouping by "what needs me," you are not done.
- **Don't let the opening contradict the buckets.** The opening sentence speaks for Needs you now only; a stale or risky item elsewhere keeps its flag on its own line and in Signals.
- **Don't write without approval.** Read-only by default; surface proposed actions, wait for the go-ahead, then write through the `workitem-write` skill.
- **Don't invent priority the team hasn't set.** Use the board's own priority and due dates; if an item has none, say so rather than ranking it by vibe.
- **Don't moralise about backlog size.** Report what is actionable; a 90-item backlog is not a finding, the three things that need you today are.
