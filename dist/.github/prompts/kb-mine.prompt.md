---
description: "Use when the user asks what's worth writing down from a day's work, wants to backfill knowledge-base candidates for a past day, or says hard-won insight is evaporating unrecorded."
phase: standardise
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read the board)"
  - "{HUB}/context/knowledge-base/ set up (the promotion ritual is understood)"
removes_pain: "durable insight from a day's work evaporating because nobody wrote it down"
---

# /kb-mine — surface a day's durable-knowledge candidates

You run the **deep projection** over a day's activity on its own: gather the day
once, then mine it for knowledge worth keeping in `{HUB}/context/knowledge-base/`. This is
the deep counterpart to `/daily-digest`'s shallow projection — same snapshot, different
lens. Reach for it when you want candidates for a day you did not digest, or to
backfill a past day.

**One projection, one source of truth.** The extraction — what qualifies, how it
routes, where it is written, how it is promoted — is defined once in
`{HUB}/context/knowledge-base/mining.md`, falling back to
`${CLAUDE_PLUGIN_ROOT}/context/knowledge-base/mining.md`. This
command only wires the gather to that projection; it does not restate the rules, so
it stays correct as the mining contract evolves.

**Read-only against sources; proposes only.** Nothing is committed to the durable
knowledge base or the board without explicit approval. The mining contract's
promotion gate stands.

**Paths.** The KB `inbox` and `kb_root` locations resolve via
`{HUB}/context/tooling/knowledge-base.md`, falling back to
`${CLAUDE_PLUGIN_ROOT}/context/tooling/knowledge-base.md` (defaults `{HUB}/context/kb-inbox/`,
`{HUB}/context/knowledge-base/`). `mining.md` honours the same config, so this command
inherits any relocation automatically.

---

## Pipeline overview

```
Phase 0 ─ Input
Phase 1 ─ Gather once (or reuse today's snapshot)  ──→ activity/YYYY-MM-DD.json
Phase 2 ─ Deep projection per mining.md            ──→ candidates ──→ GATE (promotion)
```

---

## Phase 0 — Input

- **Date.** Default to today; accept an explicit date argument (`YYYY-MM-DD`).
- **Reuse check.** If candidates for the date already exist (per the output location
  `mining.md` defines), ask whether to regenerate or reuse.

---

## Phase 1 — Gather once

Run the shared collection step — read `{HUB}/context/tooling/activity-collection.md`,
falling back to `${CLAUDE_PLUGIN_ROOT}/context/tooling/activity-collection.md` (a vendored copy
wins over the shipped one):
produce `activity/YYYY-MM-DD.json`, or **reuse it** if a peer run (`/daily-digest`)
already produced it for the day. That step owns the board / code /
chat queries and applies the private-team gate once.

**An absent board pointer is a question, not a stop.** If `{HUB}/context/tooling/board.md` is missing, infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess a board from a GitLab, Bitbucket, or Azure DevOps remote; those map to several products. With no remote, or with `gh` absent or unauthenticated, ask the user once which board they use and how to reach it, and do not offer the `gh` path. Record the answer at `.awow/board-session.md` with a `session:` line, and read it instead of asking again — ignore a note whose `session:` does not match this session. Offer `/setup-awow` Step 1 to make the answer durable; never write `{HUB}/context/tooling/board.md` yourself.

This relaxation covers an absent pointer only. **A fatal auth failure on a data source still stops the run** — surface it and do not mine from a half-snapshot.

If the snapshot still cannot be produced for any other reason, stop and surface it.

---

## Phase 2 — Deep projection

Follow `{HUB}/context/knowledge-base/mining.md`, falling back to
`${CLAUDE_PLUGIN_ROOT}/context/knowledge-base/mining.md`,
exactly: read each snapshot item's deep `payload`, apply the selectivity bar, route
each survivor to its `{HUB}/context/knowledge-base/` destination, dedup against the existing
KB, and write the candidates where that contract specifies.

Then stop at the contract's **promotion gate**: present the candidate summary (count,
targets, duplicates dropped, cap status) and wait for the user to say which to
promote. Promotion follows the ritual in `{HUB}/context/knowledge-base/README.md`,
falling back to `${CLAUDE_PLUGIN_ROOT}/context/knowledge-base/README.md` —
approved candidates only, each with a pointer left in its source item's comment.

---

## Behavioral boundaries

- **Gather once.** Reuse the snapshot when a peer run already produced it; never
  double-query a source.
- **One projection definition.** All extraction rules live in `mining.md`; this
  command must not diverge from them.
- **Proposes only.** No write into `{HUB}/context/knowledge-base/` and no board mutation
  without explicit approval.
- **Private-team boundary** is enforced once at collection; this lens cannot
  reintroduce private-surface data.
