# Synthesis — the gated drain from inbox into the durable KB

The counterpart to mining. Mining **captures** candidates into `context/kb-inbox/`;
synthesis **drains** them into `context/knowledge-base/`. This is the promotion ritual
made a case-complete contract — and it is **human-gated by default**: nothing lands in
the durable layer without explicit approval.

This is a **contract, not an autonomous routine.** An opt-in unattended mode (a nightly
drain that pushes to a branch) is deliberately *not* part of this contract — see
*Autonomous mode* at the end.

---

## Input

The **committed** candidate files in `context/kb-inbox/` (one durable insight each,
with `source` / `source_ref` / `date` / `suggested_target` frontmatter). The drain reads
committed state only — an uncommitted candidate is not yet in scope.

`_synthesis-log.md` and `README.md` are never candidates.

## Per-candidate disposition

For each candidate, read the KB subfolder its `suggested_target` names (and the
glossary), then decide — by reading the existing notes, not by keyword match — one of:

| Disposition | When | Action |
|---|---|---|
| **Novel** | No existing note covers this. | Write a new note in the target's KB format (descriptive H1, frontmatter-light; `decisions/` uses the ADR header). Confirm or override `suggested_target`. |
| **Matches** | An existing note covers the same area but this adds or sharpens something. | **Annotate/strengthen** the existing note — prefer *append* over rewrite. Do not duplicate the note. |
| **Covered** | An existing note already says this. | **No-op.** Do not churn the note. The value was confirming it's known. |
| **Thin** | Not actually durable, or noise that slipped the mining bar. | **Drop.** Logged, not promoted. A rising drop rate is a signal the policy bar is too low. |

Author novel notes so the durable layer's rules hold: one concept per file, frontmatter-
light, and **no back-links to specific stories** (the board links into the KB, never the
reverse — see `context/knowledge-base/README.md`). Provenance lives in the log and git
history, not in the note body.

## Reconcile

When a candidate contradicts an existing note (not just adds to it), do not silently
overwrite. Surface the conflict, resolve it with the user, and record *why* the resolved
version won. Never import a claim from one note into another to paper over a genuine
disagreement.

## The gate

Present the drain plan before writing: for each candidate, its disposition and target.
Wait for approval. Only on approval:

1. Apply each approved disposition (write / annotate / no-op / drop).
2. Leave a one-line pointer in the source item's board comment for anything promoted:
   `Promoted to context/knowledge-base/<subfolder>/<x>.md`.
3. Append one provenance line per candidate to `context/kb-inbox/_synthesis-log.md`.
4. **Remove the drained candidate file** from `context/kb-inbox/` and commit the removal
   — the durable record is now in `context/knowledge-base/` plus git history.

Unapproved candidates stay in the inbox for a later drain; they are not lost.

## Autonomous mode (out of scope here)

A team may want an unattended nightly drain (like a cloud routine that promotes and
pushes to a `kb-routine/*` branch, git history as the audit trail). That trades the human
gate for automation and is an **opt-in operational choice**, not the awow default — a
template must ship gated. It is deferred to a separate proposal
(`meta/proposals/kb-capture-synthesize-spine.md`, Phase 4). Until then, this drain always
stops at *The gate*.
