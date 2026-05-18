# context/tooling/boards/

Best-practice reference setup per board tool. One subfolder per supported board; the per-team choice lives at `context/tooling/board.md`.

`/setup-awow` Step 1 reads the relevant reference based on the board URL the user provides, walks the team through configuring each section (or capturing what's already there), and writes `context/tooling/board.md` with the team's actual spec.

## Supported in v0.1

| Folder | Board tool | Depth |
|---|---|---|
| `linear/` | Linear | Full reference. Greenfield-to-running without leaving the wizard. |
| `azure-devops/` | Azure DevOps | Full reference; some sections marked TODO for v0.2. |
| `jira/` | Jira | Skeleton. Mode B (assess current) is the expected path; v0.2 fills in Mode A. |
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
    team-page.md         # team page / project description conventions
    mcp.md               # MCP install for Claude Code + Copilot, verify checklist
    cycles.md or         # only if the tool has a cycle/iteration concept worth
    iterations.md        # documenting separately from states.md
```

`/setup-awow` reads the files individually so it can surface one section at a time and let the team accept / override / skip each independently.

## What gets written to `context/tooling/board.md`

Both modes (A — from reference, B — assess current) produce the same artefact shape:

```
# Board — <team name>

## Tool & wiring          # tool family, URL, MCP/CLI surface, verification status
## State machine
## Hierarchy
## Label taxonomy
## Required fields
## Team page conventions
## Cycles / iterations    # if applicable
## Divergence from reference   # populated by Mode B; empty for Mode A
```

The agent reads this file whenever it needs to know what a label means, which states are terminal, or where in the hierarchy a new issue belongs. **`context/tooling/board.md` is the single source of truth for the team's board.** The references under `<tool>/reference/` are not consulted at runtime — only the wizard reads them at setup time.

## Mode A vs. Mode B

`/setup-awow` picks the mode by counting closed issues on the board:

- **Mode A — Set up from reference.** Greenfield or under-configured (fewer than 10 closed issues). The wizard walks the team through the reference, asks accept / override / skip per section, and applies the configuration via the MCP where supported. Where the MCP cannot mutate the config (e.g. Linear Free workflow states, ADO process templates), the wizard produces a manual checklist and re-verifies after the user confirms.
- **Mode B — Assess and capture current.** Established board (≥10 closed issues). The wizard pulls the actual state machine, hierarchy, labels, and fields from the MCP and captures them into `board.md`. It diffs the capture against the reference and surfaces gaps — not to force adoption, but so the team can decide whether to close each gap, override the reference, or accept the divergence. Resolved decisions land in the `## Divergence from reference` section of `board.md`.

Both modes produce `board.md` with the same section headings, so the agent never has to know which mode produced the file.

## Override model

The reference can be overridden at two layers, in precedence order:

1. **Enterprise override.** A parent organisation that wants to ship its own board standards drops them in `.agents-overrides/tooling/boards/<tool>/reference/` next to the adopter team's `.agents/` directory. Files in this folder supersede the starter pack's reference of the same name. The wizard always tells the user which reference layer it is reading from for each decision (e.g. *"using `.agents-overrides/tooling/boards/linear/reference/labels.md` (enterprise override) as the starting point"*).
2. **Team override.** Captured directly in `context/tooling/board.md` itself. The wizard reads the reference, the team picks accept / override / skip per section, and any overrides land in the `## Divergence from reference` block (Mode B) or as inline notes within the relevant section (Mode A). Once `board.md` is written, the runtime agent reads only it; the references are not consulted again until the next wizard run.

There is no "team-level override file" between the two — the team's overrides live in the single source-of-truth file (`board.md`). This keeps the read path simple: at runtime the agent reads one file; at setup time the wizard composes the references with the team's choices and writes that file.

## Adding a new board

A new board reference goes here as `<tool>/`, following the layout above. At minimum, each file must:

- Cover its concern for that tool.
- Tell the wizard which choices to surface (Mode A) and how to assess current state (Mode B).
- Show the shape that lands in `context/tooling/board.md`'s corresponding section.

Linear's `reference/` files are the worked example. Match their shape; depth can grow over time.
