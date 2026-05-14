# context/tooling/boards/

Reference instructions per board tool. One file per supported board.

`/setup-awow` Step 1 reads the relevant reference based on the board URL the user provides, and uses it to configure `context/tooling/board.md` (the team's actual choice).

## Supported in v0.1

| File | Board tool |
|---|---|
| `linear.md` | Linear |
| `azure-devops.md` | Azure DevOps |
| `jira.md` | Jira (stub — v0.2 fills in) |
| `github-issues.md` | GitHub Issues (stub — v0.2 fills in) |

## Adding a new board

A new board reference goes here as `<tool>.md`. The file documents:

- Hostname pattern (so `/setup-awow` can detect the tool from a URL)
- Work-item hierarchy mapping (Epic / Feature / Story / Task on this tool)
- State machine mapping to the blog's five-state contract
- MCP server and how to wire it
- Labels / tags / branches conventions
- Tips specific to the tool
