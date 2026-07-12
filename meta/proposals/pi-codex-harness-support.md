# Proposal — Support the Pi and Codex harnesses

**Status:** Reconciled into [hub-and-spoke-design.md](hub-and-spoke-design.md) §7 and §10 (2026-07-12); implementation tracked as hub-and-spoke **WI-5**. The repo-root `AGENTS.md` keystone (§1 below) lands first, as it is independently valuable and marketplace-independent.
**Inputs:** Maintainer request (Casper, 2026-07-12) to make awow drivable from the Pi and Codex coding agents, using `obra/superpowers` (checked out at `../superpowers`, v6.1.1) as the reference for how a skills framework is packaged for multiple harnesses. Verified against superpowers' committed `.codex-plugin/`, `.pi/extensions/`, `docs/porting-to-a-new-harness.md`, and its `sync-to-codex-plugin.sh` / `package-codex-plugin.sh`.
**Scope:** decide how awow reaches two new harnesses — Pi and Codex — under both of awow's distribution channels (the `.agents/` → surface gather fan-out for vendored-in adopters, and a per-harness plugin/extension for global install), surfacing awow's commands **as skills** on both. This session produces the design only; implementation is phased and deferred.

Authorised exception: `.agents/AGENTS.md`'s "Do not propose" list forbids *switching harnesses* without instruction. This proposal **adds** harnesses at explicit maintainer request, so the guard does not apply.

---

## Two distribution models, and why superpowers doesn't map 1:1

superpowers and awow solve harness support differently, and the difference sets the whole design:

- **superpowers** ships one shared `skills/` directory and gives each harness a thin root-level manifest that points at it — `.codex-plugin/plugin.json` with `"skills": "./skills/"`, `.pi/extensions/superpowers.ts` registering `skillPaths` and injecting a bootstrap. It is installed *globally* into each harness and published to marketplaces via `sync-to-codex-plugin.sh` (PR into a Codex-plugins fork) and `package-codex-plugin.sh` (rootless archive for the Codex portal). It is skills-only — no slash commands.
- **awow** is vendored *into an adopter's repo*. `.agents/` is the single source of truth; `tools/gather.py` fans it out as pointer stubs into each harness's native surface (`.claude/`, `.github/`), carrying only discovery metadata so nothing can drift. It is command-centric — 27 slash commands plus 10 skills.

Two consequences fall out. First, awow's commands must reach the new harnesses **as skills** (maintainer decision): Pi has no slash-command mechanism and no `Skill` tool at all, and we keep one uniform code path rather than special-casing Codex's native prompts. Second, "both distribution models" (maintainer decision) means each harness needs *both* a gather-emitted in-repo surface *and* a plugin/extension manifest — exactly the shape awow already has for Claude Code (`gather.py` + `.claude-plugin/`).

## How each harness actually integrates (verified against superpowers v6.1.1)

| | Codex | Pi |
|---|---|---|
| Instruction file | reads `AGENTS.md` from repo root by convention | injected by the extension (superpowers wraps `SKILL.md` in `<EXTREMELY_IMPORTANT>`) |
| Skill discovery | native, via manifest `"skills": "./…/"` | native, via `skillPaths` registered by an in-process extension |
| `Skill` tool | yes (native) | **no** — model reads `SKILL.md` with `read` |
| Slash commands | custom prompts (unused here — commands-as-skills) | **none** |
| Hooks | `"hooks": {}` in the manifest is **load-bearing** — a missing `hooks` field makes Codex fall back to `hooks/hooks.json` and re-register Claude's SessionStart hook (superpowers' v6.1.1 bug fix) | lifecycle callbacks in the `.ts` (`session_start`, `session_compact`, `agent_end`, `context`) |
| Distribution | `.codex-plugin/plugin.json` + `.agents/plugins/marketplace.json`; sync/package scripts | `package.json` `"pi"` field; `pi install git:…` |

## Design

Guiding invariant, unchanged: `.agents/` stays the single source of truth; everything new is either a *generated surface* or a *thin per-harness manifest*. No substantive content is duplicated.

