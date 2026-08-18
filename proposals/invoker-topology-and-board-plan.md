# Proposal — Hat-aware setup, discovered topology, the invoker profile, and the board plan

**Status:** Accepted — in build (AWO-204 / AWO-205 / AWO-206).
**Inputs:** [context-resolution.md](context-resolution.md) (AWO-61, PR #44: index-form `board.md`, resolution ladder), [spoke-self-registration.md](spoke-self-registration.md) (AWO-133: `.awow/hub.json`, `board-scope.md` named but undefined), [hub-and-spoke-design.md](hub-and-spoke-design.md) (accepted), maintainer session (Casper, 2026-08-18).
**Scope:** three adopter-reported problems, designed together because they share one root — awow models the repo and the team, but not the *person* operating it: (1) `/setup-awow` assumes one undifferentiated driver who holds both product authority and credential access; (2) board-write gates are trusted less than they should be because their output is verbose and inconsistent across flows; (3) real adoption topologies (one PO over two teams and two boards, developers contributing across boards, one board serving multiple teams) have no home in the one-repo-one-team-one-board model.

---

## The three problems, as reported

1. **The setup driver is unclear.** Some steps only a product owner can answer (mission, conventions, board state machine); some only an engineer can (MCP wiring, tokens, bootstrap scripts). The wizard never distinguishes, so a lone engineer is asked to invent the team's mission and a PO is asked to install MCP servers.
2. **Teams adopting want to stay in the loop on board changes** — especially early — but the current gate output is verbose and each flow renders it differently. A durable "proposal document" was considered and rejected: it loses its value the moment the change lands, and it creates a second source of truth next to the board.
3. **Topology permutations are unmodeled.** The invoker is always an individual, never "the team", and the individual's lens (PO of two teams, developer on three boards) determines which context an invocation should land in. Today nothing durable models that individual, and a hub can hold exactly one `board.md`.

## Decisions (maintainer-confirmed 2026-08-18)

| # | Decision | Rejected alternatives |
|---|---|---|
| D1 | The hub's "anchor" is **discovered at setup, never declared**. Orientation questions produce the topology; no upfront ontology choice. | Fixing the anchor to product/value-stream, to the PO personally, to the team, or to the board — all frontload a decision adopters cannot yet make. |
| D2 | Wrong-hat rule is **soft park**: anyone may answer any step; out-of-hat answers are marked provisional and need confirm-by-the-right-hat. | Hard park (stalls on an absent PO; blocks engineer-led adoption). Hybrid-by-consequence (per-step severity taxonomy to maintain). |
| D3 | The invoker is **durably modeled** in a machine-local profile consulted as a resolution-ladder rung. | Roster-derived identity in `members.md` (stale-prone, commits personal mappings). Ephemeral ask-once (re-asks forever — the reported friction). |
| D4 | The canonical gate rendering is the **flat diff-style board plan**: one numbered line per change, `+`/`~`/`-` in a ` ```diff ` fence, counts footer, `details N` drill-down. | Verb-grouped sections (taller, no color). Terraform's full attribute diff (too verbose — the explicit complaint). Durable plan artifacts (two sources of truth). |
| D5 | The profile is **repo-local** (`{PROJECT}/.awow/profile.json`), not user-scope — consistent with the `hub.json` critique: `~` is invasive, sandboxed agents may not reach it, local state should sit inspectable next to the work. Accepted cost: a developer confirms their defaults once per repo. *(Deviation from the session sketch, which said machine-global; flagged for review.)* | `~/.awow/profile.json` machine-global. |
| D6 | **A hub is the unit of shared conventions and curation** — not a team, not a board. Boards relate many-to-many to hubs: one hub can index several boards, and several hubs can each scope onto one shared board. | Team = board = hub equivalence — exactly the identification that produces the reported "we're multiple teams, so do we need multiple boards?" muddle. |

## Pillar 1 — Hat-aware setup

`/setup-awow` already bifurcates cleanly by required knowledge; the split becomes explicit machinery:

- **Orientation on first entry.** Alongside the existing track question ("whole team or just you?"), two concrete questions: *which hat are you wearing here* — `product`, `engineering`, or `both` — and *what should this repo serve* (named boards and teams, not counts). No abstract anchor question, ever. Single team + single board answers collapse to today's flow with zero added ceremony.
- **`needs-hat` labels per step.** Technical: 0 (installer), 1a (read/write surface), 5 (CLAUDE.md bootstrap), 9 (skills review). Product: 1b (board configuration), 2 (mission), 3 (conventions), 4 (members + style), 6 (KB seed), 7 (neighbouring teams), 8 (extras).
- **Soft park (D2).** The wizard walks the invoker through their steps first. Out-of-hat steps may still be answered, but the artefact and `setup-progress.md` both carry a `provisional: needs <hat> confirmation` marker. `/awow-status` and the wizard surface pending confirmations at every entry; confirmation is a one-line approval by someone wearing the right hat, recorded as done.
- **Hand-off briefs.** A parked step generates a one-paragraph brief under `proposals/setup/handoff-<step>.md` naming what is needed and from whom; the recipient runs `/setup-awow` and resumes exactly there. Once `members.md` names curators (Pillar 2), briefs and provisional confirmations address them by default — the "PO owns the core repo, supported by an engineer" instinct, realized as routing rather than ownership.
- **Person-aware resume.** `setup-progress.md` gains `done-by` (name or hat) per step next to the existing checkboxes. The workshop route's fence becomes symmetric: it already keeps technical wiring out of the product meeting; hat labels now also keep product invention away from a lone engineer unless explicitly proxied.

## Pillar 2 — Discovered topology

- **The anchor emerges (D1).** Orientation answers determine the shape. One board: today's singular `context/tooling/board.md`, unchanged. Multiple boards: the wizard writes the AWO-61 index-form `board.md` with sibling `board-<name>.md` specs and records curators per board in `members.md` (the existing `Role:` field; no new ownership file).
- **One repo → one hub, kept as an invariant.** Multi-team/multi-board flexibility lives *inside* the hub (board index) and *across* spokes (each spoke maps to one hub), never as multiple hubs per repo.
- **`context/board-scope.md` finally gets a schema.** Named in three places today, defined nowhere. Minimal frontmatter, spoke-side:

  ```yaml
  board: <name>            # key into the hub's board.md index (or the single board)
  team: <board team>       # board-tool team the items land on
  project: <container>     # optional board project/container
  subpath: <dir>           # optional, monorepo scoping
  ```

  For a single-board hub the file is optional; its absence means "the hub's board".

### Vocabulary — the delineation the confusion feeds on

- **Board** — a tool surface (a Linear team space, an ADO project). Holds items; owns nothing else.
- **Board team** — the routing field *inside* the tool that says where an item lands. A tool artefact, not a people claim.
- **Hub** — the unit of shared context: one conventions set, one mission, one roster, one `board.md` (possibly index-form). The thing setup produces.
- **Team** — the people sharing a hub. awow gives "team" no other machinery meaning; org-chart teams may map 1:1, N:1, or 1:N onto hubs.
- **Curators** — the named individuals answerable for a hub's content: a **product curator** (PO hat) and a **technical curator** (engineering hat). Fields in `members.md`, not the hub's identity — a PO rotation is a one-line edit, which is why D1 refuses to anchor the hub to a person.
- **Invoker** — the individual running a command, carried by the per-repo profile (Pillar 3). Teams never invoke anything.

### The permutations, mapped

What orientation's answers produce, for each reported shape:

| Reported shape | Wiring |
|---|---|
| One team, one board | One hub, singular `board.md`. Today's flow, byte-for-byte. |
| One team / one PO, several boards | One hub; index-form `board.md` with a sibling spec and named curators per board. |
| One PO, two teams with overlapping members, a board each | **One hub** when conventions and curatorship are genuinely shared (the common case — this is the "core repo" instinct): index-form `board.md`, `members.md` rows carry a `Boards:` affiliation so flows can scope people to boards. **Two hubs** only when the teams' conventions actually diverge. |
| One board, several POs / teams | One hub per team; each hub's `board.md` points at the *same* board, scoped by board team / project. See cohabitation below. |
| A developer across N boards | Nothing at hub level. Each of their repos spokes to exactly one hub (`board-scope.md` names its board); the profile carries their default; the ladder resolves the rest. |

**The split rule:** one hub per set of people who share conventions and curators. Split on divergent conventions, never on org-chart labels — context is markdown, so starting with one hub and splitting when conventions actually diverge is cheap, and the wizard says so instead of asking adopters to predict it.

### One board, many hubs — cohabitation

When several hubs scope onto one shared board, each hub's `board.md` (or sibling spec) names its board team / project filter. Flows scope their *reads* to that slice — digests, staleness sweeps, and `/my-work` stay inside the hub's filter — but **duplicate search runs against the whole board**: a duplicate across teams is still a duplicate. Conventions stay per-hub; the board's own hygiene rules (`## Team page conventions` in each spec) are where cohabiting hubs agree on shared etiquette.

### The two seats

The same topology, from each lens the adopters keep asking from:

- **The PO's seat.** Works in the hub (or a docs spoke of it) as product curator: mission, conventions, the board index. `/process-transcript` there climbs the ladder across the whole index — a portfolio meeting can fan items to two boards in one gated plan (per-line `[board]` suffixes, Pillar 4).
- **The engineer's seat.** Works in code spokes; each spoke's `board-scope.md` pins where its items land, so repo work never asks. Their profile answers the off-repo ambiguities (a meeting about the *other* board they serve). Nothing about the hub's multi-board shape leaks into their day until an invocation genuinely spans boards.

## Pillar 3 — The invoker profile and the resolution rung

- **`{PROJECT}/.awow/profile.json`** (gitignored; `.awow/` is established local-state ground): board identity per tool, hats, default board for this repo's hub, confirmation date. Written by setup orientation, or lazily the first time an ambiguity is resolved ("record this as your default here?").
- **The ladder** (refines AWO-61's, adds one rung; board-touching commands climb in order):
  1. Explicit statement in the invocation ("on the Payments board").
  2. Item-ID prefix match against the board index.
  3. Session pin (`.awow/board-session.md`, existing).
  4. Spoke `board-scope.md`.
  5. Invoker default from `profile.json`.
  6. Single-board hub → that board.
  7. Ask once; write the session pin; offer to record in the profile.
- **Fixes the dangling pointer.** `using-awow` says "resolve per §Context resolution in AGENTS.md" but no such section exists anywhere in the repo; AWO-61's AC already claims that section. This ladder is its content — landing it closes the gap the current confusion falls through.
- `/my-work`'s per-invocation "resolve me" starts reading the profile first, asking only on a miss.

## Pillar 4 — The board plan

One grammar, defined in `workitem-write` step 4 — the single funnel every write already routes through — inherited by `/process-transcript` GATE 2, `/daily-checkin`, `/project-plan`, `/project-manager`, and ad-hoc writes. Flows stop hand-rolling gate formats.

```diff
BOARD PLAN · board: Payments [Linear]

+ 1  Story "Add rate limiting to ingest API"   → Backlog
+ 2  Story "Rate-limit config per tenant"      → Backlog
~ 3  AWO-42  body: narrow scope to EU tenants
~ 4  AWO-17  In Progress → In Review
- 5  AWO-99  close — superseded by AWO-42

Plan: 2 add · 2 change · 1 close
```

- **Symbols:** `+` create; `~` any change to an existing item (body edit, state move, field/label); `-` close or cancel. The ` ```diff ` fence gives green/red rendering in every harness that highlights markdown — no ANSI dependency.
- **Numbered lines** address the option verbs: `go` · `skip N` · `details N` · `review` · `cancel`. `review` remains the full walk-through; `details N` is defined below.
- **Multi-board plans:** per-line `[board]` suffix and a per-board breakdown in the footer; single-board plans omit both.
- **Non-gated actions stay out.** Comments and links need no approval today and are not plan lines; they appear in the post-apply `DONE` report (existing shape: Executed / Skipped / Failed / Manual follow-up).
- **The plan is ephemeral.** No durable plan artifact — a written copy is stale the moment the board updates, and the board is the only truth. Draft bodies live where they already do (`proposals/workitems/`, `proposals/setup/`) as the `details` source.

### Line anatomy

`<symbol> <n>  <subject>  <change phrase>  [<board>]` — subject is the item ID for existing items, `<Type> "<Title>"` for creates. The change phrase is generated by rule, not improvised, so flows cannot drift back into private formats:

| Action | Change phrase |
|---|---|
| create | `→ <initial state>`, plus `↳ under <n\|ID>` when parented |
| body edit | `body: <what changes>` — names the section touched (intent / AC), ≤ ~10 words |
| state move | `<from> → <to>` |
| field / label | `<field>: <old> → <new>` |
| close / cancel | `close — <reason>` |

Multiple facets on one item stay on one line, joined with ` · ` (`~ 3 AWO-42 body: narrow to EU · label: area:api`). Hard cap ~100 chars; overflow truncates with `…` — the rest lives in `details`. One item never spans two lines (variant C paired-lines was considered and rejected: taller, and the pre-image belongs in `details`).

### Where the "before" comes from

A diff needs a pre-image. `workitem-write` step 1 (Look first) already reads every touched item; it now *records* what it read — current state, title, and the body section a change targets — as the plan's snapshot. The plan renders from that snapshot, and apply re-verifies it (below). No new storage: the snapshot lives in the session, like the drafts.

### `details N` — the drill-down contract

`details N` prints, per action type, then re-presents the options; it never executes anything:

- **create** — the full draft body exactly as it would land (intent + acceptance criteria + KB link), plus the conventions it was shaped against.
- **body edit** — a true old/new diff of only the touched sections, ` ```diff ` fenced, plus the one-line rationale.
- **move / field** — current value, target value, rationale.
- **close** — reason, and what supersedes it.

Every `details` view ends with a `because:` line — provenance (next section).

### Provenance — the trust mechanism

The rejected proposal-document had one virtue: it showed *why* before anything landed. That function survives as per-line provenance instead of a second artifact: **every plan line must be traceable to a source** — a transcript quote, a check-in line, a board item, a convention — and `details N` surfaces it as `because: <source>`. A line the flow cannot source is a line it may not propose. Terraform's trust comes from determinism; a plan generated by a model can't offer that, so it offers citations. This is the early-adoption answer: the default stays terse, but every line can prove itself on demand, and `review` walks the proofs one by one.

### Apply semantics

- **Per-line independence.** Apply continues past a failure; each line reports individually in the `DONE` shape. No retries beyond one idempotent re-read; failures surface verbatim.
- **Stale-guard.** Each line re-checks its pre-image at apply time — a move re-reads the current state, a body edit re-reads the touched section. On mismatch the line is *not* applied and reports `stale — board changed since plan` with the fresh value; the user re-plans. Never force, never silently merge. (The Terraform analogue: plan against a snapshot, verify preconditions at apply — without a state file or lock.)
- **Intra-plan ordering.** `↳ under <n>` is the only dependency: parents apply before children; a failed parent skips its children, reported as skipped-because-parent-failed. Anything richer than parent/child is a smell the plan is doing `/project-plan`'s job.

## Deliberately not doing

- No hard park anywhere; no per-step severity taxonomy.
- No `manager` hat, no persona system: two hats plus `both` covers setup's actual bifurcation. Anything more re-opens the parked personas feature (`input/PROPOSAL.md` §8) without evidence.
- No per-hub verbosity setting for gates; `details`/`review` are the knobs.
- No state file, lock, or board snapshot store — the stale-guard is a per-line precondition re-check at apply time, nothing more.
- No multiple hubs per repo; no hub-level roster of individuals beyond `members.md` as it stands.
- No new top-level commands; everything lands inside `/setup-awow`, `workitem-write`, and the session-start resolution.

## Open questions

- Hat vocabulary for confirmations: is a name recorded in `done-by` (useful audit) or only the hat (less personal data in a possibly-public repo)? Lean: hat only, name optional.
- Should `details N` also show the convention *diffs* it would violate if edited (cheap now, or defer)? Lean: defer.
- Profile staleness: does anything expire or re-confirm the profile (for example on board index change)? Lean: re-confirm only when a referenced board disappears from the index.
- `process-transcript` for a PO spanning two boards: does orientation ask for a per-flow default, or is per-line `[board]` tagging at the gate enough? Lean: gate tagging is enough; watch real usage.

## Acceptance test

An engineer runs `/setup-awow` alone in a fresh repo: technical steps complete, product steps are answerable but land marked provisional, and a hand-off brief exists; the PO resumes later, confirms or amends, and the provisional markers clear. Orientation for a PO with two teams and two boards produces the index-form `board.md` with two sibling specs and curators recorded. In the resulting hub, a developer whose `profile.json` defaults to board A runs `/process-transcript` on a meeting about board B: the ladder resolves B from an explicit mention, the gate renders one flat diff-style plan with `[board]` suffixes, `details 3` prints one full draft ending in its `because:` source, `skip 2` executes the rest, and no durable plan artifact remains afterwards. If a teammate moved an item between plan and `go`, that line reports `stale` with the fresh value instead of applying. Separately, two hubs scoped onto one shared board keep their digests and `/my-work` inside their own board-team filter while duplicate search still sees the whole board.

## Follow-up work items

- Extend `/setup-awow`: orientation, `needs-hat`/`done-by`/provisional in `setup-progress.md`, hand-off briefs (new issue).
- Board plan grammar in `workitem-write` step 4 + flow gates delegating to it (new issue; coordinate with AWO-121, in progress).
- Invoker profile + ladder rung + `board-scope.md` schema + the §Context resolution landing (new issue; coordinate with AWO-61 PR #44 and AWO-133).
