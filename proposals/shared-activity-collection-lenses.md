# Proposal — shared daily-activity collection, digest & mining as lenses

**Status:** Draft (solutioning) — proposes a shape; not yet a plan or issue.

---

## Look-first check (done)

- `/daily-digest` (`.agents/commands/daily-digest.md`) already reads the board
  surface **from `context/tooling/board.md`** (Phase 1.A), the code-hosting surface
  (Phase 1.B), and an optional chat surface (Phase 1.C). Collection is *already*
  config-driven — it is just **inlined** into the one command.
- No mining / KB-extraction command exists in awow yet. The durable-knowledge path
  today is the **promotion ritual** (`context/knowledge-base/README.md`) run by
  `/process-workitem` and `/process-transcript` — human/agent-triggered, per-item,
  not a daily automated sweep over activity.
- `tools/gather.py` already owns the name **"gather"** (it generates the pointer
  stubs). A collection step must not reuse that word.
- Prior art: teams already running this pattern do it as *two passes over the same
  day* (digest, then KB-mine as a later step), which double-fetches the board + code
  surfaces and double-loads the agent context. This proposal is the awow-portable,
  prompt-driven generalisation that gathers once and projects many.

---

## Problem

Two distinct products want the **same day's activity** through different lenses:

- **Digest** — a *synthesis* lens: shallow activity (who moved what, state
  transitions, cross-relevance) → a team-wide narrative.
- **Mining** — an *extraction* lens: deep content (full issue text, comment
  threads, PR diffs) → durable KB candidates.

They "source the same data, different lenses on (almost) the same source." Today in
awow only the digest lens exists, with collection **inlined**. The moment a mining
lens is added — or a routine runs both — the naive shape is two independent
collections over one day: the board and code surfaces are queried twice, the
private-team exclusion is implemented twice (drift risk), and the agent loads the
overlapping activity into context twice. That is wasted API cost and wasted tokens,
and it couples two products that should be independent.

## The shape (proposed)

**Collect once, into a day snapshot. Each lens projects.**

```
context/tooling/board.md  ┐
code-hosting surface      ├─▶  collection step  ──▶  activity/YYYY-MM-DD.json
chat surface (optional)   ┘     (board-agnostic,        (the day snapshot;
                                 private gate applied      superset depth)
                                 once, superset depth)
                                        │
              ┌─────────────────────────┴─────────────────────────┐
        digest lens (shallow project)                mining lens (deep project)
        /daily-digest → digests/…md                  future /kb-mine → KB candidates
```

- **The collection step is board-agnostic by construction:** it reads the configured
  board from `context/tooling/board.md` (the single source of truth per
  `context/tooling/boards/README.md`) and the code/chat surfaces the digest already
  names. A Linear / ADO / Jira / GitHub adopter gets identical behaviour with zero
  provider-specific logic — the genericity comes from `context/`, not from code.
- **The snapshot is the superset (deep).** It carries the deep content the mining
  lens needs (issue descriptions, comment bodies, PR diffs). The **digest lens
  projects shallow** — it reads only activity/transition fields from the snapshot
  and never loads diffs into its synthesis context, so digest cost does not grow.
- **The private-team gate is applied once, at collection.** The private-team rule in
  `context/team/conventions/REQUIRED/labels.md` says private-surface data never flows to
  shared outputs. Applying it inside the collection step means no lens can leak it,
  and there is one implementation to keep correct.

## Positioning decision — one gather, one command, two artefacts

`activity-collection.md` is the **means to gather** — a shared sub-step, not a
product. On top of it sits a single **daily routine command** that gathers the day
**once** and emits **both** artefacts from that one corpus: the digest overview
(shallow projection) and the KB candidates (deep projection). This is the shape the
`linear` routine already has — one run, both outputs — **minus its double
collection**, which is the bug being corrected.

- **Primary path — the combined routine.** Gather once via the collection step, then
  fan out to both projections **in the same run**, holding one corpus. No second
  query, no second context load. This is the linear spec's gather-once / project-many
  fix, expressed as a prompt.
- **Standalone lenses stay available.** `/daily-digest` alone (just the overview) and
  a future `/kb-mine` alone (just candidates) each open with the same gather step and
  a **reuse check** on `activity/YYYY-MM-DD.json` — so running one never strands the
  other, and a day can be mined without being digested. The snapshot-on-disk + reuse
  check only matters for these standalone/cross-invocation runs; the combined routine
  holds the corpus in-run and needs no disk round-trip.
