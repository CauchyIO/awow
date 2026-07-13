# Codex — harness reference

The Codex coding agent. It reads `AGENTS.md` from the repo root by convention, so a vendored awow repo is legible to it with **no install step**.

## When `/setup-awow` infers Codex

A repo-root `AGENTS.md` together with a `.codex-plugin/` directory, or the user explicitly chooses Codex. (The wizard's detection wiring lands with the plugin manifest — see Status.)

## What it provides

- Reads a repo-root `AGENTS.md` natively as its instruction file — the cross-vendor standard
- A native `Skill` tool, so awow's commands reach Codex **as skills**: one uniform code path across harnesses. Codex's native custom prompts are intentionally unused (commands-as-skills is the maintainer decision).
- Hooks, declared in the plugin manifest
- A plugin manifest (`.codex-plugin/plugin.json`) installed globally, plus an agents-marketplace entry

## How `.agents/` reaches Codex

- `.agents/AGENTS.md` → repo-root `AGENTS.md` — a pointer stub emitted by `tools/gather.py`. This is what steers Codex today; no install required.
- `.agents/commands/*` and `.agents/skills/*` → a shared commands-as-skills surface rendered from the `dist/` payload (`gather.py --surface codex`). A user invokes an awow flow by asking for it by name; Codex loads the matching `SKILL.md`.

The single source of truth is `.agents/`. Edits to generated surfaces are overwritten on the next `gather.py` run.

## Manifest notes (planned — hub-and-spoke WI-5)

- `.codex-plugin/plugin.json` mirrors `.claude-plugin/plugin.json`'s metadata and version, pointing `"skills"` at the shared surface.
- The empty `"hooks": {}` field is **load-bearing**: a missing `hooks` field makes Codex fall back to `hooks/hooks.json` and re-register Claude Code's `SessionStart` hook. Keep it present and empty.
- `.agents/plugins/marketplace.json` publishes awow to the Codex agents marketplace; a sync/package script (PR-only, branch-protection-safe) does the publish.

## Status

Shipping now: the repo-root `AGENTS.md` pointer — zero-install steering for the vendored template channel. Planned under hub-and-spoke WI-5: the plugin manifest, the commands-as-skills surface, marketplace sync, and `/setup-awow` detection.

## Reference

- Design: [`pi-codex-harness-support.md`](../../../meta/proposals/pi-codex-harness-support.md), reconciled in [`hub-and-spoke-design.md`](../../../meta/proposals/hub-and-spoke-design.md) §7 and §10.
