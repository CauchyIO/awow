# Board — Example team (frozen test fixture)

## Tool & wiring

- Tool: Linear. Team **Example**, issue prefix `EX` — https://linear.app/example-team/team/EX/all
- Surface: the `linear-server` MCP.

## State machine

| Five-state contract | Linear state | Owner of transition |
|---|---|---|
| Backlog / Todo | Backlog, Todo | Human refines into Todo |
| In Progress | In Progress | Agent (on first commit) |
| In Review | In Review | Agent (on PR open) |
| Done | Done | Agent (on merge) |
