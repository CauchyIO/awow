# MCP catalogue and intake

Approved MCP servers, plus the intake template used to assess new ones.

## Catalogue

See `catalogue.md` for the team's approved-MCP list. Add entries via the intake form.

## Intake

When the team wants to add a new MCP, run through the intake template (`intake-template.md`, landing in v0.2). Until then, the questions to answer:

- **Author and publisher.** Who built this MCP?
- **Exposed tools.** What tools does it expose to the agent?
- **Tool behaviour.** Read or write? Side effects?
- **Blast radius.** Worst-case outcome if the agent calls every tool with adversarial inputs?
- **Data flow.** Personal data? Credentials? Leaves the org boundary?
- **Security precautions.** Auth, access control, rate limiting, logging?

The intake answers go in `mcps/intake/<MCP-name>.md`. A reviewer (security lead + architect) approves or rejects. Approved MCPs are added to `catalogue.md`.

## Wiring approved MCPs into the agent harnesses

Once a server is in `catalogue.md`, each adopter writes it into the harness config files. Two files, same logical server, slightly different shapes:

| Harness | File | Key | Secrets |
| --- | --- | --- | --- |
| Claude Code | `.mcp.json` (repo root) | `mcpServers` | `${VAR}` / `${VAR:-default}` from shell env |
| GitHub Copilot (VS Code) | `.vscode/mcp.json` | `servers` + `inputs` | `${input:id}` — VS Code prompts once, stores in OS keychain |

Example pair for the same Linear server:

```jsonc
// .mcp.json — Claude Code
{
  "mcpServers": {
    "linear": {
      "type": "http",
      "url": "https://mcp.linear.app/sse",
      "headers": { "Authorization": "Bearer ${LINEAR_TOKEN}" }
    }
  }
}
```

```jsonc
// .vscode/mcp.json — Copilot
{
  "inputs": [
    { "type": "promptString", "id": "linear-token", "password": true }
  ],
  "servers": {
    "linear": {
      "type": "http",
      "url": "https://mcp.linear.app/sse",
      "headers": { "Authorization": "Bearer ${input:linear-token}" }
    }
  }
}
```

Each catalogue entry should record the rendered snippet for both harnesses (or `/setup-awow` Step 0 emits them from the catalogue) so adopters can copy without guessing.

### Gotchas adopters hit

- **Unset env vars are fatal.** Claude Code refuses to parse `.mcp.json` if a `${VAR}` has no value and no `:-default`. Always supply a default or document the required export.
- **Approval prompt is per-user.** Both harnesses ask once before activating a project-scoped server. To re-prompt: `claude mcp reset-project-choices` (Claude Code) or "MCP: Reset Trusted Servers" in VS Code's command palette.
- **`${CLAUDE_PROJECT_DIR}` is server-side only.** In `.mcp.json` `command`/`args`, use `${CLAUDE_PROJECT_DIR:-.}` — the variable is set in the spawned server's env, not at config-parse time.
- **Copilot needs Agent mode.** MCP tools don't fire in inline completions or Ask mode.

## Reference

- The full reference: see the intake-template and rollout-playbook tickets in the team's upstream research inventory — these are the source for the v0.2 versions.
- MCP Servers Directory: see `REFERENCES.md`. Cross-reference, don't vendor.
- Claude Code MCP docs: `code.claude.com/docs/en/mcp`.
- Copilot MCP docs: `code.visualstudio.com/docs/copilot/chat/mcp-servers`.
