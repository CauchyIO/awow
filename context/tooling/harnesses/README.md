# context/tooling/harnesses/

Reference instructions per agent harness. One file per supported harness.

`/setup-awow` Step 1a detects which harness the user is on and loads the matching reference. The real signal is which harness the model is running inside; corroborating on-disk signals are `.claude/`, `.github/`, a repo-root `AGENTS.md` with `.codex-plugin/` (Codex), `.pi/` (Pi), and `.opencode/` or `opencode.json` (opencode).

## Supported harnesses

| File | Harness | Delivery |
|---|---|---|
| `claude-code.md` | Claude Code | plugin (`dist/`, served by the awow repo's marketplace manifest) |
| `copilot.md` | GitHub Copilot | Copilot plugin (`dist/.github/plugin/`) |
| `codex.md` | Codex | repo-root `AGENTS.md` + `.codex-plugin/` plugin manifest |
| `pi.md` | Pi | repo-root `AGENTS.md` + `package.json` `pi.skills` package |
| `opencode.md` | opencode | repo-root `AGENTS.md` + native `.agents/skills/` + `package.json` `main` plugin |
| `m365-copilot.md` | Microsoft 365 Copilot (pilot / experimental) | declarative agent via `gather.py --surface m365` |

Every harness installs the same built payload. Claude Code and GitHub Copilot install from the awow repo, whose marketplace manifest serves `dist/`; Codex, Pi and opencode install from `CauchyIO/awow-dist`, where `tools/sync-dist.sh` publishes that directory. Codex and Pi are added per [`pi-codex-harness-support.md`](../../../proposals/pi-codex-harness-support.md), reconciled into hub-and-spoke WI-5: both read the repo-root `AGENTS.md` for zero-install steering, and reach awow's commands as skills through the payload — Codex via `.codex-plugin/plugin.json`, Pi via `package.json` `pi.skills`. `tools/gather.py` renders `.agents/` into the payload once per harness; nothing is mirrored into a repo's own harness folders. `m365-copilot.md` is a pilot: it targets non-technical users with no repo, via a declarative agent `gather.py --surface m365` emits — see that file for scope and current limits.

## Why multiple

The supported harnesses have non-overlapping user bases. Single-harness defaults exclude real audiences; carrying one reference file per harness keeps the starter pack usable for any of them from the same `.agents/` source.

## Adding a new harness

Same shape. The file documents what the harness provides (slash commands? agent skills? hooks?), how the built payload reaches it, and the settings file format.
