# Proposal — KB capture→synthesize spine (durable intake + tunable policy + drain)

**Status:** Draft (built, awaiting review) — Phases 1–3 implemented; open questions resolved (`kb-inbox/` name, separate `mining-policy.md`). Phase 4 (feeder unification, autonomous drain, tuning loop) still deferred.

---

## Look-first check (done)

- awow already owns the **front half** of a KB ingestion pipeline. The shared gather
  (`context/tooling/activity-collection.md`) produces one day snapshot; the mining
  lens (`context/knowledge-base/mining.md`) deep-projects it into candidates; and
  `/daily-routine` Phase 3 writes those to `kb-candidates/YYYY-MM-DD.md`. Two other
  feeders (`/process-workitem`, `/process-transcript`) already route durable content
  toward `context/knowledge-base/` via the promotion ritual.
- The **staging surface is ephemeral.** `kb-candidates/` is gitignored (see
  `.gitignore`), one file **per day**, and discarded after review. Promotion is the
  manual ritual in `context/knowledge-base/README.md` — a human reads the day file
  and says which entries to promote. There is no committed hand-off between "extracted"
  and "promoted", and nothing survives a day that wasn't promoted the same day.
- The **selectivity bar is hardcoded.** `mining.md` fixes the qualifies/does-not test
  and a `~5`-candidate cap in prose. There is no lever an adopter can tune, and no
  signal that tells them whether the bar is set too high or too low.
- The **full pattern is well-understood** from teams already running it: extraction
  (mining, transcripts, backload) writes one-file-per-candidate into a **committed**
  intake; a tunable policy drives what gets kept; a drain moves the inbox into the
  durable KB (promote / reconcile / synthesize / heal) with git history as the audit
  trail; a tuning loop nudges the policy from a yield signal. This proposal is the
  awow-portable, prompt-driven, **human-gated** generalisation of that spine's
  **information-gathering half** — the query-side KB agent and its serving/gateway
  infrastructure are out of scope for a template repo.
