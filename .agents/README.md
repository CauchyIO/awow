# .agents/

The single source of truth for everything the agent reads at session start. This folder is harness-agnostic: `tools/gather.py` builds it into the plugin payloads under `dist/` and `dist-telemetry/`, rendered once per harness — full command copies for Claude Code, a commands-as-skills surface for Codex, Pi and opencode, and the Copilot plugin under `dist/.github/plugin/`. Nothing here is mirrored into this repo's own `.claude/` or `.github/`; commands and skills reach a maintainer's session through the same plugin an adopter installs.

**Edit `.agents/`, then run `python tools/gather.py`.** `gather.py --check` fails CI on any drift between the source and the payloads.

## Layout

| Subfolder | Purpose |
|---|---|
| `AGENTS.md` | The canonical rule set. The root `AGENTS.md`, `.claude/CLAUDE.md` and `.github/*` instruction files are hand-authored pointers to it |
| `commands/` | Slash commands / agent skills, phase-tagged |
| `skills/` | "What good looks like" — declarative markdown the agent references |

## Building the payloads

```bash
python tools/gather.py            # build dist/ and dist-telemetry/
python tools/gather.py --check    # report what would change, do not write
```

## What does NOT live here

- Team context (mission, conventions, members) → `context/team/`
- Tooling configuration → `context/tooling/`
- Generated agent output (drafts, proposals) → `proposals/`
- The maintainer eval runner `/test-awow` → `.claude/commands/` (repo-local, not part of the payload)
