# context/tooling/harnesses/

Reference instructions per agent harness. One file per supported harness.

`/setup-awow` Step 0 detects which harness the user is on (from the presence of `.claude/` or `.github/` directories) and loads the matching reference.

## Supported in v0.1

| File | Harness |
|---|---|
| `claude-code.md` | Claude Code |
| `copilot.md` | GitHub Copilot |

Both ship from day one. The team can use one or both; `tools/gather.py` mirrors `.agents/` to both surfaces.

## Why two

Claude Code and GitHub Copilot have non-overlapping user bases. Single-harness defaults exclude one of the real audiences. Supporting both from day one keeps the starter pack usable for either.

## Adding a new harness

Same shape. The file documents what the harness provides (slash commands? agent skills? hooks?), how `.agents/` mirrors to its surface, and the settings file format.
