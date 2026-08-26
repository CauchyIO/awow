# context/company/

The surface that bridges the team to the rest of the organisation. Who's involved beyond this team, and where this team hangs in the wider structure.

## Files

| File | Purpose |
|---|---|
| `neighbouring-teams.md` | 1° teams — those whose work directly intersects ours. Filled on first need: the first cross-team boundary a transcript or design touches records the team it named. Each neighbouring team writes its own summary; ours records the boundary. |
| `department.md` | Optional backlink written by `/setup-department` in a registered team repo — names the department and its repo. Absent in a standalone installation. |

## How the agent uses this

- Neighbouring-team entries tell the agent who to *push to* when a change on this team's board affects another team (per the cross-team visibility principle), and let `/process-transcript` and `/solution-design-flow` recognise team names and ownership boundaries.
- `department.md` resolves the department for the OKR cascade.

Nothing here is scaffolded up front. Per the fill-on-first-need contract in the agent instructions, absence is the normal starting state and commands offer the first entry at the moment a boundary appears.

## What does NOT live here

- Internal team members → `context/team/members.md`
- Detailed knowledge of how another team works → that's *their* team profile, not ours; we summarise here, they own the depth.
- Project artefacts shared with stakeholders → `input/quarterly/` or the codebase, not here.

## Maintenance

If a neighbouring team's entry feels stale, the fix is to ask that team to update it — not to rewrite their summary ourselves.
