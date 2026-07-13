# Pi — harness reference

The Pi coding agent. It has no slash-command mechanism and no `Skill` tool, so awow reaches it through an in-process extension that registers skill paths and injects a session bootstrap.

## When `/setup-awow` infers Pi

A `.pi/` directory (the installed extension), or the user explicitly chooses Pi. (The wizard's detection wiring lands with the extension — see Status.)

## What it provides

- No native repo-root instruction-file convention — the extension injects awow's bootstrap at session start
- Native skill discovery via `skillPaths` registered by an in-process extension; **no `Skill` tool** — the model reads a `SKILL.md` with its `read` tool
- **No slash commands** — awow flows are invoked by name
- Lifecycle callbacks (`session_start`, `session_compact`, `agent_end`, `context`) in the extension's TypeScript

## How `.agents/` reaches Pi

- `.agents/commands/*` and `.agents/skills/*` → the shared commands-as-skills surface rendered from the `dist/` payload (`gather.py --surface pi`), registered via `skillPaths`.
- Instructions reach Pi through the extension's injected bootstrap, not a committed file: it points at `.agents/AGENTS.md` (or, in a thin spoke, the hub) plus an awow tool mapping.

The single source of truth is `.agents/`. Edits to generated surfaces are overwritten on the next `gather.py` run.

## Extension notes (planned — hub-and-spoke WI-5)

- `.pi/extensions/awow.ts` registers `skillPaths` via `resources_discover` and injects an `<EXTREMELY_IMPORTANT>` bootstrap at `session_start`/`session_compact`, cleared on `agent_end` with a dedup guard.
- The bootstrap carries an awow **tool mapping**: Pi's lowercase `read`/`write`/`edit`/`bash`; no `Skill` tool → read `SKILL.md`; no slash commands → invoke flows by name; subagents only if a `pi-subagents` tool is present.
- `package.json` gains a `"pi"` field so the extension installs with `pi install`.
- The exact extension-API surface (`resources_discover`, `context`, lifecycle events) is pinned against the installed Pi version before build (proposal open item 3).

## Status

Planned under hub-and-spoke WI-5: the extension, the commands-as-skills surface, and `/setup-awow` detection. Pi has **no** zero-install in-repo story — unlike Codex it does not read a repo-root instruction file, so Pi support is extension-only.

## Reference

- Design: [`pi-codex-harness-support.md`](../../../meta/proposals/pi-codex-harness-support.md), reconciled in [`hub-and-spoke-design.md`](../../../meta/proposals/hub-and-spoke-design.md) §7 and §10.