### 1. Keystone — a generated root `AGENTS.md`
Codex reads `AGENTS.md` from the repo root, and it is the cross-vendor instruction standard (awow's own `copilot.md` already calls it that; Cursor and others honour it). Today `gather.py` emits only `.github/AGENTS.md`. Add a **root `AGENTS.md`** pointer stub → `.agents/AGENTS.md`, GENERATED-marked (so orphan handling is safe) and non-destructive via awowify's existing `<file>.awow` conflict mechanism when an adopter already ships one. This one file makes a vendored awow repo legible to Codex (and to Pi, if Pi honours root `AGENTS.md`) with zero install, and it is independently valuable for portability. **This is the highest-leverage single change.**

### 2. The shared skills surface (enables commands-as-skills + both plugin manifests)
Both plugin manifests need one directory to point at. `gather.py` gains an emitter that renders **every `.agents/skills/*` and every `.agents/commands/*` as a `SKILL.md`** into a single generated, GENERATED-marked, orphan-safe surface. A Pi/Codex user then invokes an awow flow by asking for it by name (e.g. "run daily-routine"), and the harness loads the corresponding `SKILL.md`. Command frontmatter collapses to `name` + `description` exactly as today's stubs do; the body points at `.agents/commands/<name>.md`.

Where this surface lives is **Decision D1** below — it overlaps directly with hub-and-spoke's WI-1 `gather.py --surface plugin` emitter, so the two should share one payload rather than build parallel ones.

### 3. Per-harness manifests (Phase 2)
- **Codex** — `.codex-plugin/plugin.json`: `{name, version, description, "skills": "<surface>", "hooks": {}, "interface": {…}}`, metadata and version mirroring `.claude-plugin/plugin.json`. The empty `"hooks": {}` is mandatory (see table). `.agents/plugins/marketplace.json` for the Codex agents marketplace.
- **Pi** — `.pi/extensions/awow.ts`: registers `skillPaths: [<surface>]` via `resources_discover`, and injects an `<EXTREMELY_IMPORTANT>` bootstrap at `session_start`/`session_compact` (cleared on `agent_end`, with a dedup guard) pointing at `.agents/AGENTS.md` plus an **awow tool mapping** — Pi's lowercase `read`/`write`/`edit`/`bash`; no `Skill` tool → read `SKILL.md`; no slash commands → invoke awow flows by name; subagents only if a `pi-subagents` tool is present. Adapted from superpowers' `superpowers.ts`, but the bootstrap body is awow's conventions, not superpowers'. `package.json` gains a `"pi"` field for `pi install`.
- **Marketplace sync/package scripts** adapted from superpowers' two scripts, respecting awow's PR-only / branch-protection posture.

### 4. Docs, detection, plumbing
- `context/tooling/harnesses/{pi,codex}.md` following the `claude-code.md` / `copilot.md` shape; update the harnesses `README.md` supported table (retitle "Supported in v0.1" → a version-agnostic heading, since four harnesses no longer means v0.1).
- `/setup-awow` Step 0 harness detection: extend beyond `.claude/`/`.github/` to recognise `.codex-plugin/` / root `AGENTS.md` (Codex) and `.pi/` (Pi).
- `gather.py`: new output-root constants, extend the hardcoded surface lists in `plan_top_level`/`plan_commands`/`plan_skills`/`plan_folder_readmes`, and add `--surface` choices (`codex`, `pi`) alongside `filter_surface`. CI `--check` covers the new surfaces, same drift guard as today.
- Version consistency: the new manifests carry the awow version; wire them into `tools/awow_lock.py` backfill so a stale manifest can't ship (the same discipline hub-and-spoke's WI-1 calls for).

## Relationship to adjacent proposals

- **`hub-and-spoke-adoption.md`** — its WI-1 builds `gather.py --surface plugin` emitting `dist/commands/` + `dist/skills/`; its D1 asks how awow reaches non-Claude harnesses. **This proposal is the multi-harness half of that same problem.** The shared skills surface here *is* hub-and-spoke's `dist/` payload with two more consumers. Recommendation: land the payload emitter once, jointly. If hub-and-spoke lands first, this proposal's Phase 1 shrinks to "add Pi/Codex as consumers of `dist/`". If this lands first, its emitter is written to hub-and-spoke's `dist/` shape from the start.
  **Settled (2026-07-12, maintainer session — see [hub-and-spoke-design.md](hub-and-spoke-design.md) §10):** D1 = (c), D2 = (c). hub-and-spoke's emitter owns the payload; Pi/Codex are `--surface codex` / `--surface pi` render targets of it. Two amendments follow: (1) the path sweep uses harness-neutral tokens substituted per surface at render time — prompt bodies never carry `${CLAUDE_PLUGIN_ROOT}` literally, since Codex/Pi don't resolve it; (2) this proposal's bootstrap must also handle the **spoke shape** (thin repos with a root `AGENTS.md` pointing at the hub, no `.agents/` present). Phase 1's in-repo value applies to the vendored template channel, which stays the public on-ramp for external adopters; Cauchy repos migrate to spokes.
