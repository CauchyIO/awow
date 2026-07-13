# Codex — harness reference

The Codex coding agent. It reads `AGENTS.md` from the repo root by convention, so a vendored awow repo is legible to it with **no install step**.

## When `/setup-awow` infers Codex

A repo-root `AGENTS.md` together with a `.codex-plugin/` directory, or the user explicitly chooses Codex. `/setup-awow` Step 1a detects both signals.

## What it provides

- Reads a repo-root `AGENTS.md` natively as its instruction file — the cross-vendor standard
- A native `Skill` tool, so awow's commands reach Codex **as skills**: one uniform code path across harnesses. Codex's native custom prompts are intentionally unused (commands-as-skills is the maintainer decision).
- Hooks, declared in the plugin manifest
- A plugin manifest (`.codex-plugin/plugin.json`) installed globally, plus an agents-marketplace entry

## How `.agents/` reaches Codex

- `.agents/AGENTS.md` → repo-root `AGENTS.md` — a pointer stub emitted by `tools/gather.py`. This is what steers Codex today; no install required.
- `.agents/commands/*` and `.agents/skills/*` → a shared commands-as-skills surface rendered from the `dist/` payload (`gather.py --surface plugin`, into `dist/agent-skills/`). A user invokes an awow flow by asking for it by name; Codex loads the matching `SKILL.md`.

The single source of truth is `.agents/`. Edits to generated surfaces are overwritten on the next `gather.py` run.

## Manifest notes

Both files are emitted into `dist/` by `gather.py` (the payload's own `dist/` published as a git repo *is* the Codex marketplace, so the plugin sits at its root with `source: "./"`):

- `dist/.codex-plugin/plugin.json` mirrors `.claude-plugin/plugin.json`'s metadata and **version** (derived at gather time from the one canonical manifest, so it cannot ship stale — `gather.py --check` fails on drift), pointing `"skills"` at the shared `agent-skills/` surface.
- The empty `"hooks": {}` field is **load-bearing**: a missing `hooks` field makes Codex fall back to `hooks/hooks.json` and re-register Claude Code's `SessionStart` hook. Keep it present and empty.
- `dist/.agents/plugins/marketplace.json` publishes awow to the Codex agents marketplace. `tools/sync-dist.sh` mirrors the built `dist/` to the `CauchyIO/awow-dist` marketplace repo via a branch + PR (PR-only, branch-protection-safe).

Install path: `codex plugin marketplace add <awow-dist repo>` → `codex plugin add awow@awow`.

## Status

Shipping under hub-and-spoke WI-5: the repo-root `AGENTS.md` pointer (zero-install steering), the `.codex-plugin/plugin.json` manifest, the commands-as-skills surface, `/setup-awow` Step 1a detection, and marketplace publish via `tools/sync-dist.sh` → `CauchyIO/awow-dist`.

## Reference

- Design: [`pi-codex-harness-support.md`](../../../meta/proposals/pi-codex-harness-support.md), reconciled in [`hub-and-spoke-design.md`](../../../meta/proposals/hub-and-spoke-design.md) §7 and §10.
