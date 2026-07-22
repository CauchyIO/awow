---
name: kb-synthesize
description: "Use when mined knowledge candidates are piling up unpromoted, or the user asks to drain the KB inbox, review staged candidates, or fold recent learnings into the durable knowledge base."
---

# /kb-synthesize — drain the inbox into the durable knowledge base

You run the **synthesis drain**: read the committed candidates in `{HUB}/context/kb-inbox/`,
decide each one's fate against the existing KB, and — **on explicit approval** — promote
the survivors into `{HUB}/context/knowledge-base/`. This is the back half of the pipeline whose
front half is `/kb-mine` (capture); this command is capture's counterpart (synthesize).

**One drain, one source of truth.** The disposition rules — how a candidate is judged
(novel / matches / covered / thin), how contradictions are reconciled, what the gate
requires, and how a drained file is cleared — are defined once in
`{HUB}/context/knowledge-base/synthesis.md`, falling back to
`../../context/knowledge-base/synthesis.md`. This
command only sequences that contract; it does not restate the rules, so it stays correct
as synthesis evolves.

**Writes the durable KB — but only past the gate.** Unlike `/kb-mine` (which proposes
only), this command *does* write into `{HUB}/context/knowledge-base/`. It never does so without
explicit approval: it presents the full drain plan and waits.

**Paths.** The KB `inbox` and `kb_root` locations resolve via
`{HUB}/context/tooling/knowledge-base.md`, falling back to
`../../context/tooling/knowledge-base.md` (defaults `{HUB}/context/kb-inbox/`,
`{HUB}/context/knowledge-base/`). `synthesis.md` honours the same config, so this command
inherits any relocation automatically.

---

## Pipeline overview

```
Phase 0 ─ Load inbox
Phase 1 ─ Plan dispositions (per synthesis.md)   ──→ drain plan
Phase 2 ─ GATE (approval)  ──→ promote / annotate / no-op / drop  ──→ {HUB}/context/knowledge-base/
```

---

## Phase 0 — Load inbox

Read the **committed** candidate files in `{HUB}/context/kb-inbox/` (skip `README.md` and
`_synthesis-log.md`). If a file is present but uncommitted, warn and skip it — the drain
operates on committed state (`synthesis.md`, *Input*).

Read each candidate's `kind`. Absent means `knowledge`. Keep the two lanes separate from
here on: they take different disposition sets and land in different trees. Report the
split in one line (`4 knowledge, 1 guidance`) so the user knows what is about to be
judged against what.

If the inbox holds no candidates, say so and stop — there is nothing to drain. Point the
user at `/kb-mine` to produce some.

Accept an optional filter argument (e.g. a date `YYYY-MM-DD` or a source) to drain only a
subset; default is the whole inbox.

---

## Phase 1 — Plan dispositions

For each loaded candidate, follow
`{HUB}/context/knowledge-base/synthesis.md`, falling back to
`../../context/knowledge-base/synthesis.md`,
exactly: read the KB subfolder its `suggested_target` names (and the glossary), then
assign a disposition — **novel** (write a new note), **matches** (annotate/strengthen an
existing note), **covered** (no-op), or **thin** (drop) — and flag any candidate that
*contradicts* an existing note for reconciliation.

For `kind: guidance` candidates, follow that contract's *Guidance candidates* section
instead: read the `suggested_target` file **and its siblings**, then assign **novel**,
**sharpens**, **covered**, **contradicts**, **unroutable**, or **thin**. Count the rules
in the destination first — at ten, the plan carries a merge or a replacement, never an
eleventh append. A candidate with `suggested_target: UNROUTED`, or one naming a file
that does not exist, is **unroutable**: it stays in the inbox and is reported. Never
create a convention or style file to give a candidate somewhere to go.

Do not write anything yet. Assemble the **drain plan**: for each candidate, its
disposition, its target path, and (for contradictions) the conflict to resolve.

---

## Phase 2 — The gate, then apply

Present the drain plan and **wait for approval** — this is the promotion gate; do not
cross it on your own.

For every guidance candidate in the plan, show its `source_quote` verbatim next to the
diff that would land. A rule the user approves without seeing the sentence it came from
is guessed, not approved. A guidance candidate with no `source_quote` is malformed —
report it, leave it in the inbox, and do not offer it for approval.

On approval, apply per `synthesis.md`, *The gate*:

1. Apply each approved disposition (write / annotate / no-op / drop).
2. Leave a `Promoted to {HUB}/context/knowledge-base/<subfolder>/<x>.md` pointer in the source
   item's board comment for anything promoted.
3. Append one provenance line per candidate to `{HUB}/context/kb-inbox/_synthesis-log.md`.
4. Remove each drained candidate file and commit the removal.

Candidates the user does not approve stay in the inbox for a later drain — they are not
lost. Reconcile contradictions *with* the user; never silently overwrite a note.

---

## Behavioral boundaries

- **One drain definition.** All disposition/reconcile/gate rules live in `synthesis.md`;
  this command must not diverge from them.
- **Gated writes only.** No write into `{HUB}/context/knowledge-base/`, no board comment, and no
  inbox removal before explicit approval.
- **Never create a convention or style file.** A guidance candidate with no existing
  destination is *unroutable* and stays in the inbox. Promotion moves a rule into a file
  someone already decided to keep; it never invents one.
- **Committed state only.** Drain committed candidates; never an uncommitted file.
- **Human-gated by default.** This command is the interactive drain. An unattended nightly
  mode is out of scope (see `synthesis.md`, *Autonomous mode*).
