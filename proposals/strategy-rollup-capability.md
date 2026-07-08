# The strategy layer as an awow capability — bets on the board, rolled up weekly

**Status:** DRAFT — awaiting approval · **Date:** 2026-07-08 · **Validation instance:** the Cauchy `linear` repo (Q3 2026 OKR cycle)

## Outcome (intended)

A team that has named strategic bets can see, every week, **which bets moved and why — read off the board, never re-derived from memory.** People keep doing normal board work (issues under projects, status transitions the lifecycle already maintains); the *only* new human act is a bounded weekly line per engagement, agent-pre-filled. Everything above that — the project→KR links, the per-bet rollup, the cycle-level re-bet — is agent mechanics. Admin sustains itself because the input has a visible output: the contributor watches "their" bet's number move.

## Context

1. **awow is wired below the "what," and now (at one adopter) above it — but the two layers don't touch at runtime.** The delivery chain (`solution-design-flow → project-plan → refinement-prep → process-workitem → digests`) assumes the *what* is decided. The Cauchy instance built `/strategy-flow` (formation: bets → battery-hardened KRs, two gates) and ran a real cycle through it: five bets locked, KRs drafted, a projects-as-bets portfolio translated. What does not exist — anywhere — is the **runtime linkage**: no convention ties a board project to the KR it serves, no ritual carries the off-board client delta onto the board, no command rolls board reality up into per-bet movement.

2. **The digests cannot be the rollup — until the data is board-resident.** `daily-checkin` maps a day to the board; `weekly-digest` aggregates board activity. The strategic delta at a consultancy is precisely the ~70% that is *not* on the board (client stacks, client repos). Bolting a bets section onto the digests inherits their blind spot. The fix (validated in the Cauchy framework work) is to **put the missing signal on the board first** — a weekly status line per engagement project — after which the digest layer reads it for free.

3. **The board contract is the right seam.** `context/tooling/board.md` is already the single pointer every board access resolves through, and `context/quarterly/` is already the declared home of OKR artefacts ("outcome → epic → feature → story, outcome-down"). The capability is mostly *filling in the seam both already gesture at*.

## Thesis — split by what each layer is good at

| Layer | What it is | Built as |
|---|---|---|
| **Linkage contract** | every L2 project carries `Serves: <KR-ids>` (or `BAU`); emergent work classified on arrival (`Contribution:` / `BAU` / `drift`) | context contract + one line in the board-linkage discipline |
| **Capture ritual** | weekly engagement line: five bounded questions per engagement project, agent pre-fills from the ~30% it sees, lead corrects in ~5 min — events and deltas, **never hours** | command + convention |
| **Rollup read** | weekly: per bet, per KR — state, Δ, evidence links, flags (missing line = chased = red) | command (mechanical, no judgement) |
| **Re-bet** | per cycle: grade KR *movement* (not plan adherence) → a fixed decision set: one double-down, one kill/park, one reallocation, one new risk | command (the judgement layer) |

The human supplies bets and judgement; the agent supplies structure, memory, and the challenge battery. Nothing here creates a second planning surface — the board stays the single source of truth; the OKR document in `context/quarterly/` is the only new artefact class.

## Proposal — four stages, smallest first

**Stage 0 — upstream `/strategy-flow` as-is.** It exists in the Cauchy instance, has survived a real Gate-1/Gate-2 cycle, and is board-agnostic already (it reads `context/quarterly/` + the board contract). Copy up, gather into `dist/`.

**Stage 1 — the linkage contract.** Extend the `context/tooling/board.md` template (and `boards/*/reference/hierarchy.md`) with an **OKR-linkage section**: where the quarterly OKR doc lives (`context/quarterly/strategy-okrs-<period>.md`), the `Serves:` header convention on L2 projects, the on-arrival classification of emergent work, and the orphan/coverage tests (every project → a KR or explicit BAU; every bet → ≥1 project). Opt-in and config-gated like `architecture-aware-development`: absent a quarterly OKR doc, nothing fires.

**Stage 2 — the weekly line.** New command `/engagement-line` (name open): for each engagement project the caller leads, draft the five-question line from visible activity (repo, board, recent transcripts), present for correction, post as a project comment. The questions are fixed: (1) movement vs. the project's stated outcome, (2) adoption/way-of-working signal, (3) what flew in + its classification, (4) commercial signal, (5) impact evidence banked. Guardrails: no timesheets; a draft to correct, never a blank form.

**Stage 3 — the reads.** `/bet-rollup` (weekly, mechanical): walk the OKR doc → projects via `Serves:` → weekly lines + issue movement → emit the per-bet table + flags. `/strategic-review` (per cycle): consume the rollups, force the four-decision output, log the re-bet into `context/quarterly/`. The weekly digest gains a one-table bets section that *reuses* `/bet-rollup` output rather than recomputing it.

## Boundaries

- **awow ships mechanics, never content.** KR text, targets, and any private split (which KRs live on a private team/board) are adopter-side. The contract only says *where* the linkage lives.
- **Instance-first, like every capability.** Validate the full loop at Cauchy for one cycle (Q3), then generalize what survived contact and ship in the next plugin minor. The Cauchy instantiation is deliberately allowed to run ahead of this proposal.
- **No new board objects.** Lightweight `Serves:` links, not initiative layers — promotion to a tool's native initiative/portfolio object is an adopter ADR after a proven cycle, not part of this capability.

## Acceptance (for the Q3 validation instance)

1. Every active project on the instance board carries `Serves:` or `BAU`; the orphan list is empty or explicit.
2. ≥2 engagement projects receive an agent-pre-filled weekly line for 4 consecutive weeks, each corrected in ≤10 min.
3. `/bet-rollup` produces the weekly per-bet table read at the team's weekly — with **zero** statuses re-derived from memory in that meeting.
4. One `/strategic-review` runs mid-cycle and outputs the four decisions.
5. The generalization diff back into awow (this proposal → commands + contract) is written from what the instance actually needed, not from this draft.
