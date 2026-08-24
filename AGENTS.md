# Agent instructions

This repo is awow's own source. The canonical rule set for every agent working here is [`.agents/AGENTS.md`](.agents/AGENTS.md) — **read it before doing anything else.** Commands live under `.agents/commands/`, skills under `.agents/skills/`, conventions and context under `context/`.

`AGENTS.md` is the cross-vendor instruction-file standard: a harness that reads it natively from the repo root — Codex, Pi, opencode — is steered to the source above with no install step.

Nothing under `.agents/` is mirrored into harness folders. Commands and skills reach a session through the awow plugin, whose marketplace is this repo: `.claude-plugin/marketplace.json` serves `dist/`, built by `tools/gather.py`. The maintainer loop is in [`guides/guide-setup-and-two-harnesses.md`](guides/guide-setup-and-two-harnesses.md).
