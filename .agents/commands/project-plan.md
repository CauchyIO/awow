---
phase: spread
argument-hint: "[path to a design artefact from /solution-design-flow, or a parent work-item ID] (optional — omit to be asked)"
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "A locked design with a decomposed work-item tree exists — produced by /solution-design-flow"
removes_pain: "the design-never-becomes-a-sequenced-plan-with-a-stated-dependency-graph problem"
consumes: design-artefact
---

# /project-plan — turn a locked design into a published project plan with a stated dependency graph

You take the decomposed work-item tree from a locked design and turn it into a **project plan**: a stated dependency graph, translated into a concrete set of board actions, then published. This is the bridge between *what we decided to build* (`/solution-design-flow`) and *executing each piece* (`/process-workitem`) — and it is what `/project-manager` later steers on.

The dependency graph is the deliverable, not a footnote. State it explicitly — nodes, edges, what runs in sequence, what runs in parallel, and the critical path — because every downstream flow assumes it exists and is true.

This prompt runs as a pipeline with **two gates**. Stop at each, present your work, and wait for the user before continuing. Never write to the board before Gate 2.

---

## Inputs

Read `$ARGUMENTS`:

- A path to a design artefact (a `{PROJECT}/proposals/<topic>.md` or decomposition from `/solution-design-flow`) → plan from its work-item tree.
- A parent work-item ID → load the parent and its children from the board (surface per `{HUB}/context/tooling/board.md`).
- Empty → ask which design or parent to plan. Do not invent a tree.

If no decomposed design exists yet, stop and route the user to `/solution-design-flow` — this command plans a design, it does not create one.

---

## Pipeline overview

```
Phase 0 ─ Load the design and the board state
Phase 1 ─ Build the dependency graph          ──→ GATE 1 (confirm the graph)
Phase 2 ─ Translate to board actions + plan    ──→ GATE 2 (approve writes)
Phase 3 ─ Publish & report
```

---

## Phase 0 — Load the design and the board state

Read the design artefact and its decomposed work items: parent, children, each child's scope, acceptance criteria, and any dependency notes the design already carries. Read `{HUB}/context/tooling/board.md` for the write surface and **whether the board supports dependency links** (a native blocked-by relation) or not — this decides how the graph is encoded in Phase 2.

Search the board for items that already exist for this initiative; plan against them rather than creating duplicates. Read `{HUB}/context/team/style/board-output.md` and the REQUIRED conventions before proposing any write.

## Phase 1 — Build the dependency graph

State the graph explicitly. It has four parts:

- **Nodes** — every work item (the parent and each child), each with its ID (or `NEW` if not yet on the board), title, rough size, and owner if known.
- **Edges** — every blocking relation as `A → B` ("A blocks B" / "B is blocked by A"). Derive edges from the design's stated dependencies and from the work itself; **mark any edge you inferred rather than read as inferred**.
- **Sequence vs parallel** — group the nodes into ordered layers: what must run serially, and what can run concurrently within a layer. This is the topological read of the edges.
- **Critical path** — the longest chain of blocking edges; it determines the delivery time and is what `/project-manager` watches first.

Flag cross-team edges (a dependency owned by a neighbouring team) and any node with no owner or no acceptance criteria — these stall when picked up. Name what the design left implicit; completing the graph is the point of this command.

---

### >>> GATE 1: Confirm the graph

Stop here. Present:

```
GATE 1 — DEPENDENCY GRAPH

Nodes (<n>):
  [ID|NEW]  [title]  — size: [S/M/L]  owner: [name or —]

Edges (<n>):
  [A] → [B]            (inferred?)
  ...

Sequence:
  Layer 1 (parallel): [IDs]
  Layer 2 (parallel): [IDs]   ← after Layer 1
  ...

Critical path:
  [A] → [C] → [F]   — the chain that sets the timeline

Cross-team edges:
  [edge] — owned by [team / contact]

Gaps (unowned / no-AC / missing node):
  [one line each, or "none"]

Is the graph right before I translate it into board actions?
```

