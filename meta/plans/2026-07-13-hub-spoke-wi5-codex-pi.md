# hub-spoke WI-5 — Codex + Pi packaging (implementation staging)

> Executing an accepted design (hub-and-spoke-design.md §7/§10 + pi-codex-harness-support.md §3), refined by grounding against codex 0.144 + pi 0.80.6 (their own docs) and the superpowers v6.1.1 reference. Branch: `feat/hub-spoke-wi5` off `feat/hub-spoke-design` (has WI-1 `dist/` + the pi-codex keystone).

## What grounding changed vs the original proposal

- **Codex 0.144**: marketplace plugin model (`codex plugin marketplace add <local|git>` → `codex plugin add awow@<mkt>`). Local marketplaces work → dogfoggable. Reads root `AGENTS.md` natively (keystone = the reflex; no session hook needed → the empty `"hooks": {}` is load-bearing, it suppresses codex auto-registering a SessionStart hook).
- **Pi 0.80.6**: natively discovers `.agents/skills/<name>/SKILL.md` and reads `AGENTS.md`/`CLAUDE.md`. Real skills + conventions already reach Pi. A pi package is just a `package.json` `pi` key (`{extensions, skills}`) or convention dirs; `pi install -l ./path` registers locally without copying.
- **The gap for both is awow's *commands*** (in `.agents/commands/`, discovered as skills by neither) → the core deliverable is a **commands-as-skills surface**.

## The surface (both harnesses point here)

`gather.py` renders, under the `dist/` payload, `dist/agent-skills/<name>/SKILL.md` — one dir per **command and skill**, full content (not a pointer; the plugin ships where `.agents/` is absent), token-substituted, GENERATED-marked, orphan-safe:
- Each command → `SKILL.md` with `name` + `description` frontmatter + the command body (as a skill: action-vocabulary, invoked by name).
- Each skill → its `SKILL.md` (+ bundled `scripts/`/`references/` copied alongside).

Duplication of the real skills between `dist/skills/` (Claude) and `dist/agent-skills/` (codex/pi) is accepted — `dist/` is wholly generated. Claude keeps `dist/commands/` (slash commands) + `dist/skills/` (skills); codex/pi use the unified `agent-skills/`.

## Stages (each dogfood-verified against the real CLI)

**Stage 1 — Foundation: the commands-as-skills surface emitter.**
`plan_agent_skills()` in `gather.py` → `dist/agent-skills/`; wire into `plan_plugin`/the plugin surface; `--check`-covered; orphan-safe. Verify: gather + `--check` green; spot-check a rendered `SKILL.md`.

**Stage 2 — Codex.**
`dist/.codex-plugin/plugin.json` (gather-emitted: metadata+version mirrored from `.claude-plugin/plugin.json`, `"skills": "./agent-skills/"`, `"hooks": {}`, an `interface` block) + `.agents/plugins/marketplace.json` (codex marketplace manifest, schema from superpowers). **Dogfood:** `codex plugin marketplace add <dist>` + `codex plugin add awow@…` + confirm a skill is discoverable.

**Stage 3 — Pi.**
A pi package manifest pointing `pi.skills` at `dist/agent-skills` (+ native `.agents/skills` already covered). Assess a `.pi/extensions/awow.ts` reflex/tool-map — **start package-only** (AGENTS.md gives the reflex natively); add a thin extension only if dogfooding shows the reflex/commands-surface doesn't land. **Dogfood:** `pi install -l <pkg>` (or `.pi/settings.json`) + a headless `pi -p` that discovers an awow command-as-skill.

**Stage 4 — Plumbing.**
Marketplace sync + portal-package scripts (adapted from superpowers' two, PR-only/branch-protection-safe); version discipline (a `.version-bump`-style lockstep across `.claude-plugin`, `.codex-plugin`, marketplace, `package.json` — or extend `tools/awow_lock.py`); `/setup-awow` Step 0 detection for `.codex-plugin`/`.pi`; codex.md/pi.md "Status" + pi.md zero-install correction; harness README table.

**Stage 5 — Tests.**
Un-SKIP the codex/pi manifest checks in `tests/harness/*/wiring.sh` (they now assert the real manifests) and add surface/manifest coverage to the gather `--check` + a light dogfood test. (These live on the harness-wiring-tests branch; land there or here per merge order.)

## Open calls (resolved inline, not guessed)

- **Pi extension yes/no** — decided in Stage 3 by dogfooding (lean: package-only first).
- **Version discipline mechanism** — `.version-bump.json`+script (superpowers' shape) vs extending `awow_lock.py`; pick in Stage 4 against what awow already has.
- **Surface duplication** — accept it (generated payload) unless it complicates the codex plugin root; revisit only if it does.

## Status (as built)

- **S1–S3** — done, dogfood-verified against codex 0.144 + pi 0.80.6 (isolated `CODEX_HOME` + project-local `.pi/`).
- **S4** — done:
  - **Version discipline** — resolved to *derive, don't duplicate*: `plan_codex`/`plan_pi` read `version` from the one canonical `.claude-plugin/plugin.json`, and `gather.py --check` (CI-enforced) fails on any drift. No `.version-bump.json` needed — nothing can ship stale.
  - **Pi extension** — resolved *no*: S3 confirmed Pi reads root `AGENTS.md` + `.agents/skills` natively, so the package (`package.json` `pi.skills`) is the whole integration.
  - **Marketplace publish** — `tools/sync-dist.sh` mirrors the built `dist/` → `CauchyIO/awow-dist` via a branch + PR (branch-protection-safe; dry-run by default; runs `gather --check` in preflight so a stale payload can't be published). awow's `dist/`-as-repo IS the codex marketplace, so superpowers' nested-monorepo + OpenAI-portal packager did **not** port — a single root-level mirror replaces both.
  - **`/setup-awow` Step 1a** detects Codex (`.codex-plugin/` + root `AGENTS.md`) and Pi (`.pi/`).
  - **Docs** — `codex.md`/`pi.md` Status flipped to shipping; `pi.md` extension→package correction + "zero-install" fix; harness `README.md` table.
- **S5** — the codex/pi wiring-test un-SKIP lives on the harness-wiring-tests branch (PR #27); it lands there / on rebase. Manifest + version-lockstep drift is already guarded here by `gather.py --check`.
