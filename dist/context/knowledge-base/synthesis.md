# Synthesis — the gated drain from inbox into the durable KB

The counterpart to mining. Mining **captures** candidates into `context/kb-inbox/`;
synthesis **drains** them into `context/knowledge-base/`. This is the promotion ritual
made a case-complete contract — and it is **human-gated by default**: nothing lands in
the durable layer without explicit approval.

This is a **contract, not an autonomous routine.** An opt-in unattended mode (a nightly
drain that pushes to a branch) is deliberately *not* part of this contract — see
*Autonomous mode* at the end.

**Paths.** The `inbox` and `kb_root` locations resolve via
`context/tooling/knowledge-base.md`. The literals below (`context/kb-inbox/`,
`context/knowledge-base/`) are the defaults; if that config declares different
locations, use those.

---

## Input

The **committed** candidate files in `context/kb-inbox/` (one durable insight or rule
each, with `kind` / `source` / `source_ref` / `date` / `suggested_target` frontmatter,
plus `source_quote` when `kind: guidance`). The drain reads committed state only — an
uncommitted candidate is not yet in scope.

`kind` selects the disposition set: `knowledge` (the default, and the only kind before
`/update-context` existed) takes *Per-candidate disposition* below; `guidance` takes
*Guidance candidates*. A candidate with no `kind` is `knowledge`.

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

## Guidance candidates (`kind: guidance`)

A guidance candidate is a rule the team obeys, not a fact about the system. It promotes
into `context/team/`, never into `kb_root`. `/update-context` is its only feeder, and
the drain sees it only when the user deferred it at that command's gate or it arrived
`UNROUTED`.

Read the `suggested_target` file **and its siblings** before deciding — the tree is not
deterministic and a rule can plausibly belong in `conventions/` or `style/`. Then:

| Disposition | When | Action |
|---|---|---|
| **Novel** | The target file states no rule covering this. | Append the rule to the target file, in that file's own format. |
| **Sharpens** | An existing rule covers the same ground, less precisely. | Rewrite that rule in place. Do not append a near-duplicate beside it. |
| **Covered** | An existing rule already says this. | **No-op.** The value was confirming it is written down. |
| **Contradicts** | An existing rule says the opposite. | Do not resolve it yourself. Surface both, with the candidate's `source_quote`, and let the user choose which survives and why. |
| **Unroutable** | `suggested_target` is `UNROUTED`, or names a file that does not exist. | Leave the candidate in the inbox and report it. Do not drop it — a growing unrouted pile is the signal that the tree is missing a home. |
| **Thin** | Scoped to one file, one ticket, or one person's preference. | **Drop.** Logged, not promoted. |

Three rules bind every guidance disposition:

- **Never create a convention or style file.** No destination means *unroutable*, always.
  There is no disposition that ends in a new file, at either end of the pipeline.
- **Cap each destination file at ten rules.** Count the unit that file already uses — a
  `## Rule N` section, a row of a rules table, an item of a numbered list. At the cap,
  propose a **merge** of two existing rules or a **replacement** of the one this
  candidate supersedes, and show that diff. Never an eleventh append. `conventions/
  REQUIRED/` is read at the start of every session, so an extra rule there taxes every
  future turn in the repo.
- **Show `source_quote` verbatim at the gate.** A candidate without one is malformed:
  report it and leave it in the inbox.

Provenance for guidance differs from the KB's. A promoted guidance rule carries a
one-line HTML comment immediately after it:

```markdown
<!-- Added YYYY-MM-DD via /update-context: "<source_quote>" -->
```

The KB forbids in-note provenance because the durable layer is frontmatter-light and the
board links into it. `context/team/` has neither property — it is read by agents mid-
session, where knowing a rule came from a named human sentence is what makes it
challengeable. `/process-retro` writes the same shape for the same reason.

## The gate

Present the drain plan before writing: for each candidate, its disposition and target.
Wait for approval. Only on approval:

1. Apply each approved disposition (write / annotate / no-op / drop, or the guidance
   equivalent).
2. Leave a one-line pointer in the source item's board comment for anything promoted:
   `Promoted to context/knowledge-base/<subfolder>/<x>.md`. Skip this for `kind:
   guidance` — it has no source board item; its provenance is the HTML comment beside
   the landed rule.
3. Append one provenance line per candidate to `context/kb-inbox/_synthesis-log.md`.
   For a guidance candidate, name the destination path and the disposition.
4. **Remove the drained candidate file** from `context/kb-inbox/` and commit the removal
   — the durable record is now in `context/knowledge-base/` or `context/team/`, plus git
   history.

Unapproved candidates stay in the inbox for a later drain; they are not lost.

## Autonomous mode (out of scope here)

A team may want an unattended nightly drain (like a cloud routine that promotes and
pushes to a `kb-routine/*` branch, git history as the audit trail). That trades the human
gate for automation and is an **opt-in operational choice**, not the awow default — a
template must ship gated. It is deferred to a separate proposal
(`meta/proposals/kb-capture-synthesize-spine.md`, Phase 4). Until then, this drain always
stops at *The gate*. This binds both lanes, and it is why
`/update-context` ships with no `--auto` mode either: a rule written into
`context/team/` unattended is binding on everyone who opens a session afterwards.
