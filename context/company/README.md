# context/company/

The surface that bridges the team to the rest of the organisation. Who's involved beyond this team, who owns what, who needs to know what.

## Files

| File | Purpose |
|---|---|
| `stakeholders.md` | People outside the team whose work depends on or supplies into the team's |
| `neighbouring-teams.md` | 1° teams — those whose work directly intersects ours. Each neighbouring team writes its own summary; these are stubs |
| `raci.md` | Who owns what across the agentic operating model |

## How the agent uses this

- Stakeholder list lets the agent route cross-team work correctly during refinement (`/refinement-prep`) and surface cross-team dependencies in transcripts (`/process-transcript`).
- Neighbouring-team summaries tell the agent who to *push to* when a change on this team's board affects another team (per the cross-team visibility principle).
- RACI lets the agent attribute ownership decisions correctly.

## What does NOT live here

- Internal team members → `context/team/members.md`
- Detailed knowledge of how another team works → that's *their* team profile, not ours; we summarise here, they own the depth.
- Project artefacts shared with stakeholders → `input/quarterly/` or the codebase, not here.

## Maintenance

Each team writes its own summary. If a neighbouring team's stub feels stale, the fix is to ask that team to update it — not to rewrite their summary ourselves.
