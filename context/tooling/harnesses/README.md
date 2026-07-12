# context/tooling/harnesses/

Reference instructions per agent harness. One file per supported harness.

`/setup-awow` Step 0 detects which harness the user is on (from the presence of `.claude/` or `.github/` directories) and loads the matching reference. Codex (repo-root `AGENTS.md` / `.codex-plugin/`) and Pi (`.pi/`) detection is wired with their plugin manifests (hub-and-spoke WI-5).

## Supported harnesses

| File | Harness | Delivery |
|---|---|---|
| `claude-code.md` | Claude Code | plugin + vendored surfaces |
| `copilot.md` | GitHub Copilot | vendored surfaces |
| `codex.md` | Codex | repo-root `AGENTS.md` (live) + plugin manifest (WI-5) |
| `pi.md` | Pi | extension (WI-5) |

Claude Code and GitHub Copilot ship in the vendored template channel. Codex and Pi are being added per [`pi-codex-harness-support.md`](../../../meta/proposals/pi-codex-harness-support.md), reconciled into hub-and-spoke WI-5; the repo-root `AGENTS.md` that steers Codex ships now, the rest with the manifests. `tools/gather.py` mirrors `.agents/` to each surface.

## Why multiple

The supported harnesses have non-overlapping user bases. Single-harness defaults exclude real audiences; carrying one reference file per harness keeps the starter pack usable for any of them from the same `.agents/` source.

## Adding a new harness

Same shape. The file documents what the harness provides (slash commands? agent skills? hooks?), how `.agents/` mirrors to its surface, and the settings file format.