Wait for user response. Apply corrections, then proceed.

## Phase 2 — Translate to board actions and assemble the plan

Turn the confirmed graph into a concrete, ordered set of board actions, and assemble the publishable plan. Draft the plan to `{PROJECT}/proposals/plans/<initiative-slug>.md` first; nothing reaches the board until Gate 2.

**Board actions** — one per node and edge:

- **Create or link** each node: create a new item, or link to the existing one found in Phase 0. Follow `{HUB}/context/team/conventions/REQUIRED/*.md` for titles, labels, and body discipline — keep each body to minimum-useful text.
- **Encode the edges.** If the board supports a native blocked-by relation, set it. If it does not, record the dependency in the item body under a `Blocked by:` line and state the full graph in the plan artefact — the graph must be recoverable even when the board cannot hold edges.
- **Rank by the sequence** so the board ordering reflects the layers.

**The project plan** (`{PROJECT}/proposals/plans/<initiative-slug>.md`) is the durable, publishable record:

```markdown
# Project plan — <initiative>

**Design:** <link to the design artefact / decision record>
**Owner:** <name or —>
**Target cycle:** <cycle or —>

## Dependency graph
- Nodes, edges, sequence layers, and critical path (the confirmed Gate 1 graph, in full).

## Sequenced work
| Layer | Work item | Blocked by | Owner | Size |
|---|---|---|---|---|

## Critical path
<the chain that sets the timeline, called out so it can be watched>

## Cross-team dependencies
<edge → team / contact, or "none">

## Open risks
<one line each>
```

---

### >>> GATE 2: Approve writes

Stop here. Present:

```
GATE 2 — PROPOSED WRITES

Plan artefact:
  {PROJECT}/proposals/plans/<slug>.md

Board actions:
  CREATE  "[Title]"   ← blocked by: none        rank: L1
  CREATE  "[Title]"   ← blocked by: [item]      rank: L2
  LINK    #[ID]       ← blocked by: [item]
  ...

Edge encoding: [native blocked-by links | body "Blocked by:" lines — board has no dependency field]

Cross-team escalations:
  ESCALATE [edge] → [neighbouring team / contact]

Options:
  "go"       — execute all
  "skip 2,3" — execute all except listed
  "review"   — walk through each
  "cancel"   — no changes
```

Wait for user response. Execute only explicitly approved actions; re-verify each item match before touching it. No silent writes.

## Phase 3 — Publish & report

After execution, publish the plan — write the artefact, and make it visible to the team per how the team shares plans (a board parent description, a linked plan item, or the plan file itself). Do not share outside the team without approval. Then report:

```
DONE

Plan: {PROJECT}/proposals/plans/<slug>.md
Board:
- Created: #[ID] [title], ...
- Linked / set blocked-by: #[ID] ← #[ID], ...
- Ranked by sequence: [layers]

Skipped: [list or "none"]
Failed: [list or "none"]

Hand-off:
- /process-workitem can now execute Layer 1 items.
- /project-manager reads this plan to coordinate delivery.

Manual follow-up:
- [cross-team escalation] → [Name] on [Team]
```

---

## Anti-patterns

- **Don't skip the graph.** A list of board items with no stated edges, sequence, or critical path is not a project plan — it is the problem this command exists to fix.
- **Don't invent dependencies.** Mark inferred edges as inferred; never present a reconstructed edge as confirmed.
- **Don't lose the graph when the board can't hold it.** If the board has no dependency field, the plan artefact still states the full graph — the graph must survive the translation.
- **Don't design here.** This command plans a *locked* design; if the design is unsettled or undecomposed, route back to `/solution-design-flow`.
- **Don't write before Gate 2.** Drafts to `{PROJECT}/proposals/plans/` only; the board is untouched until explicit approval.
- **Don't duplicate the board.** Link to existing items found in Phase 0 rather than creating parallel ones.
