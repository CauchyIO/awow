# .agents/

The single source of truth for everything the agent reads at session start. This folder is harness-agnostic; `tools/gather.py` emits **pointer stubs** in `.claude/` (Claude Code surface) and `.github/` (GitHub Copilot / AGENTS.md surface).

A pointer stub is a tiny file: harness-required frontmatter (description, name) plus a one-line body telling the agent to read the canonical source under `.agents/`. The stub carries no substantive content. **Edit `.agents/`, then run `python tools/gather.py`.** Stubs are overwritten on the next gather.

> **Why pointers, not copies or symlinks:** copies drift; symlinks fail on Windows and can't carry per-surface frontmatter. Pointer stubs have nothing to drift — the only thing gather syncs is the harness discovery metadata, and `gather.py --check` flags any divergence.

## Layout

| Subfolder | Purpose |
|---|---|
| `CLAUDE.md` | The team's primary instruction file. Mirrored to `.claude/CLAUDE.md` and `.github/AGENTS.md` |
| `commands/` | Slash commands / agent skills, phase-tagged |
| `skills/` | "What good looks like" — declarative markdown the agent references |

## Generating the surfaces

```bash
python tools/gather.py            # mirror .agents/ to both surfaces
python tools/gather.py --check    # report what would change, do not write
```

## What does NOT live here

- Team context (mission, conventions, members) → `context/team/`
- Tooling configuration → `context/tooling/`
- Generated agent output (drafts, proposals) → `proposals/`
