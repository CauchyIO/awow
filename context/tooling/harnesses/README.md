# context/tooling/harnesses/

Reference instructions per agent harness. One file per supported harness.

`/setup-awow` Step 1a detects which harness the user is on and loads the matching reference. The real signal is which harness the model is running inside; corroborating on-disk signals are `.claude/`, `.github/`, a repo-root `AGENTS.md` with `.codex-plugin/` (Codex), and `.pi/` (Pi).

## Supported harnesses

| File | Harness | Delivery |
|---|---|---|
| `claude-code.md` | Claude Code | plugin + vendored surfaces |
| `copilot.md` | GitHub Copilot | vendored surfaces |
| `codex.md` | Codex | repo-root `AGENTS.md` + `.codex-plugin/` plugin manifest |
| `pi.md` | Pi | repo-root `AGENTS.md` + `package.json` `pi.skills` package |

Claude Code and GitHub Copilot ship in the vendored template channel. Codex and Pi are added per [`pi-codex-harness-support.md`](../../../meta/proposals/pi-codex-harness-support.md), reconciled into hub-and-spoke WI-5: both read the repo-root `AGENTS.md` for zero-install steering, and reach awow's commands as skills through the `dist/` payload — Codex via `.codex-plugin/plugin.json`, Pi via `package.json` `pi.skills`. `tools/gather.py` mirrors `.agents/` to each surface; `tools/sync-dist.sh` publishes `dist/` to the `CauchyIO/awow-dist` marketplace repo.

## Why multiple

The supported harnesses have non-overlapping user bases. Single-harness defaults exclude real audiences; carrying one reference file per harness keeps the starter pack usable for any of them from the same `.agents/` source.

## Adding a new harness

Same shape. The file documents what the harness provides (slash commands? agent skills? hooks?), how `.agents/` mirrors to its surface, and the settings file format.
