# kb-inbox — the committed intake for durable-knowledge candidates

The staging surface between **extraction** and **promotion**. The mining lens (and,
later, other feeders) writes each surviving candidate here as its own file; the
synthesis drain (`context/knowledge-base/synthesis.md`) reads from here and, on
approval, promotes into `context/knowledge-base/`.

**Committed on purpose.** Unlike the ephemeral `activity/` snapshots, this folder is
tracked in git. A mined insight that isn't promoted the same day must survive until it
is drained — the inbox is a durable backlog, not day-scratch. The drain reads the
*committed* state, so a candidate has to be committed to be seen.

**Location.** This folder (`inbox`) is configurable — its path is declared in
`context/tooling/knowledge-base.md` (default `context/kb-inbox/`). Relocate it there.

**One concept per file.** Each candidate is a single durable insight, so it can be
promoted, deferred, or dropped on its own.

---

## Two lanes, one drain

Candidates arrive in two kinds. Both stage here, both drain through `/kb-synthesize`,
and they differ only in where they promote to and how they are judged:

| `kind` | Feeder | Promotes into | What it is |
|---|---|---|---|
| `knowledge` (default) | `/kb-mine`, transcripts, work items | `kb_root` (`context/knowledge-base/`) | A durable fact about the system or the domain. |
| `guidance` | `/update-context` | `context/team/conventions/` or `context/team/style/` | A durable rule the team obeys — "when X, do Y". |

The split is the P3 predicate `/update-context` applies: normative and team-scoped is
`guidance`; a fact about the world is `knowledge`. *"The staging DB is eu-west-1"* is
knowledge even though it is durable, general, and asserted. A candidate carries exactly
one kind.

## File format

Filename: `YYYY-MM-DD-<source>-<slug>.md` — the date it was captured, the feeder that
produced it, and a short kebab slug (e.g. `2026-07-01-mine-per-tenant-auth.md`).

Frontmatter is allowed **here** precisely because the inbox is transient — the durable
layer stays frontmatter-light (see `context/knowledge-base/README.md`). Keep it to this
fixed schema:

```markdown
---
kind: knowledge | guidance                # which lane this drains into (default: knowledge)
source: mine | transcript | workitem | update-context   # which feeder produced this
source_ref: <TEAM>-123 | <repo>#45 | path/to/transcript.md   # where it came from
date: YYYY-MM-DD                          # capture date
suggested_target: <vocabulary depends on kind — see below>
source_quote: "<the verbatim sentence>"   # kind: guidance only, required
---

<the candidate body, already written in its destination's format — a decisions/
candidate uses the ADR header (Context / Decision / Consequences); a guidance
candidate is the rule itself, in the target file's own format>
```

`suggested_target` is the feeder's routing guess; the drain confirms or overrides it.
Its vocabulary depends on `kind`:

| `kind` | `suggested_target` |
|---|---|
| `knowledge` | `architecture`, `patterns`, `runbooks`, `decisions`, or `glossary` — a `kb_root` subfolder |
| `guidance` | a repo-relative path to an **existing** file under `context/team/`, or the literal `UNROUTED` |

`UNROUTED` means no destination file exists. It is a deliberate terminal state, not a
failure to fix: neither the feeder nor the drain may create a new convention or style
file to resolve it. A file invented at that moment is one no README indexes, no command
reads, and `/setup-awow` does not know about. Unrouted candidates accumulating is the
signal that the context tree is missing a home — inventing one destroys the signal by
looking like a resolution.

`source_quote` is required for `kind: guidance` and holds the **verbatim** sentence the
rule was stated in — one line, double-quoted, never paraphrased. Both gates that can
approve a guidance candidate show it, because a rule approved without seeing the
sentence it came from is guessed rather than approved. A guidance candidate missing it
is malformed: the drain reports it and leaves it in the inbox.

The body is authored in the destination's format so promotion is a move, not a rewrite.

## Lifecycle

1. **Capture** — a feeder writes one file per candidate here and commits it.
2. **Drain** — `synthesis.md` reads the committed candidates. For a `kind: knowledge`
   candidate the human-gated drain decides: promote (novel), annotate an existing note
   (matches), no-op (already covered), or drop (thin). A `kind: guidance` candidate
   takes the guidance dispositions instead. See that contract for both sets.
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
