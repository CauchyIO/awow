# KB mining — the deep projection over a day snapshot

The counterpart to the digest's shallow projection. Where the digest reads a day
snapshot's activity to narrate *what moved*, mining reads the snapshot's **deep
`payload`** — issue descriptions, comment threads, PR bodies and diffs — to surface
**durable knowledge** worth keeping.

This is a **projection contract, not a command.** `/kb-mine` follows it. It assumes
the day snapshot already exists (produced by the shared collection step,
`context/tooling/activity-collection.md`)
and never re-queries a source.

**Read-only against the durable KB.** The only output is *candidates* staged in
`context/kb-inbox/` — one committed file per candidate. Nothing is written into
`context/knowledge-base/` here; that is the synthesis drain's job
(`context/knowledge-base/synthesis.md`), and it is approval-gated (see *Output* and
*Handoff to synthesis*).

**Paths.** The `inbox` and `kb_root` locations resolve via
`context/tooling/knowledge-base.md`. The literals below (`context/kb-inbox/`,
`context/knowledge-base/`) are the defaults; if that config declares different
locations, use those.

---

## Input

The deep view of the snapshot: for each item, its `payload` (issue `description`,
`comments`, state `history`; PR `body`, `review_comments`, capped `diff`) plus the
`ref`/`title`/`actor` surface for attribution. The private-team gate already ran at
collection, so nothing here can carry private-surface data.

## Selectivity — read the policy

The keep bar is **not hardcoded here.** Apply the selectivity dial, the enabled
`categories`, and the qualifies/does-not rubric defined in
`context/knowledge-base/mining-policy.md`. That is the one place an adopter tunes what
mining keeps; this contract reads it and applies it so the two never drift.

The rubric's essence: mine for what belongs in a **reference layer**, not a changelog —
*would a teammate six months from now, hitting this problem cold, be glad this was
written down?* awow ships strict (`selectivity: 2`): a low yield of high-signal
candidates beats a pile of noise. See the policy for the full qualifies/does-not lists
and examples.

## Routing

Map each surviving candidate to its `context/knowledge-base/` destination, per that
folder's `README.md`:

| Signal | Target |
|---|---|
| Recurring solution / "how we do X" | `patterns/<slug>.md` |
| A choice with trade-offs | `decisions/<slug>.md` (lightweight ADR format) |
| System shape / integration contract | `architecture/<slug>.md` |
| Repeatable ops / incident procedure | `runbooks/<slug>.md` |
| A domain term | an entry appended to `glossary.md` |

Author each candidate **in its destination's format** — e.g. a `decisions/`
candidate uses the ADR header (Context / Decision / Consequences) from the KB README.

## Dedup

Before proposing a candidate, search the existing `context/knowledge-base/` tree.
Drop any candidate substantially covered by an existing entry; among near-duplicate
candidates from the same day, keep the strongest one. Record how many you dropped —
it is a signal about the day's true yield.

## Caps

Bound the run's output by `max_candidates_per_run` and `max_candidates_per_item` from
`mining-policy.md`. If more seem to qualify than the run cap allows, the selectivity bar
is too low — raise its strictness and keep the strongest. Note when a cap was hit (in
the run summary) — it is a signal about the day's true yield.

## Output — one committed candidate per file in kb-inbox

Write each surviving candidate as its own file in `context/kb-inbox/`, named
`YYYY-MM-DD-mine-<slug>.md`, per that folder's `README.md` format:

```markdown
---
source: mine
source_ref: <ref>                # the issue/PR the insight came from
date: YYYY-MM-DD
suggested_target: patterns | decisions | architecture | runbooks | glossary
---

<the candidate body, already in the destination's format — e.g. a decisions/
candidate uses the ADR header (Context / Decision / Consequences)>
```

Commit the new candidate files — the synthesis drain reads committed state. Then present
a short summary to the user: how many candidates, their targets, how many duplicates were
dropped, and whether a cap was hit.

`context/kb-inbox/` is a **committed** backlog (unlike the ephemeral `activity/`
snapshots): a candidate survives until the drain promotes or drops it. The durable
record is whatever synthesis lands in `context/knowledge-base/`.

## Handoff to synthesis — approval-gated, never automatic

This lens **proposes**; the synthesis drain (`context/knowledge-base/synthesis.md`)
**promotes**, on explicit human approval only. Mining never writes into
`context/knowledge-base/` and never touches the board — it stages into the inbox and
stops. See `synthesis.md` for the per-candidate disposition (novel / matches / covered /
thin), the promotion gate, and the pointer-plus-provenance ritual.