- **`superpowers-integration-shape.md`** — that proposal imports superpowers' *skill content* into awow. This one borrows superpowers' *harness-packaging patterns*. Orthogonal; no overlap in files, but both touch `.agents/skills/` and `gather.py`, so sequence to avoid two concurrent gather reworks.
- **`plugin-distribution.md`** — its build-pipeline (`gather.py --surface plugin`, version discipline, `${CLAUDE_PLUGIN_ROOT}` resolution) is the same critical path; reuse it.

## Work items (phased)

### Phase 1 — gather fan-out (in-repo adopter value, no marketplace dependency)
- **WI-1** — root `AGENTS.md` emitter in `gather.py` (keystone, §1), non-destructive, `--check`-covered.
- **WI-2** — shared skills surface emitter: skills + commands-as-skills into the Decision-D1 location, GENERATED-marked, orphan-safe, aligned to hub-and-spoke's `dist/` shape.
- **WI-3** — `context/tooling/harnesses/{pi,codex}.md` + README table + `/setup-awow` Step 0 detection.

### Phase 2 — plugin/extension manifests + marketplace
- **WI-4** — `.codex-plugin/plugin.json` (+ `.agents/plugins/marketplace.json`), empty `"hooks": {}`, version-locked.
- **WI-5** — `.pi/extensions/awow.ts` + `package.json` `"pi"` field + awow bootstrap/tool-mapping.
- **WI-6** — sync/package scripts adapted from superpowers; PR-only, branch-protection-safe.
- **WI-7** — regression tests (extend `tests/setup-awow/` + `/test-setup-awow`) for both surfaces and both manifests.

## Decisions the team must make explicitly

| # | Decision | Options | Lean |
|---|---|---|---|
| D1 | **Shared-surface location** — where the generated skills+commands surface lives | (a) namespaced `.agents/dist/skills/` (never collides with an adopter's own `skills/`); (b) top-level `skills/` (superpowers-identical, familiar to porters); (c) whatever hub-and-spoke's `dist/` settles on | **Settled 2026-07-12: (c)** — hub-and-spoke-design.md §10 |
| D2 | **Sequencing vs hub-and-spoke** | (a) land jointly (one `dist/` emitter); (b) this first, hub-and-spoke consumes it; (c) hub-and-spoke first, this adds consumers | **Settled 2026-07-12: (c)** — hub-and-spoke's emitter owns the payload; this adds consumers |
| D3 | **Codex commands: skills only, or also native prompts later** | (a) skills-only forever (uniform); (b) skills now, add native `.codex` prompts later for nicer `/name` UX | (a) — maintainer chose commands-as-skills; revisit only if Codex UX demands it |
| D4 | **Pi bootstrap breadth** | (a) inject `.agents/AGENTS.md` pointer + tool mapping only (thin); (b) also inline awow's board-first reflex | (a) — keep parity with how Claude/Copilot get conventions; avoid a Pi-only behaviour fork |

## Open items to verify before Phase 1 (external-tool unknowns — not guessed)

1. **Codex project-skill discovery** — confirm, against the installed Codex version, whether Codex discovers repo-local skills without an installed plugin, or whether root `AGENTS.md` (pointing at `.agents/`) is the only zero-install in-repo mechanism. Determines whether WI-2's surface has an in-repo Codex consumer or is Phase-2-only for Codex.
2. **Pi + root `AGENTS.md`** — does Pi honour a root instruction file without the extension? If not, Pi's in-repo story is extension-only (Phase 2), and Phase 1 for Pi is just "ensure the surface exists".
3. **Pi extension-API compatibility** — pin the `@earendil-works/pi-coding-agent` API surface (`resources_discover`, `context`, lifecycle events) against the version adopters run.
4. **Codex root-`AGENTS.md` merge** — how Codex merges repo-root `AGENTS.md` with an adopter's own / `~/.codex/AGENTS.md`, to confirm the non-destructive stub coexists cleanly.
5. **External-link rule** — `copilot.md` carries `docs.github.com` links; the new `codex.md`/`pi.md` will want equivalents. The global "no external links without approval" rule means those doc URLs need explicit sign-off (or go to `REFERENCES.md` only). Flag at WI-3.

## Suggested sequencing

1. Review and accept this proposal; settle D1–D2 jointly with hub-and-spoke's owner.
2. Resolve open items 1–2 with a quick spike against installed Codex + Pi (what does each actually discover in a vendored awow repo?).
3. File board issues per work item; Phase 1 (WI-1..3) is path-independent and can start once the `dist/` shape is agreed.
