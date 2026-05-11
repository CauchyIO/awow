# Upstream registries

Catalogues of reusable assets (skills, prompts, MCP servers) that this repo's agent can pull from. The team's local repo *links to* and *pulls from* these; it never vendors their contents.

## Posture by version

| Version | Posture | What this file enables |
|---|---|---|
| v0.1 (now) | Reference-only | Documentation. `/setup-awow` ends by pointing the user here. No fetcher. |
| v0.2 | Pull-on-demand | `/awow-add skill <upstream>:<name>` fetches and installs locally as a fork |
| v1.0+ | Federated | Version-pinned, drift-detection, multi-upstream |

## Registries

### Anthropic Skills

- **URL:** https://github.com/anthropics/skills
- **Scope:** Official Claude skill catalogue. Document creation, file operations, data extraction, slack/notion integrations, MCP-server scaffolds.
- **License:** Apache 2.0
- **Lands under:** `.agents/skills/`
- **Pull mechanism (v0.2+):** Git submodule or fetch-and-flatten via `/awow-add skill anthropics:<name>`
- **Last checked:** 2026-05-11

### awesome-copilot

- **URL:** https://github.com/github/awesome-copilot
- **Scope:** Community-curated Copilot prompts, chat modes, agent skills, instruction files. Strongest list for the GitHub Copilot harness.
- **License:** MIT
- **Lands under:** `.agents/skills/` (skills), `.agents/commands/` (prompts), or harness-specific reference in `context/tooling/harnesses/copilot.md`
- **Pull mechanism (v0.2+):** Fetch raw file via `/awow-add prompt awesome-copilot:<name>`
- **Last checked:** 2026-05-11

### MCP Servers Directory

- **URL:** https://mcpservers.org/agent-skills
- **Scope:** Multi-vendor MCP server catalogue plus an agent-skills collection. Cross-references both `.agents/skills/` and `mcps/`.
- **License:** Varies per entry — always check the source repo
- **Lands under:** `mcps/catalogue.md` (for MCP servers) or `.agents/skills/` (for skills)
- **Pull mechanism (v0.2+):** `/awow-add mcp mcpservers:<name>` for MCP entries
- **Last checked:** 2026-05-11

## Adding a registry

When a new upstream catalogue earns its place:

1. Add it as a section above with the same shape: name, URL, scope, license, lands-under, pull-mechanism, last-checked.
2. Add it to the relevant per-domain README (`.agents/skills/README.md`, `mcps/README.md`, or the harness reference).
3. Update `last-checked` annually or when something material changes (license, scope, governance).

## Anti-patterns

- **Vendoring upstream content.** Don't copy a skill into the repo. Link, pull on demand, and fork what you pull. The repo is not a content distributor.
- **Over-pulling.** Every skill read at session start costs context. Pull what you use; leave the rest in the registry.
- **Treating registries as authoritative.** Community content varies in quality. Pulled content becomes a local fork you own.
