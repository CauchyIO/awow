# Azure DevOps — state machine reference

ADO's workflow has more states than the five-state contract. Each ADO process template (Agile / Scrum / CMMI / Basic) names them differently; the convention below uses **Agile** names and notes the variants.

## Mapping (Agile process)

| Five-state contract | ADO state(s) | Notes |
|---|---|---|
| Backlog / Todo | `New` then `Approved` | Approved = refined and ready to pick up. |
| In Progress | `Active` (Agile) / `Committed` (Scrum) | Agent moves on commit. |
| In Review | `Resolved` + `status:needs-review` tag | ADO has no native "In Review" state on Agile; use `Resolved` with a tag. |
| Blocked | `Active` + `status:blocked` tag | Modelled as a tag, not a state. |
| Done | `Closed` | Terminal. |

ADO also has `Removed` (cancelled). Treat as terminal-non-success, sibling of `Closed`.

## Transition ownership

| Transition | Owner | Trigger |
|---|---|---|
| `New` → `Approved` | Human | Refinement: estimate, area path, iteration set. |
| `Approved` → `Active` | Agent | First commit. |
| `Active` → `Resolved` | Agent | PR opened with link. |
| `Resolved` → `Closed` | Agent | PR merged + reviewer-approved. |
| any → `Blocked` (tag) | Agent flags; human confirms | External dependency. |
| any → `Removed` | Human | Scope drop. |

## Wizard responsibilities

**Mode A (from reference).** ADO workflows are template-customised per project. The MCP cannot mutate the process template; surface a manual checklist for the user to run in **Project Settings → Process** and re-verify after confirmation.

**Mode B (assess current).** Read the project's actual workflow via the MCP. Surface deviations from the table above (extra states like `Investigating`, `Pending`, etc.) and ask the user to map each deviation to a five-state-contract slot.

## What lands in `board.md`

```
## State machine

ADO process template: <Agile | Scrum | CMMI | Basic | custom>.

| Five-state contract | ADO state | Owner |
|---|---|---|
| Backlog / Todo | New, Approved | Human approves |
| In Progress | Active | Agent (on commit) |
| In Review | Resolved + status:needs-review | Agent (on PR open) |
| Blocked | Active + status:blocked | Agent flags |
| Done | Closed | Agent (on merge) |

Divergence from reference: <none | list>.
```
