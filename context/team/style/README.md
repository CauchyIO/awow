# context/team/style/

Writing-mode guidance — *how* the team writes, separated by surface.

Different surfaces want different voices. Brevity rules differ from prose rules; ticket comments differ from external blog posts. This folder is one file per mode.

## Files

| File | Surface | Voice |
|---|---|---|
| `board-output.md` | Story bodies, feature descriptions, epic bodies | Terse, declarative, structured |
| `comments.md` | Story comments | Transient, focused on current state |
| `placement.md` | Decision tree: which surface should this content go on? | (Companion to `conventions/REQUIRED/output-discipline.md`) |
| `prose.md` | Long-form internal/external (briefs, blogs, docs) | Complete sentences, paragraphs, engineer's actual voice |

## How the agent uses this

When the agent is about to write something, it asks: *which surface?* That determines which style file applies. A blog draft and a story body do not follow the same rules.

The board-output rules are non-negotiable and are also encoded in `context/team/conventions/REQUIRED/output-discipline.md`. The file here in `style/` is the human-readable companion; the file in `conventions/REQUIRED/` is the agent's hard constraint.

## What does NOT live here

- Naming rules (verbs, prefixes, slugs) → `context/team/conventions/`
- Mission / vision / values → at the `context/team/` root
- External brand guidelines → not in this repo (link from `prose.md` if needed)
