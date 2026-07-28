# Azure DevOps — MCP reference

**Source docs:** Microsoft's Azure DevOps MCP server at [github.com/microsoft/azure-devops-mcp](https://github.com/microsoft/azure-devops-mcp) (or as included in the official Azure MCP bundle). The repo README has the current install steps and required env vars (PAT, organisation, project).

Read-write semantics required. ADO has a per-organisation rate limit; `/process-workitem` and `/refinement-prep` batch their writes to stay under it.

## Install — Claude Code

TODO — confirmed install command. The Azure DevOps MCP is typically a local stdio server (not HTTP), so the shape is closer to:

```bash
claude mcp add azure-devops-server -- npx -y @azure/azure-devops-mcp
```

Confirm against the repo README before running. Auth is via a PAT passed through env vars; see the README.

## Install — Copilot

TODO — confirmed `.vscode/mcp.json` snippet. For a stdio-based MCP the shape is roughly:

```json
{
  "servers": {
    "azure-devops-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@azure/azure-devops-mcp"],
      "env": { "ADO_PAT": "${env:ADO_PAT}" }
    }
  }
}
```

Confirm field names and env-var binding against the Azure DevOps MCP repo README.

## Verify

1. List work items from a known project to verify read access.
2. A no-op write on a scratch work item (set a field to its current value) to verify write access.
3. Record the verification status in `context/tooling/board.md`.

## Branch naming

ADO does not auto-generate branch names. Convention:

`issue/{TEAM}-{number}` — e.g. `issue/PROJ-1042`

Or per-user: `{user}/{TEAM}-{number}-{slug}`. Pick one team-wide.

## Rate limits

ADO has a per-organisation API rate limit. The seed commands batch writes to stay under it; if you customise heavily, watch for `429` responses.
