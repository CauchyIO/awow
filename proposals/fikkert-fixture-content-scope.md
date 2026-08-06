# Fikkert & Zn. canonical fixture — content scope (AWO-74 pre-build review)

**Status:** PROPOSAL — awaiting Casper's review. AWO-74's AC gates the build on
this review; the project plan's top risk is building the L-sized fixture with
no locked content spec and rebuilding it after first review. Lock this, then
the build is mechanical.

Everything below composes with the sustainable-testing design (§"The canonical
company fixture"): one fictional company every suite draws on, living in
`tests/fixtures/fikkert/`, fully synthetic and committable.

## 1. Company canon (the facts every artefact must agree on)

- **Fikkert & Zn.** — mid-size e-commerce **fulfilment** provider (design-fixed).
  Family firm, ~140 FTE, Dutch market. Clients are webshops; Fikkert stores,
  picks, packs, ships, and handles returns.
- **Team under test: Warehouse Systems** — 6 devs + PO, 2-week sprints,
  GitHub Issues board (design-fixed). Owns **FLOW**, the in-house warehouse
  suite: `flow-intake` (goods receipt), `flow-pick` (pick/pack routing),
  `flow-returns` (returns portal), `flow-bridge` (client-webshop API).
- **People** (invented, review welcome): PO **Marloes Fikkert**; devs
  **Jeroen Baks**, **Sanne de Wit**, **Timo Vermeulen**, **Priya Nair**,
  **Daan Kuiper**, **Aisha El Amrani**. Ops stakeholder: **Henk Fikkert**
  (warehouse manager, source of messy verbal requirements).
- **Standing tensions** (what makes the material realistically messy): a
  peak-season (Q4) capacity theme, a flaky label-printer integration that ops
  keeps reporting as new, and a half-migrated returns flow — recurring
  material across briefs/transcripts so duplicate-detection has real bait.
- Canon lives in `tests/fixtures/fikkert/CANON.md` — the single reference any
  later scenario overlay must not contradict. Anything not in canon is free.

## 2. Tree inventory

**Source material:** the build transforms `tests/fixtures/fikkert/_seed/`
(the former `meta/` workspace, frozen 2026-05-25 — the only complete worked
example of a populated `context/` tree) exactly per its README: keep the
structure, replace every real fact (Cauchy mission, `@hetspookjee`, GitHub
project #3, `awow-test` label) with the §1 canon, refresh conventions
against the current template (the snapshot predates the department layer and
the M365 harness). `_seed/` is deleted in the same change once the fixture
proper exists.

```
tests/fixtures/fikkert/
  CANON.md            # §1 in file form
  context/            # populated variant — passes tools/validate-context.py
  context-stub/       # /setup-awow seed-stub state (deliberate variant, design §fixture)
  board/              # seed script + snapshot for the awow-test-fixture repo
  material/           # messy inputs, all in-universe
```

- **`context/` (populated)**: mission, team roster w/ RACI (the 8 people
  above), and the five REQUIRED conventions (`board-linkage`, `branches`,
  `issue-titles`, `labels`, `output-discipline`) filled with
  Fikkert-specific, non-stub content (e.g. `FLOW-` issue-title prefix,
  `area:intake|pick|returns|bridge` labels) so convention-respect grading has
  real conventions to check against. Structure mirrors the live template —
  never a hand-invented layout.
- **`context-stub/`**: the same tree exactly as `/setup-awow` seeds it —
  stub markers intact. Generated from the live seed, not hand-copied.
- **`board/`**: `seed.sh` (idempotent, `gh` CLI, targets the throwaway
  `awow-test-fixture` repo only) + `snapshot.json` (the same content as
  data, for offline assertions). Seed set: **12 issues** — 8 legitimate open
  items across the four modules, 1 in-progress with branch link, 2
  near-duplicate pairs-in-waiting (the label-printer and returns themes, as
  duplicate-bait), 1 mislabeled/missing-fields item (hygiene bait);
  **labels** per the fixture's own `labels.md`; **2 milestones** (Sprint 41,
  Peak-season readiness).
- **`material/`**: 4 artefacts — refinement-meeting transcript (~2 pages,
  Henk rambling, 3 extractable work items of different right-sizes),
  project brief (returns-portal phase 2, overlaps 1 seeded issue),
  incident/retro transcript (label-printer, tests dedup against the seeded
  theme), short email thread (client escalation via `flow-bridge`). Every
  artefact carries **planted, enumerable graded features** — each extractable
  claim/work item traceable to a source sentence (the design's traceability
  check), each duplicate-bait mapped to the seeded issue it collides with.
  A `material/FEATURES.md` index lists them so rubric authors (AWO-80/84/85)
  cite plants, not vibes.

## 3. Layer-0 drift tests (ship with the fixture, run in CI)

1. Populated `context/` structurally matches the live template (every
   REQUIRED file present and non-stub; no orphans when the template evolves)
   and passes `tools/validate-context.py` — design §fixture, verbatim.
2. `context-stub/` matches the current `/setup-awow` seed-stub state.
3. `board/snapshot.json` schema-checked and internally consistent with
   `seed.sh` (same ids/labels/milestones).
4. `material/FEATURES.md` plants resolve: every referenced source line exists
   in its artefact; every duplicate-bait target exists in the board seed.

## 4. Out of scope (this item)

- Reference banks (≥5 tier-labeled outputs) — phase in with the matrix work
  (design: after sabotage qualification; AWO-82/88 territory).
- Sabotage variants — derived by script from this fixture, never stored
  copies (AWO-77 rules the session-scoped path).
- Scenario overlays (opening/persona/rubric per suite) — owned by
  AWO-80/84/85/86; they compose from this fixture, copy + overlay.
- Actually creating/seeding the `awow-test-fixture` GitHub repo — that is
  AWO-75's disposable-board seam; this item only ships `seed.sh` + snapshot.

## 5. Review asks (Casper)

1. Canon sign-off (§1) — names, product shape, the three standing tensions.
2. Counts (§2) — 12 seeded issues / 4 material artefacts enough for the
   three suites drawing on this, or trim/grow?
3. Confirm `context-stub/` generation from the live seed is acceptable as a
   build step (vs a committed frozen copy).

`session: 17d97cc2-6888-4564-805e-baee9e682f71`
