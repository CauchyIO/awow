# Agent instructions (.claude/)

The canonical rules for this repo live in [`.agents/AGENTS.md`](../.agents/AGENTS.md) — read it first. Commands are under `.agents/commands/`, skills under `.agents/skills/`, conventions and context under `context/`.

Claude Code does not discover those folders directly. Commands and skills reach a session through the **awow plugin**, whose marketplace is this repo (`.claude-plugin/marketplace.json` serves `dist/`, built by `tools/gather.py`). To exercise a branch's payload before it merges: `python tools/gather.py && claude --plugin-dir dist`.

The one repo-local command is `/test-awow` in `commands/` — the maintainer eval runner over `tests/<suite>/`.