- This proposal continues the open thread in
  [shared-activity-collection-lenses](shared-activity-collection-lenses.md) ("`/kb-mine`
  standalone still open") — it does not re-litigate the gather; it upgrades what
  happens to a candidate **after** it is mined.

---

## Problem

Mining a day is only useful if the durable knowledge it surfaces reliably *lands*.
awow's current path leaks at the hand-off:

- **Same-day-or-lost.** A candidate lives in `kb-candidates/<date>.md` (gitignored).
  If it isn't promoted before that scratch is cleared, the insight is gone. There is
  no committed backlog of "extracted but not yet promoted."
- **Per-day granularity fights promotion.** One file holds the whole day's candidates,
  so a promotion decision is all-or-scan; there is no per-candidate unit to move,
  annotate, or defer independently, and no per-candidate provenance.
- **No tuning surface.** The selectivity bar is prose baked into `mining.md`. An
  adopter whose runs are all noise (bar too low) or all silence (bar too high) has no
  lever to turn and no yield signal to turn it against.
- **Promotion is unstructured.** The ritual says "extract into the right subfolder and
  leave a pointer," but there is no contract for the recurring hard cases: a candidate
  that *matches* an existing note (annotate vs. rewrite), one *already fully covered*
  (no-op, don't churn), or two candidates that *contradict* each other.

Net: awow can *find* durable knowledge but has no durable place to *stage* it, no lever
to *tune* what it finds, and no contract for the *drain*. The three are one spine.

## The shape (proposed)

**Capture into a committed inbox. Tune what's captured with a policy. Drain the inbox
into the KB through a synthesis contract — human-gated.**

```
activity-collection.md ─▶ mining.md ──(reads)──▶ mining-policy.md   (the tunable lever)
   (gather once)            (deep project)              │
                                   │                    ▼
                                   └──── emits one-file-per-candidate ────▶ context/kb-inbox/
                                                                              (COMMITTED intake;
                                                                               source + suggested_target
                                                                               frontmatter per file)
                                                                                     │
                                                            synthesis.md  ◀──(drains)─┘
                                                            (promote / reconcile / synthesize / heal)
                                                                     │  GATE (human approval)
                                                                     ▼
                                                            context/knowledge-base/
                                                            (+ _synthesis-log.md provenance)
```

Three additions, all in awow's idiom — prose contracts under `context/`, board- and
provider-agnostic, human-gated by default:

- **`context/kb-inbox/` — a committed intake surface.** One file per candidate,
  `YYYY-MM-DD-<source>-<slug>.md`, with lightweight frontmatter (`source:` =
  `mine|transcript|workitem`, `source_ref:` = the issue/PR/transcript it came from,
  `date:`, `suggested_target:` = `architecture|patterns|runbooks|decisions|glossary`).
  Frontmatter is allowed **here** precisely because the inbox is transient staging, not
  the durable layer (which stays frontmatter-light per its README). A `_synthesis-log.md`
  is an append-only provenance log, never a candidate. This replaces the ephemeral
  `kb-candidates/<date>.md` as the staging layer: extraction still writes per run, but
  each surviving candidate lands as its own committed file that survives until drained.
- **`context/knowledge-base/mining-policy.md` — the tunable lever.** Lifts the
  selectivity bar out of `mining.md`'s prose into a small policy with frontmatter dials
  (`selectivity`, `categories`, `max_candidates_per_run`, `max_candidates_per_item`)
  plus the keep/drop rubric and examples. `mining.md` *reads* the policy instead of
  hardcoding the bar. An adopter tunes one file; the mining contract is unchanged.
- **`context/knowledge-base/synthesis.md` — the drain contract.** Defines how a staged
  candidate becomes durable: for each inbox file decide **novel** (write the note),
  **matches** (annotate/strengthen — prefer append over rewrite), **covered** (no-op,
  don't churn), or **thin** (drop, logged); reconcile contradictions between touched
  notes; append a provenance line to `_synthesis-log.md`; remove the drained inbox file.
  This is the existing promotion ritual made explicit and case-complete — **still
  gated**: nothing lands in `context/knowledge-base/` without human approval.

## Positioning decision — upgrade the hand-off, keep everything upstream

The gather and the mining projection are **done and unchanged**. This proposal touches
only what happens to a candidate after `mining.md` selects it.

- **`kb-inbox/` supersedes `kb-candidates/` as the staging layer.** Same role (pre-
  promotion review), but committed, per-candidate, and provenance-stamped, so a
  candidate can survive across days and be promoted independently. The per-day scratch
  file is retired.
- **The policy is a lever, not a new stage.** `mining.md` already applies a selectivity
  test; this only makes that test's dials editable in one place.
- **Synthesis is the promotion ritual, made a contract.** It does not introduce a new
  authority — a human still approves every write into the durable layer. It gives the
  agent a deterministic disposition for each candidate instead of ad-hoc judgement.
- **Autonomous nightly drain is explicitly NOT proposed here.** An unattended drain that
  promotes and pushes to a branch is an operational choice a team makes on its own repo;
  for a template the default must be human-gated. An opt-in autonomous mode is a *later,
  separate* proposal, layered on top of `synthesis.md` — not part of this spine.

So: **the inbox is the durable staging primitive; the policy is the one lever over what
gets staged; the synthesis contract is the gated drain — and the gather/mining half is
untouched.**

## What changes

| Artefact | Change |
|---|---|
| **`context/kb-inbox/`** (new) | Committed intake surface. `README.md` (lifecycle + file format + frontmatter schema), `_synthesis-log.md` (append-only provenance), and `YYYY-MM-DD-<source>-<slug>.md` candidate files. Committed on purpose — the drain reads committed state. |
| **`context/knowledge-base/mining-policy.md`** (new) | Tunable extraction policy: frontmatter dials (`selectivity`, `categories`, caps) + the keep/drop rubric + examples, lifted out of `mining.md`. |
| **`context/knowledge-base/synthesis.md`** (new) | The drain contract: per-candidate disposition (novel/matches/covered/thin), reconcile, provenance-log, remove drained file. Human-gated. The promotion ritual in `knowledge-base/README.md` points to it. |
| **`/kb-synthesize`** (new command) | The invokable wrapper over `synthesis.md` — loads the inbox, plans dispositions, runs the approval gate, applies. The drain's entry point, mirroring how `/kb-mine` wraps `mining.md`. |
| `context/knowledge-base/mining.md` | Reads `mining-policy.md` for the selectivity bar/caps instead of hardcoding them; emits **one committed file per candidate into `context/kb-inbox/`** instead of one gitignored `kb-candidates/<date>.md`. |
| `/daily-routine` (Phase 3) | Deep projection now emits into `context/kb-inbox/`; the promotion gate points at `synthesis.md`. Behaviour-preserving otherwise. |
| `context/knowledge-base/README.md` | Promotion-ritual section references `synthesis.md` (the case-complete drain) and the inbox as the staging layer. |
| `.gitignore` | Drop `kb-candidates/` (retired). `context/kb-inbox/` is **committed** (not ignored). `activity/` stays ignored. |
| `/process-workitem`, `/process-transcript` | (Optional, follow-up) also emit durable-but-unshaped insight into `context/kb-inbox/` as feeders, instead of only inline-promoting — unifies all feeders on one intake. |

## Portability check (the whole point)

- **Board / provider:** unchanged — this touches only post-mining artefacts, which are
  already board-agnostic (they carry a `source_ref`, not a provider query).
- **Adopter with only a digest today:** unaffected. `kb-inbox/` and the policy are
  additive; an adopter who never mines simply has an empty inbox.
- **Enterprise override:** the new contracts are ordinary `context/` files; they inherit
  the existing `.agents-overrides/` precedence with no new override surface.
- **Human-gated default:** no autonomous write path is introduced, so no adopter
  inherits an unattended-push posture by adopting this spine.
- **Frontmatter discipline:** frontmatter appears **only** in the transient inbox; the
  durable layer stays frontmatter-light, so the KB README's authoring law is preserved.

## Phasing

1. **Introduce `context/kb-inbox/`** (README + format + `_synthesis-log.md`), and point
   `mining.md` / `/daily-routine` Phase 3 at it (one committed file per candidate).
   Retire `kb-candidates/` from `.gitignore`. *(Done.)*
2. **Lift the selectivity bar into `mining-policy.md`;** have `mining.md` read it. No
   behaviour change at default dial values — this is a refactor of where the knob lives.
   *(Done.)*
3. **Write `synthesis.md`** (the case-complete, human-gated drain) and its invokable
   wrapper **`/kb-synthesize`**, re-point the promotion ritual in
   `knowledge-base/README.md` at it, and weave the spine into `/setup-awow` Step 6.
   *(Done.)*
4. **(Later, separate proposal) Unify the other feeders** (`/process-workitem`,
   `/process-transcript`) on the inbox, and/or an **opt-in autonomous drain mode** and
   a **yield-log + tuning** loop over `mining-policy.md`. Out of scope here.

## Accepted risks

- **A committed inbox can accrete un-drained candidates.** Mitigated by the drain being
  part of the daily routine and by `synthesis.md`'s "thin → drop" disposition; a
  staleness sweep over `kb-inbox/` (like the KB's 90-day link check) can be added if it
  becomes a problem.
- **Frontmatter in the inbox is a second format to keep honest.** Bounded: it is a tiny
  fixed schema, lives only in the transient layer, and never leaks into the durable KB.
- **Three new contract files is more surface to maintain.** Mitigated: each replaces or
  formalises something that already exists implicitly (staging, selectivity bar,
  promotion ritual) rather than inventing a new data path.

## Open questions

1. **Inbox vs. candidates naming.** Adopt `kb-inbox/`, or align with awow's existing
   `kb-candidates` vocabulary (e.g. a committed `kb-candidates/`)? *(Resolved: `kb-inbox/` —
   "inbox" reads as a durable backlog, "candidates" read as day-scratch.)*
2. **Policy home.** `context/knowledge-base/mining-policy.md`, or fold the dials into
   `mining.md`'s frontmatter? Leaning a separate file — a lever an adopter edits should
   not sit inside the contract that reads it.
3. **Should Phase 4's autonomous-drain and tuning loop be one follow-up proposal or two?**
   (Defer to when Phases 1–3 land.)
4. **Do the transcript/workitem feeders migrate to the inbox in this proposal or the
   follow-up?** Leaning follow-up — keep this spine to the mining feeder first.
