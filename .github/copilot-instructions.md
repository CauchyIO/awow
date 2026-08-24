# Agent instructions (.github/)

The canonical rules for this repo live in [`.agents/AGENTS.md`](../.agents/AGENTS.md) — read it first. Commands are under `.agents/commands/`, skills under `.agents/skills/`, conventions and context under `context/`.

GitHub Copilot does not discover those folders directly. Prompts and skills reach a session through the awow Copilot plugin (`copilot plugin marketplace add CauchyIO/awow`), which `tools/gather.py` builds into `dist/.github/plugin/`; `.github/plugin/plugin.json` here is that plugin's manifest source.
