# Azure DevOps — team page conventions reference

ADO's "team page" surface is the **team description** under Project Settings → Teams → `<team>`, plus the team's default **Iteration Path** and **Area Path**.

## What a team profile should contain

- **Mission** — one sentence; mirror of `context/team/mission.md`.
- **Members** — name, role, focus area.
- **Default Area Paths** — which scopes belong to this team.
- **Iteration cadence** — sprint length; sprint start day.
- **Links** — to the team's wiki, dashboards, runbooks.

## Wizard responsibilities

**Mode A (from reference).** Generate a draft team description from Steps 2–4 answers. ADO's MCP write surface for team description is limited; emit as manual paste.

**Mode B (assess current).** Read team description if MCP exposes it; otherwise ask the user to paste the current contents.

## What lands in `board.md`

```
## Team page conventions

Team description status: <populated | pending-manual-paste | empty>.
Default Area Paths owned: <list>.
Default Iteration Path root: <…>.
Divergence from reference: <none | list>.
```
