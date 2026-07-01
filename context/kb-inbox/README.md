# kb-inbox — the committed intake for durable-knowledge candidates

The staging surface between **extraction** and **promotion**. The mining lens (and,
later, other feeders) writes each surviving candidate here as its own file; the
synthesis drain (`context/knowledge-base/synthesis.md`) reads from here and, on
approval, promotes into `context/knowledge-base/`.

**Committed on purpose.** Unlike the ephemeral `activity/` snapshots, this folder is
tracked in git. A mined insight that isn't promoted the same day must survive until it
is drained — the inbox is a durable backlog, not day-scratch. The drain reads the
*committed* state, so a candidate has to be committed to be seen.

**One concept per file.** Each candidate is a single durable insight, so it can be
promoted, deferred, or dropped on its own.

---

## File format

Filename: `YYYY-MM-DD-<source>-<slug>.md` — the date it was captured, the feeder that
produced it, and a short kebab slug (e.g. `2026-07-01-mine-per-tenant-auth.md`).

Frontmatter is allowed **here** precisely because the inbox is transient — the durable
layer stays frontmatter-light (see `context/knowledge-base/README.md`). Keep it to this
fixed schema:

```markdown
---
source: mine | transcript | workitem     # which feeder produced this
source_ref: <TEAM>-123 | <repo>#45 | path/to/transcript.md   # where it came from
date: YYYY-MM-DD                          # capture date
suggested_target: architecture | patterns | runbooks | decisions | glossary
---

<the candidate body, already written in its suggested_target's KB format —
e.g. a decisions/ candidate uses the ADR header (Context / Decision / Consequences)>
```

`suggested_target` is the mining lens's routing guess; the drain confirms or overrides
it. The body is authored in the destination's format so promotion is a move, not a
rewrite.

## Lifecycle

1. **Capture** — a feeder writes one file per candidate here and commits it.
2. **Drain** — `synthesis.md` reads the committed candidates. For each, the human-gated
   drain decides: promote (novel), annotate an existing note (matches), no-op (already
   covered), or drop (thin). See that contract for the disposition rules.
3. **Clear** — a drained candidate's file is removed (the removal is committed); its
   fate is recorded in `_synthesis-log.md`. The durable record is whatever landed in
   `context/knowledge-base/` plus the git history — not the inbox file.

## Not candidates

- `_synthesis-log.md` — append-only provenance of every drain disposition. Never a
  candidate; the drain writes to it, never promotes from it.
- `README.md` — this file.

## Staleness

Candidates should not linger. The drain's "thin → drop" disposition and the daily
routine draining as it mines keep the inbox short. If un-drained candidates accumulate,
that is a signal the drain isn't being run — surface it at a retrospective.
