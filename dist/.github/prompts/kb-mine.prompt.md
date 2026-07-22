---
description: "surface a day's durable-knowledge candidates"
phase: standardise
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read the board)"
  - "{HUB}/context/knowledge-base/ set up (the promotion ritual is understood)"
removes_pain: "durable insight from a day's work evaporating because nobody wrote it down"
---

# /kb-mine — surface a day's durable-knowledge candidates

You run the **deep projection** over a day's activity on its own: gather the day
once, then mine it for knowledge worth keeping in `{HUB}/context/knowledge-base/`. This is
the standalone counterpart to `/daily-routine` Phase 3 — same projection, without the
overview. Reach for it when you want candidates for a day you did not digest, or to
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
produce `activity/YYYY-MM-DD.json`, or **reuse it** if a peer run (`/daily-digest` or
`/daily-routine`) already produced it for the day. That step owns the board / code /
chat queries and applies the private-team gate once.

If the snapshot cannot be produced (no `{HUB}/context/tooling/board.md`, or a fatal auth
failure on a source), stop and surface it — do not mine a half-snapshot.

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