- **Collection is nobody's property.** It is the gather means both projections call —
  not a stage the digest owns, and **not** a hard `collect → digest → mine` chain
  where mining depends on the digest (the one thing in the linear routine worth *not*
  copying: there mining is Step 5 *after* the digest PR).

So: **the gather step is the primitive; the daily routine is the one command that
gathers once and fans out to both projections; the individual lenses are thin
standalone wrappers over the same primitive.**

## What changes

| Artefact | Change |
|---|---|
| **Collection step** (new) | `context/tooling/activity-collection.md` — the gather means: what to pull from the `board.md` surface + code + chat, at superset depth, private-team gate applied once, and the `activity/YYYY-MM-DD.json` snapshot schema (normalised, board-agnostic fields + a `payload` for deep content). |
| **Daily routine** (new) | The combined command: gather once via the collection step, then fan out to **both** projections in the same run — the digest overview *and* the KB candidates. This is the primary path and the awow analog of the `linear` daily routine. |
| `/daily-digest` | Becomes a **standalone wrapper**: open with the collection step (or reuse snapshot), then the **shallow** projection → overview. Behaviour-preserving for the digest output; usable alone or called by the daily routine. |
| Future `/kb-mine` | Standalone wrapper: collection step (or reuse snapshot) → **deep** projection → KB candidates via the promotion ritual (`context/knowledge-base/`). Out of scope to build here; the routine and this lens share one projection definition. |
| `.gitignore` / retention | `activity/*.json` snapshots are ephemeral scratch (gitignored) — the digest and KB outputs are the durable records. |

## Portability check (the whole point)

- **Board:** read from `context/tooling/board.md`. No provider names in the
  collection step. Works for every board in `context/tooling/boards/`.
- **Private exclusion:** read from `context/team/conventions/REQUIRED/labels.md`.
  Teams without a private surface simply have nothing to exclude.
- **Enterprise override:** inherits the existing `.agents-overrides/` precedence for
  board references — no new override surface needed.
- **Adopter with only a digest today:** unaffected; collection is factored out but
  the digest still produces the same file. The mining lens is additive.

## Phasing

1. **Write the collection step** + snapshot schema. *(Done — `context/tooling/activity-collection.md`.)*
2. **Point `/daily-digest` at it** (reuse-or-produce + shallow projection). *(Done.)*
   Fixture-day parity check is manual — the digest is a prompt, not code, so there is
   no deterministic output to diff automatically.
3. **Define the deep (mining) projection + the combined daily routine.** *(Done —
   `context/knowledge-base/mining.md` + `/daily-routine`.)* One command gathers once
   and emits both artefacts; this is where the token/perf win lands end-to-end.
4. **`/kb-mine` standalone.** *(Done — thin wrapper over the Phase-3 deep projection.)*
   Delegates all extraction to `context/knowledge-base/mining.md`, so it inherits any
   later change to that contract (e.g. the committed-inbox spine in
   [kb-capture-synthesize-spine](kb-capture-synthesize-spine.md)) for free.

## Accepted risks

- **Snapshot carries deep content even on digest-only days.** Acceptable: the digest
  projects shallow and never loads diffs into synthesis context; the extra depth
  sits in the snapshot file, not the digest's token budget. A shallow-only
  collection mode is available if a digest-only adopter ever needs it — deferred.
- **A new shared contract is another file to keep honest.** Mitigated by the
  fixture-day parity test in Phase 2 and by collection already being config-driven
  today (this factors out what exists; it does not invent a new data path).

## Open questions

1. Snapshot home + retention: `activity/YYYY-MM-DD.json` gitignored scratch, or kept
   as an auditable record? (Leaning: gitignored — outputs are the record.)
2. Is the collection contract a **command** (`/collect-activity`) or a **non-command
   shared step** referenced by each lens? (Leaning: shared step — users invoke
   lenses, not the collector; a routine can still trigger it via the first lens.)
3. Does the mining lens belong in awow's core catalogue, or stay an optional
   capability like the digest's email mode? (Defer to the mining-lens proposal.)
