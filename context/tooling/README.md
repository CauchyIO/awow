# Tooling

The team's actual tooling choices live in `board.md` (produced by `/setup-awow` Step 1). The reference files under `boards/<tool>/reference/` and `harnesses/` describe what each tool brings to the agentic operating model; the wizard reads them at setup time and writes the team's resolved choices into `board.md`.

## Files

- `board.md` — the team's actual board spec (single source of truth). Filled by `/setup-awow` Step 1.
- `design-system.md` — pointer to the team's design system (presence + location). Ships as `mode: absent`; filled by `/design-system`. Read by every command that produces an HTML artifact.
- `boards/linear/` — Linear reference (full)
- `boards/azure-devops/` — Azure DevOps reference (full; some v0.2 TODOs)
- `boards/jira/` — Jira reference (skeleton; v0.2 full)
- `boards/github-issues/` — GitHub Issues + Projects reference (skeleton + `gh` CLI alternative)
- `harnesses/claude-code.md` — Claude Code reference
- `harnesses/copilot.md` — GitHub Copilot reference

Each `boards/<tool>/` folder contains a top-level `README.md` indexing the per-section reference files under `reference/` (states, hierarchy, labels, fields, team-page, mcp, cycles/iterations). See `boards/README.md` for the full layout and override model.
