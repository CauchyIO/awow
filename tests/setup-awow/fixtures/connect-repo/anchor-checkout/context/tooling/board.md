# Board — Example team (frozen test fixture — the anchor's board)

## Tool & wiring

- Tool: Linear. Team **Example**, issue prefix `EX` — https://linear.app/example-team/team/EX/all
- Surface: the `linear-server` MCP — https://linear.example.invalid/mcp (confirmed 2026-08-20)

## State machine

| Five-state contract | Linear state | Owner of transition |
|---|---|---|
| Backlog / Todo | Backlog, Todo | Human refines into Todo |
| In Progress | In Progress | Agent (on first commit) |
| Done | Done | Agent (on merge) |
