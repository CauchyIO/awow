# GitHub Copilot — harness reference

GitHub's coding agent. The second supported harness.

## When `/setup-awow` infers Copilot

Presence of `.github/` directory with `copilot-instructions.md` or `AGENTS.md`, or the user explicitly chooses Copilot.

## What it provides

- `AGENTS.md` — the cross-vendor instruction file standard
- `copilot-instructions.md` — Copilot's native instruction file (older format)
- **Agent skills** — Copilot's equivalent of Claude Code skills. See https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- Chat modes, custom prompts (community-curated set: https://github.com/github/awesome-copilot)
- MCP integration (newer, less mature than Claude Code's)

## How `.agents/` mirrors to `.github/`

`tools/gather.py` copies:

- `.agents/CLAUDE.md` → `.github/AGENTS.md` (rename; same content)
- `.agents/commands/<phase>/<name>.md` → `.github/prompts/<name>.md` or `.github/skills/<name>/SKILL.md` (depending on shape)
- `.agents/skills/*.md` → `.github/skills/<name>/SKILL.md`

The single source of truth is `.agents/`. Edits to `.github/` are overwritten on the next `gather.py` run.

## Slash commands

Copilot does not have slash commands in the same shape as Claude Code, but **agent skills** cover the same ground. A Claude `/setup-awow` slash command becomes a Copilot agent skill that the user invokes by referencing it in chat.

## Reference

- Docs: https://docs.github.com/en/copilot
- Agent skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- Community catalogue: https://github.com/github/awesome-copilot (also in REFERENCES.md)
