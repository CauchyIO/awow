---
description: "gather the day once, produce both the overview and the KB candidates"
phase: standardise
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "/daily-digest producing a clean overview"
  - "{HUB}/context/knowledge-base/ set up (the promotion ritual is understood)"
removes_pain: "gathering the same day twice — once to summarise it, once to mine it"
---

# /daily-routine — gather the day once, produce both the overview and the KB candidates

You run the full daily pass in one command: gather the day's activity **once**, then
project it two ways — a team overview (the digest) and durable-knowledge candidates
(the mining lens). This is the combined path; `/daily-digest` and a future
`/kb-mine` remain available for running a single lens on its own.

**One gather, two artefacts.** The whole point is that collection happens once. The
snapshot produced in Phase 1 is reused by both projections; neither re-queries the
board or code surfaces, and the deep content is loaded once.

**Read-only against sources.** The overview is a markdown file; the KB candidates are
a review file. Nothing is committed to the durable knowledge base, the board, or any
external system without explicit approval (the digest's email gate and the KB
promotion gate both still apply).

---

## Pipeline overview

```
Phase 0 ─ Input & mode detection
Phase 1 ─ Gather once           ──→ activity/YYYY-MM-DD.json   (the day snapshot)
Phase 2 ─ Overview  (shallow projection)  ──→ digests/YYYY-MM-DD.md
Phase 3 ─ KB candidates (deep projection) ──→ {HUB}/context/kb-inbox/*.md   ──→ synthesis.md GATE (promotion)
```

Phases 2 and 3 are **independent projections of the same snapshot** — not a chain.
If one fails, the other still stands; report the failure and proceed.

---

## Phase 0 — Input & mode detection

- **Date.** Default to today; accept an explicit date argument (`YYYY-MM-DD`).
- **Email mode (optional).** If the user passes recipient emails, forward them to the
  overview projection (Phase 2) exactly as `/daily-digest` handles them — HTML render
  + manual send gate. No emails → markdown overview only.
- **Reuse check.** If `digests/<date>.md` already exists, or `{HUB}/context/kb-inbox/`
  already holds `<date>-mine-*.md` candidates, ask whether to regenerate or reuse each,
  independently.

---

## Phase 1 — Gather once

Run the shared collection step — read `{HUB}/context/tooling/activity-collection.md`,
falling back to `${CLAUDE_PLUGIN_ROOT}/context/tooling/activity-collection.md` (a vendored copy
wins over the shipped one): produce
`activity/YYYY-MM-DD.json` (or reuse it if present). That step owns the board / code /
chat queries (keyed off `{HUB}/context/tooling/board.md`), the normalised snapshot schema,
and the private-team gate.

If the snapshot cannot be produced — no `{HUB}/context/tooling/board.md`, or a fatal auth
failure on a source — stop here. Do not run either projection against a half-snapshot.

Both projections below **reuse this one snapshot**. Do not collect again.

---

## Phase 2 — Overview (shallow projection)

Produce the team overview exactly as `/daily-digest` specifies from its Phase 2
onward (synthesis → markdown → optional HTML render + send gate). Because the
snapshot already exists, `/daily-digest`'s own Phase 1 reuse check short-circuits
collection — it reads the snapshot's shallow surface (`kind` / `ref` / `actor` /
`title` / `activity`) and never loads `payload.diff`.

Write `digests/YYYY-MM-DD.md`. Honour every source's `status` in the Data Sources
table; never invent data for a failed source.

If email mode is on, carry it through to `/daily-digest`'s render + **manual send
gate** — never send without explicit approval.

---

## Phase 3 — KB candidates (deep projection)

KB paths (`inbox`, `kb_root`) resolve via `{HUB}/context/tooling/knowledge-base.md`,
falling back to `${CLAUDE_PLUGIN_ROOT}/context/tooling/knowledge-base.md`; the
literals below are the defaults.

Mine the same snapshot for durable knowledge, per `{HUB}/context/knowledge-base/mining.md`
(falling back to `${CLAUDE_PLUGIN_ROOT}/context/knowledge-base/mining.md`):
read each item's deep `payload`, apply the selectivity bar (tuned by
`{HUB}/context/knowledge-base/mining-policy.md`, else
`${CLAUDE_PLUGIN_ROOT}/context/knowledge-base/mining-policy.md`), route each survivor to its
`{HUB}/context/knowledge-base/` destination, dedup against the existing KB, and stage each
survivor as one committed file in `{HUB}/context/kb-inbox/`.

This projection **proposes only**. Do not write into `{HUB}/context/knowledge-base/` and do
not touch the board. Present the candidate summary (count, targets, duplicates
dropped, cap status) and stop — promotion is the synthesis drain (`/kb-synthesize`, per
`{HUB}/context/knowledge-base/synthesis.md`, else
`${CLAUDE_PLUGIN_ROOT}/context/knowledge-base/synthesis.md`), which runs the **approval gate** before any
candidate lands in the durable KB. You may offer to run `/kb-synthesize` now, or leave
the candidates staged in the inbox for a later drain.

If mining fails, say so and finish — the overview is already produced. The two
projections do not depend on each other.

---

## Behavioral boundaries

- **Gather once.** Never let a projection re-query a source; both read the Phase 1
  snapshot.
- **Read-only against sources.** The only writes are the overview and the staged
  inbox candidates; neither promotes into the durable KB. Promotion is synthesis's job,
  behind its gate.
- **Two approval gates stand.** The digest's email send and the synthesis promotion
  both require explicit user approval. Never cross either on your own.
- **Independent projections.** A failure in one does not block or invalidate the
  other; report honestly and produce what you can.
- **Respect the private-team boundary.** Enforced once at collection; neither
  projection can reintroduce private-surface data.
