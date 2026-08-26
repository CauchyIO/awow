# JIT context — fill on first need, shrink the wizard

**Status:** Draft (2026-08-26)

## Problem

Across three consecutive adoption attempts at different organisations, the same failure repeated: setup is experienced as a chore — too much friction, no direct outlook on reward — so it doesn't happen, and adoption stalls before the first command ever runs. `/setup-awow` is waterfall: it front-loads every decision (mission, conventions, members, neighbouring teams) before the adopter has seen any value. Questions like *"What is your team's mission?"* land as far-off ceremony when the person just wants to process a transcript.

The hypothesis from those engagements: a flow that works right off the bat, decently, invites incremental investment; a wizard that demands investment up front invites abandonment.

## Direction

Invert the dependency. Commands do not require setup output — they fill context on first need.

### The contract

1. **Absence is the marker.** Team-data context files (`gather.py` `TEAM_DATA_CONTEXT_PATHS`) stay absent until first needed. No stub scaffolding: the existing rule stands — *"a generic stub is worse than absence; commands branch on absence, but cannot branch on boilerplate"* (`tools/gather.py:167-169`). We considered vendoring marked stubs instead ("assess that they're still unwritten") and rejected it: a machine-readable unwritten-marker must survive partial edits and payload evolution, which is the vintage-drift problem all over again (CAU-1338). Absence needs no marker and no drift handling.
2. **The payload ships working defaults only where a working default exists.** That is `gather.py`'s existing `template` category (`design-system.md`, `mining-policy.md`, …) — unchanged, extended only when a genuine default emerges.
3. **Consuming commands flip prerequisites to fill-on-first-need.** When a command reads an absent context file, it makes a one-line offer in the style CAU-1333 established (infer-and-state, escape hatch, silence means the default): fill it now (a one-liner, or a draft inferred from the repo), proceed without, or skip-and-note. A "fill it now" yes is the approval for that context write — the gate moves to the moment of need instead of a wizard step. The clearest current counter-example is `refinement-prep`'s declared prerequisite `"{HUB}/context/team/mission.md exists"`; under this contract that line is replaced by a fill offer.

### `/setup-awow` end-state

The wizard shrinks to the jobs that genuinely cannot be defaulted or deferred:

- **Step 0** — installer / install-shape.
- **Step 1a** — board surface wiring (MCP install, auth, board URL) plus the CAU-1332 preflight, which guards exactly this remaining core.
- **Spoke/anchor registration** (per the CAU-1410 model).

Steps 2 (mission/profile), 3 (conventions), 4 (members + style), 6 (KB seed), 7 (neighbouring teams), and 8 (extras) dissolve into their consuming commands as JIT fills. `/setup-awow` survives as the wire-me-up / repair / deepen entry point — no longer the front door to value. Step 1b (board capture) already half-follows the pattern: `workitem-write` carries an absent-`board.md` fallback today; deepening capture remains an explicit Step 1b re-run.

### Prune `context/company/`

The folder is team-data (never in the payload) and mostly dead:

- `stakeholders.md`, `raci.md` — no command reads them; delete from the tree and from Step 7's scaffolding.
- `neighbouring-teams.md` — two real readers (`/process-transcript`, `/solution-design-flow`), both absence-tolerant; goes JIT (first cross-team boundary in a transcript triggers the offer to record the team).
- `company/department.md` — the spoke→department backlink written by `/setup-department`; load-bearing, stays.

Coordinate the folder's final shape with CAU-1410's secondary-contexts model rather than deleting drive-by.

## Relation to in-flight work

- **CAU-1333 (PR #73)** — the foundation. Its infer-and-state, one-review-gate style is the house style for every JIT fill offer. Merge first.
- **CAU-1332 (PRs #71/#76)** — the preflight guards what *remains* of setup. This proposal is the reconciliation criterion for the #73/#76 overlap in Step 1a: an explicit surface pick fires only on genuine ambiguity (multiple candidates, or a sole candidate failing verification); a single verified candidate is adopted with the stated escape hatch.
- **CAU-1331** (read-only until an explicit apply gate) — composes: JIT fills are the per-file form of the same gate.
- **CAU-1339** (`/enroll-awow`) — unaffected; machine enrollment is upstream of context.

## First slice

1. Land the contract in `.agents/AGENTS.md` (the reflex: absent context file → fill-on-first-need offer, never a hard prerequisite).
2. Convert the consumers with declared prerequisites (`refinement-prep` first) and the two `neighbouring-teams.md` readers.
3. Prune `company/` scaffolding from `/setup-awow` Step 7 and delete the two dead files.
4. Rewrite `/setup-awow`'s step map to the shrunken core; steps 2–8 become pointers to where each fill now lives.

Out of scope: retiring Step 1b capture modes, the anchor rename itself (CAU-1410), payload/template changes in `gather.py`.
