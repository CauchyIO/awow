# Claude Code — harness reference

Anthropic's official CLI for Claude. The recommended harness for this operating model.

## When `/setup-awow` infers Claude Code

Presence of `.claude/` directory in the repo root, or the user explicitly chooses Claude Code.

## What it provides

- Slash commands (e.g. `/setup-awow`, `/refinement-prep`)
- Skills (markdown files the agent reads at session start)
- Hooks (shell commands executed on harness events)
- MCP server integration
- `~/.claude/CLAUDE.md` (user-global) + repo `CLAUDE.md` (project-scoped) instruction files

## How `.agents/` mirrors to `.claude/`

`tools/gather.py` copies:

- `.agents/CLAUDE.md` → `.claude/CLAUDE.md`
- `.agents/commands/<phase>/<name>.md` → `.claude/commands/<name>.md` (phase prefix dropped in the surface)
- `.agents/skills/*.md` → `.claude/skills/*.md`

The single source of truth is `.agents/`. Edits to `.claude/` are overwritten on the next `gather.py` run.

## Settings

`.claude/settings.json` is the harness configuration: permissions, MCP servers, environment variables, hooks. `/setup-awow` Step 0 writes the MCP block for the team's board.

## Reference

- Docs: https://docs.anthropic.com/en/docs/claude-code
- Skills directory: https://github.com/anthropics/skills (also in REFERENCES.md)
