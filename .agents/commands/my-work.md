---
phase: spread
prerequisites:
  - "Step 1 of /setup-awow complete (the agent can read the board)"
removes_pain: "the what-am-I-actually-needed-on-right-now problem"
---

# /my-work — what the board says you need to act on

Read the board through one lens: **what needs *you*, now.** You run this to get oriented at the start of a block of work, or any time the board has drifted out of your head ("I'm lost, what's pending on me?").

This is the *inbound, personal* view. It is distinct from its neighbours:

- `/daily-checkin` — *outbound*: you narrate what you did, it updates the board.
- `/daily-digest` — *team-wide*: what the whole team shipped.
- `/my-work` — *inbound, personal*: what the board is asking of you.

Read-only by default. You triage; you do not silently mutate the board.

## Inputs

- Optional: a person (name or board handle) to run it for. Default: the current user, resolved from `{HUB}/context/tooling/board.md` (board identity) or the git identity.
- Optional: a scope — a single project/team. Default: everything assigned to you.

## Flow

### 1. Resolve "me"

Determine whose work to pull. If the board identity is ambiguous, ask once; do not guess across users.

### 2. Pull assigned work

Query the board (surface per `{HUB}/context/tooling/board.md`) for items assigned to that person across all states. Pull enough to triage: title, state, priority, due date, last-update time, parent, and whether the item is blocked or in review.

**An absent `board.md` is a question, not a stop.** Infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess from a GitLab, Bitbucket, or Azure DevOps remote; ask. With no remote, or with `gh` absent or unauthenticated, ask once which board they use and how to reach it, and do not offer the `gh` path. Record the answer at `.awow/board-session.md` with a `session:` line and read it rather than asking twice; ignore a note whose `session:` does not match this session. Offer `/setup-awow` Step 1 to make it durable; never write `{HUB}/context/tooling/board.md` yourself.

### 3. Group by what it needs from you — not by raw status

Do not dump a status list. Re-group into action buckets:

- **Needs you now** — In Review awaiting *your* review, blocked-on-you, overdue, or high-priority Todo. These are the things that move only if you act.
- **In flight** — your In Progress items. Flag any that are **stale** (no update in N working days; default 3) — these are the ones quietly stuck.
- **Waiting** — blocked on someone else or an external dependency. Name what each is waiting on, so you know whom to chase rather than what to do.
- **Next up** — the top few of your Todo / Backlog, by priority, so you know what surfaces when the current work clears.

### 4. Surface the signals, briefly

Call out, in one line each: overdue items, stale In Progress, anything In Review aging without a reviewer, and any item assigned to you that has no parent or no acceptance criteria (it will stall when picked up).

### 5. Offer to act — never act silently

End with a short list of concrete follow-ups you *could* take (move a stale item back to Todo, comment a nudge on an aging review, close something already done). Take none without explicit approval — this command reads the board; it does not rewrite it on its own.

## Output template

```markdown
# Your work — <date>

## Needs you now (<n>)
- **<ID>** <title> — <why it needs you: review / blocked-on-you / overdue / high-pri> <link>

## In flight (<n>)
- **<ID>** <title> — <state>, last moved <when> <⚠ stale if applicable>

## Waiting (<n>)
- **<ID>** <title> — waiting on <person / dependency>

## Next up (<n>)
- **<ID>** <title> — <priority>

## Signals
- <overdue / stale / unparented / no-AC call-outs, one line each>

## I could (with your go-ahead)
- <concrete board action> — <which item>
```

## Anti-patterns

- **Don't echo the board.** A flat list of every assigned issue is the problem this command exists to solve, not the output. If you are not re-grouping by "what needs me," you are not done.
- **Don't write without approval.** Read-only by default; surface proposed actions, wait for the go-ahead.
- **Don't invent priority the team hasn't set.** Use the board's own priority and due dates; if an item has none, say so rather than ranking it by vibe.
- **Don't moralise about backlog size.** Report what is actionable; a 90-item backlog is not a finding, the three things that need you today are.
