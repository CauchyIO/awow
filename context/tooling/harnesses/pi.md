# Pi — harness reference

The Pi coding agent. It reads the repo-root `AGENTS.md` and discovers `.agents/skills/` natively, so awow's conventions and skills reach it **with no extension**. A package manifest (`package.json` `pi.skills`) points Pi at the shared commands-as-skills surface, and that package is the whole integration.

## When `/setup-awow` infers Pi

A `.pi/` directory (Pi's per-repo config), or the user explicitly chooses Pi. `/setup-awow` Step 1a detects the `.pi/` signal.

## What it provides

- Reads a repo-root `AGENTS.md` natively as its instruction file — the cross-vendor standard. awow steers Pi **zero-install**, the same as Codex.
- Native skill discovery: Pi finds `.agents/skills/<name>/SKILL.md` on its own, and a package's `pi.skills` paths register additional skill roots — awow uses this for the commands-as-skills surface.
- Skills are invoked with `/skill:<name>`, which injects the matching `SKILL.md`. There is **no `Skill` tool** and no other slash-command mechanism — the flow's own body drives it.

## How `.agents/` reaches Pi

- `.agents/commands/*` and `.agents/skills/*` → the shared commands-as-skills surface rendered from the `dist/` payload (`gather.py --surface plugin`, into `dist/agent-skills/`), registered through the package's `pi.skills` paths.
- Instructions reach Pi through the repo-root `AGENTS.md` it reads natively — no committed extension, no injected bootstrap.

The single source of truth is `.agents/`. Edits to generated surfaces are overwritten on the next `gather.py` run.

## Package notes

- `dist/package.json` carries a `"pi"` key whose `skills` array points at `./agent-skills` — the commands-as-skills surface. `pi install -l dist` (local) or an install from the published `CauchyIO/awow-dist` repo registers those skill paths.
- The `version` is derived at gather time from the canonical `.claude-plugin/plugin.json`, so the package cannot ship a stale version — `gather.py --check` fails on drift.
- No `.pi/extensions/*.ts`: hub-and-spoke WI-5 S3 dogfooding confirmed Pi's native `AGENTS.md` + `.agents/skills` discovery makes an in-process extension unnecessary. The earlier proposal assumed an extension; grounding against Pi 0.80.6 removed it.

## Status

Shipping under hub-and-spoke WI-5: the `package.json` `pi` manifest, the commands-as-skills surface, and `/setup-awow` Step 1a detection. Pi needs **no** extension — it reads the repo-root `AGENTS.md` natively, so awow's instructions steer it **zero-install**; only the commands-as-skills surface needs the package (`pi install`). This corrects the earlier "Pi has no zero-install" framing: steering is zero-install, the skills surface is package-installed.

## Reference

- Design: [`pi-codex-harness-support.md`](../../../meta/proposals/pi-codex-harness-support.md), reconciled in [`hub-and-spoke-design.md`](../../../meta/proposals/hub-and-spoke-design.md) §7 and §10.
