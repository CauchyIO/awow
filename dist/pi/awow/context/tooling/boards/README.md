# context/tooling/boards/

Best-practice reference setup per board tool. One subfolder per supported board; the per-team choice lives at `context/tooling/board.md`.

`/setup-awow` picks the reference from the board URL, prints its install snippet, observes the live board with reads only, and writes `context/tooling/board.md` under the section headings the reference names.

## Supported in v0.1

| Folder | Board tool | Depth |
|---|---|---|
| `linear/` | Linear | Full reference. |
| `azure-devops/` | Azure DevOps | Full reference; some sections marked TODO for v0.2. |
| `jira/` | Jira | Skeleton. |
| `github-issues/` | GitHub Issues + Projects v2 | Skeleton + `gh` CLI alternative to the MCP. |

## Layout per board

Each `<tool>/` folder follows the same shape:

```
<tool>/
  README.md              # one-screen index; when /setup-awow picks this tool
  reference/
    states.md            # five-state contract → tool's workflow states
    hierarchy.md         # L1–L4 mapping to the tool's primitives
    labels.md            # label/tag taxonomy with type: / area: / status:
    fields.md            # priority, estimate, iteration, assignee
    duplicates.md        # the tool's dedup features + limits; search-before-create recipe
    team-page.md         # team page / project description conventions
    mcp.md               # MCP install for Claude Code + Copilot, verify checklist
    cycles.md or         # only if the tool has a cycle/iteration concept worth
    iterations.md        # documenting separately from states.md
```

`/setup-awow` reads `mcp.md` for the install snippet and the verify checklist, and the other files for the shape of each `board.md` section and the defaults it proposes when the board shows no pattern of its own.

## What gets written to `context/tooling/board.md`

Setup observes the live board and writes this shape:

```
# Board — <team name>

## Tool & wiring          # tool family, URL, MCP/CLI surface, verification status
## State machine
## Hierarchy
## Label taxonomy
## Required fields
## Avoiding duplicates    # the tool's dedup limits + the team's search-before-create recipe
## Team page conventions
## Cycles / iterations    # if applicable
## Divergence from reference   # where the observed board departs from the reference
```

The agent reads this file whenever it needs to know what a label means, which states are terminal, where in the hierarchy a new issue belongs, or how to check the board for an existing issue before creating one. **`context/tooling/board.md` is the single source of truth for the team's board.** The references under `<tool>/reference/` are not consulted at runtime — only `/setup-awow` reads them.

## Observation, not configuration

`/setup-awow` never changes the board. It reads the actual state machine, hierarchy, labels, fields and cycles through the wired surface, writes them into `board.md`, and notes where the observed board departs from the reference under `## Divergence from reference`. A section the surface cannot answer reads `unknown — not observable`, and a reference default carried into `board.md` ends its line with `(reference default)`, so no default reads as the team's observed rule. Where the board shows no pattern of its own (a new board), the conventions it proposes come from the reference defaults, marked as proposals for the team to strike or keep. Configuring the board itself — creating states, labels or fields — stays a human action in the board's UI.

## Override model

The reference can be overridden at two layers, in precedence order:

1. **Enterprise override.** A parent organisation that wants to ship its own board standards drops them in `.agents-overrides/tooling/boards/<tool>/reference/` next to the adopter team's `.agents/` directory. Files in this folder supersede the starter pack's reference of the same name. Setup says which reference layer it read for each section.
2. **Team override.** Captured directly in `context/tooling/board.md` itself. Setup writes what it observed, the team edits the file, and departures from the reference live in the `## Divergence from reference` block. Once `board.md` is written, the runtime agent reads only it.

There is no "team-level override file" between the two — the team's overrides live in the single source-of-truth file (`board.md`). This keeps the read path simple: at runtime the agent reads one file; at setup time `/setup-awow` composes the observed board with the reference's shape and writes that file.

## The lifecycle contract (optional section in `board.md`)

`/board-lifecycle` governs the project layer only when `board.md` carries a `## Lifecycle` section declaring the team's shapes and horizon rules. Its documented form:

```markdown
## Lifecycle

| Shape | Horizon rule | On expiry |
| --- | --- | --- |
| shape:engagement | contract / SOW end date | Needs decision |
| shape:campaign | target date | Needs decision |
| shape:system | scheduled scope review (quarterly) | Needs decision |

Exception status: Needs decision (reversible; renewal restores the prior status, closure is human).
Tripwire: 2 unresolved cycles → initiative At risk, rollup marked unverified.
```

Rules the section encodes: every project carries exactly one mutually exclusive `shape:*` label (applied by project template); each shape names the date that ends the project's authorization; a missing horizon is itself an exception; expiry moves a project into the reversible exception status via an approved plan — never an automatic close; and activity timestamps are never the staleness signal. Teams may rename shapes, add shapes, or pick a different exception status name — `/board-lifecycle` reads this section rather than hardcoding the defaults.

## Adding a new board

A new board reference goes here as `<tool>/`, following the layout above. At minimum, each file must:

- Cover its concern for that tool.
- Say what to observe on the board and which defaults to propose when the board shows no pattern.
- Show the shape that lands in `context/tooling/board.md`'s corresponding section.

Linear's `reference/` files are the worked example. Match their shape; depth can grow over time.
