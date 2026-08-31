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

## How `.agents/` reaches Claude Code

Through the awow plugin. `tools/gather.py` builds `.agents/` into `dist/` — `commands/` and `skills/` as full copies, `hooks/` for the session reflex — and the marketplace manifest in the awow repo serves that directory, so `/plugin marketplace add CauchyIO/awow` and `/plugin install awow` deliver the commands, skills and hooks to any repo. Path tokens in the prompt bodies render to `${CLAUDE_PLUGIN_ROOT}` at build time; `{ANCHOR}` and `{PROJECT}` resolve at runtime through the session reflex.

Nothing is copied into a repo's `.claude/`: the team's own `CLAUDE.md` there is theirs (bootstrapped by `/setup-awow` Step 5), and awow never regenerates it. A legacy vendored tree still mirrors `.agents/` into `.claude/` with its own `tools/gather.py`; that route is retired for new installs.

## Settings

`.claude/settings.json` is the harness configuration: permissions, MCP servers, environment variables, hooks, and the project-scope plugin enablement. `/setup-awow` Step 1 writes the MCP block for the team's board.

## Reference

- Docs: https://docs.anthropic.com/en/docs/claude-code
- Skills directory: https://github.com/anthropics/skills (also in REFERENCES.md)
