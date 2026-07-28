# Design — hub-and-spoke distribution: plugin machinery, hub context, thin spokes

**Status:** Accepted design — **MVP validated 2026-07-12, 5/5 assertions green** (see §8.1).
**Inputs:** [hub-and-spoke-adoption.md](hub-and-spoke-adoption.md) (direction + audit findings), [pi-codex-harness-support.md](pi-codex-harness-support.md) (harness packaging, reconciled in §10), maintainer design session with Casper (2026-07-12) — all decisions below were made explicitly in that session.
**Scope:** the concrete, buildable design for distributing awow's machinery as a versioned plugin while shared context lives in one hub repo and each project repo becomes a thin spoke. Covers spoke/hub file shapes, path resolution, the write path, harness delivery (Claude Code, Codex, Pi), an MVP validation spike, and the work-item breakdown. Supersedes nothing yet; on acceptance it is the implementation companion to hub-and-spoke-adoption.md, and `plugin-distribution.md` is marked Superseded.

---

## 1. Decisions made (2026-07-12 session)

| # | Decision | Outcome |
|---|---|---|
| S1 | Hub repo | **`CauchyIO/linear` stays the hub** — no dedicated hub repo extracted. Its existing `context/` tree is already the right shape; it is simultaneously the hub and its own project's spoke. |
| S2 | Connector style | **Path A (committed connector)** for all Cauchy spokes; Path B (gitignored) reserved for public repos, decided per project. |
| S3 | GitHub Copilot | **Dropped from hub-and-spoke scope.** No Copilot delivery to spokes. Copilot remains supported only in the vendored template channel as today. (Resolves the parent proposal's D1: none of options a–c; out of scope.) |
| S4 | Distribution channels | **Both channels coexist deliberately**: hub-and-spoke (plugin + hub) is the team-scale model; the vendored template channel ("Use this template" + `/awowify`) stays as the public on-ramp for external adopters. Both ship from the same payload emitter. |
| S5 | Harness set | **Claude Code, Codex, Pi.** Codex/Pi per pi-codex-harness-support.md, reconciled in §10. |
| S6 | Build order | **Design first, then board items per work item** (§9). MVP spike (§8) gates the big build. |
| S7 | Hub write path | **Pull-before-write, auto-commit + push to hub main for append-only data paths** (kb-inbox, retros); PR flow for hub governance files. See §6 — this is the least-proven joint and the MVP's primary target. |

Parent-proposal decisions adopted as leaned: D2 drafts live in the spoke repo; D3 board reference data ships in the plugin; D4 solo/team tailoring via registry capability flags; D5 Path A default, B for public repos; D6 project-scope committed enablement, user-scope documented as power-user option.

## 2. Architecture — three layers, three homes

| Layer | Home | Reaches a machine via |
|---|---|---|
| **Machinery** — commands, skills, hooks, tools, board reference data, KB contracts | `CauchyIO/awow`, `.agents/` as dev source | Built payload (`dist/`), rendered per harness, installed once per developer, updated by plugin version bump |
| **Shared context** — company, team, KB, retros, conventions, board config | `CauchyIO/linear` — the hub | One local clone per developer; located by identity (§4), never by relative path |
| **Project context** — mission, board-scope, do-not-propose | Each spoke repo, committed | `git clone` of the spoke |

The payload is built, not the raw repo: `gather.py --surface plugin` emits `.agents/commands/*` → `dist/commands/`, `.agents/skills/*` → `dist/skills/<name>/SKILL.md`, plus `tools/` and `hooks/`. `.claude-plugin/marketplace.json` points at `dist/` so `meta/`, guides, and maintainer context stop shipping to installers. Every payload change bumps `plugin.json`; CI runs the emitter with `--check` (same drift pattern as the existing gather check). Codex and Pi surfaces are additional render targets of the same emitter (§7, §10).

## 3. The spoke shape

A connected spoke (e.g. `overnight`) commits this and nothing more:

```
overnight/
├── AGENTS.md                  # reflex + connector in one committed stub:
│                              #   "this repo follows awow; hub: CauchyIO/linear;
│                              #    project: overnight" — read natively by Codex,
│                              #    injected for Pi, referenced from .claude/CLAUDE.md
├── .claude/settings.json      # enables awow@<marketplace> at project scope
└── context/
    ├── mission.md             # what this project is, one page
    ├── board-scope.md         # which board team/project this repo maps to
    └── do-not-propose.md      # project-specific guardrails (optional)
```

Four or five small public-safe files. The connector data (hub identity by git remote, project name) lives in `AGENTS.md` frontmatter — one stub serves as both cross-harness reflex and connector; no machine paths, no `../linear`, ever. Teammates get a working spoke from `git clone` alone (plus the once-per-machine step in §4). Drafts and proposals live in the spoke repo (D2).

## 4. Path resolution — identity, not location

Committed files name the hub by **identity** (git remote URL); each machine maps identity → local path exactly once:

- `resolve_hub()` in `tools/awow_paths.py`: `$AWOW_HUB` env var → per-user settings entry (written once by `/connect-project`) → **fail loud** naming the one-line fix. Never a guessed relative path, never a silent fallback.
- After resolving, **verify the clone's `origin` matches the connector's named remote** — a wrong or stale mapping stops loudly rather than reading the wrong team's context.
- `resolve_repo()`: `$CLAUDE_PROJECT_DIR` → `git rev-parse` → cwd. Replaces the five `__file__`-derived roots (audit B6/B8).

Prompt bodies never contain literal paths to either root. Source files in `.agents/` use two **neutral tokens** — machinery root and context root, the latter split into `{HUB}` (shared context) and `{PROJECT}` (repo-local project context) — and each surface emitter substitutes the harness-correct form at render time: `${CLAUDE_PLUGIN_ROOT}` for the Claude plugin surface, repo-relative for vendored surfaces, the extension root for Pi. The ~139 hardcoded `context/`/`tools/`/`.agents/` references get swept to these tokens once (following the shape `context/tooling/knowledge-base.md` already established), and a CI grep-lint blocks bare repo-relative paths in shipped prompts from ever landing again.

Worked example — `/awow:my-work` inside `overnight`:

1. The prompt (plugin cache) references `{HUB}/context/tooling/board.md` and `{PROJECT}/context/board-scope.md`.
2. `AGENTS.md` names hub `CauchyIO/linear`, project `overnight`.
3. `resolve_hub()` maps identity → `~/…/linear` (wherever this machine keeps it), verifies origin.
4. Board config read from the hub, scope from the spoke; the command proceeds exactly as today.

## 5. The hub shape and per-file classification

The hub is linear's `context/` tree **as it exists today** — no restructuring — plus one new file, `registry.yml`: `(git remote, subpath?) → project entry` (context dir, path A|B, solo/team capability flags, board, tracing). Many-to-one, so multi-repo products share one project context and monorepos scope by subpath. It replaces per-repo `setup-progress.md` for `/awow-status` and gives `/connect-project` deterministic teammate re-runs.

Linear's `context/` currently mixes team-owned **data** with awow-shipped **contracts**. The sweep classifies every file once:

| Stays in hub (team-owned, tunable) | Moves to plugin payload (awow-shipped machinery) |
|---|---|
| `company/**` (raci, stakeholders, neighbouring-teams) | `knowledge-base/mining.md`, `synthesis.md` (contracts) |
| `team/**` (members, mission, vision, conventions, style) | `tooling/harnesses/**` (harness docs) |
| `knowledge-base/**` content (architecture, decisions, patterns, runbooks, derived) | `tooling/boards/**` reference data (generic wizard input, D3) |
| `kb-inbox/`, `retros/`, `quarterly/`, `capture-queue/` | |
| `tooling/board.md`, `tooling/knowledge-base.md` (team config) | |
| `knowledge-base/mining-policy.md` (team-tunable policy) | |

Rule of thumb: if a team would edit it, it's hub; if only awow maintainers version it, it's payload. Implementation lands the full table file-by-file.

## 6. The write path (least-proven joint)

Reads are the easy half. Several commands **write** shared context: mining/`/daily-routine` capture into `kb-inbox/`, retro processing lands in `retros/`, digests update derived KB files. Today those are commits in the repo you're working in; under hub-and-spoke they are writes into a *different repo's* working tree (the local hub clone), which must then reach the team.

Design (S7): for **append-only data paths** (`kb-inbox/`, `retros/`) commands pull the hub first, write, then auto-commit and push to hub main — collision risk is near zero (per-user, timestamped files) and the KB already has its own human approval gate at synthesis time, so pushing captures is not pushing conclusions. **Governance files** (conventions, style, registry, mining-policy) keep PR flow. A failed push (network, protection, conflict) is a loud stop with the pushable state left intact locally — never silently dropped.

Open until the MVP proves it (§8): whether hub main allows direct pushes for data paths (linear's branch protection is the hub team's call), and how concurrent same-day captures from two machines merge in practice.

## 7. Harness delivery

| | Delivery | Reflex (session bootstrap) | Commands |
|---|---|---|---|
| **Claude Code** | plugin from marketplace, versioned | plugin hook, tiered by availability state (below) | native `/awow:*` |
| **Codex** | `.codex-plugin/plugin.json` (with the load-bearing empty `"hooks": {}`) + marketplace sync | reads committed root `AGENTS.md` natively | commands-as-skills, invoked by name |
| **Pi** | `.pi/extensions/awow.ts` via `pi install` | extension injects bootstrap + tool mapping at session start (Pi has no `Skill` tool, no slash commands) | commands-as-skills, invoked by name |

One shared detection helper drives every reflex, implementing the availability states: connector present + hub resolvable → full reflex with reachability-checked pointers; connector present, hub missing → "clone the hub / set `AWOW_HUB`", stop; registry knows the remote but no connector → nudge `/connect-project`; unknown repo → silent. The `.agents/AGENTS.md` sentinel and the worktree decline-flag are retired; opt-out is native `"awow@…": false` in `.claude/settings.local.json`.

## 8. MVP validation spike — prove it before building it

None of the risky joints depend on the 139-reference sweep, the registry, or `/connect-project`, so the load-bearing chain is provable in a ~1–2 day spike with two hand-swept commands:

1. **Micro-payload:** copy `my-work` (read-heavy) and a slimmed `kb-mine` (write path) into a scratch `dist/commands/`, hand-replace paths with the neutral tokens, add `plugin.json`. Install from local disk (`claude plugin marketplace add <path>`) — no GitHub release needed.
2. **Fixture spoke:** scratch repo (or an `overnight` branch) carrying only the §3 files. Real linear clone as hub.
3. **Minimal `resolve_hub()`** — env → settings → fail-loud chain, ~40 lines.
4. **Headless assertions** via `claude -p` through a cheap-model gateway (run repeatedly):
   - `/awow:my-work` reads board config from the hub and scope from the spoke — the answer names the spoke's board items, not the hub repo's.
   - kb-mine writes a capture into the hub clone's `kb-inbox/` and the commit + push lands (write path, §6).
   - Unset `$AWOW_HUB` → loud actionable stop, no improvised conventions (fail-loud).
   - Prompt provably loaded from plugin cache; name collisions with repo-local commands resolve sanely (the two spikes carried from `plugin-distribution.md`).
5. **Phase 2, same fixture:** point Codex (`codex exec`, custom `base_url`) and Pi at the identical spoke — does root `AGENTS.md` steer them; do commands-as-skills load (resolves pi-codex open items 1–2).

**Exit criteria:** all four Claude Code assertions green → the architecture is proven and the big build is mechanical execution. If the write path or plugin-cache resolution fails, we learned it for two days' work instead of after a 139-file sweep. The MVP fixture is not throwaway: it grows into the WI-8 regression suite.

### 8.1 MVP results (run 2026-07-12, Claude Code 2.1.207, model haiku, headless `claude -p`)

Executed same-day as the design session; the spike took ~1 hour, not the budgeted 1–2 days. One deliberate deviation: a **synthetic hub** (minimal `context/` + local bare origin) stood in for the real linear clone so the write-path test pushed to a fixture remote, not the team's hub. The resolution chain under test is identical.

| # | Assertion | Result |
|---|---|---|
| T1 | Read path: `/awow-mvp:my-work` in a thin spoke reports `board=` from the hub and `team=/project=` from the spoke | **PASS** — exact expected output, first try |
| T2 | Write path: `/awow-mvp:kb-mine` writes the capture into the hub clone, commits, pushes; commit verified in the bare origin's log | **PASS** |
| T3 | Fail-loud: `AWOW_HUB` unset, no settings entry → actionable stop, no improvisation | **PASS** — and the model did *not* probe sibling dirs even though `../hub` existed |
| T4 | Provenance + collision: commands served from `~/.claude/plugins/cache/awow-mvp-mkt/…`; repo-local `/my-work` and plugin `/awow-mvp:my-work` coexist without interference (namespacing) | **PASS** |
| T5 | Identity check: `AWOW_HUB` pointing at a clone whose `origin` ≠ the connector's `awow-hub` → loud mismatch stop naming both | **PASS** |

Notes for the build: local-path marketplaces work (`claude plugin marketplace add <dir>` + `install`), so WI-1 can be dogfooded without a GitHub release; the runs used the developer's normal auth — wiring the shared model gateway is WI-8's job; the fixture (marketplace + hub-origin + spoke) was session-scratch — WI-8's first task is a `setup-fixture.sh` that regenerates it with machine-local absolute paths.

## 9. Work items

| WI | Deliverable | Depends on |
|---|---|---|
| WI-0 | Spikes: MVP (§8), Codex/Pi in-repo discovery, Pi extension-API pin | — |
| WI-1 | Payload emitter: `gather.py --surface plugin`, `dist/` shape shared by all harness targets, marketplace repoint, version discipline + `--check` in CI | WI-0 |
| WI-2 | Neutral-token path sweep (~139 refs) + render-time substitution per surface + grep-lint in CI | WI-1 |
| WI-3 | Shared detection helper + tiered reflex; retire `.agents/AGENTS.md` sentinel + decline flag | WI-2 |
| WI-4 | `/hub-setup`, `/connect-project` (+ `--migrate` deleting vendored files by manifest), `registry.yml`, `awow_paths.py`; **acceptance test: migrate `overnight` to a thin spoke** | WI-2 |
| WI-5 | Codex + Pi manifests, commands-as-skills surface, marketplace sync scripts (pi-codex WI-2/4/5/6, reconciled §10) | WI-1 |
| WI-6 | Hub write-path plumbing per §6 (pull-before-write, push, failure handling) | WI-0 |
| WI-7 | Docs: harness pages, README, mark `plugin-distribution.md` Superseded, update hub-and-spoke-adoption.md status | WI-1..6 |
| WI-8 | Harness test suite: headless matrix (Claude Code / Codex / Pi) against the shared model gateway, grown from the MVP fixture; behavioural coverage for the three harnesses, §8 assertions as the regression floor | WI-0, WI-5 |

`/awowify` remains the template-channel on-ramp (S4); `/update-awow` gains "update plugin + `git pull` the hub" for hub-and-spoke installs; `/awow-add` becomes a registry capability-flag toggle for connected repos.

## 10. Reconciliation with pi-codex-harness-support.md

That proposal's D1 (shared-surface location) resolves to **(c)** — the surface is this design's `dist/` payload; its D2 (sequencing) resolves to **(c)** — this design owns the emitter, Pi/Codex are added as `--surface codex` / `--surface pi` render targets. One payload; three harness surfaces (Claude Code, Codex, Pi) plus the vendored template channel all render from it. Its Phase 1 in-repo value applies to the **vendored template channel** (which S4 keeps for external adopters), not to spokes; its bootstrap must additionally handle the spoke shape (§3), where `AGENTS.md` points at the hub instead of `.agents/`. Its verified integration details (empty `"hooks": {}`, Pi bootstrap mechanics, commands-as-skills) are adopted as-is into WI-5.

## 11. Open questions

- Hub branch protection vs direct data-path pushes (§6) — hub team decides; MVP informs.
- Hub clone freshness: should the reflex warn when the local hub clone is N days behind origin? (Lean: yes, warn-only, at session start.)
- CI flows with no hub/plugin present degrade to no-awow — acceptable? (Carried from parent; likely yes, state it in docs.)
- Path A public-safety review over time — candidate owner: a connect-installed pre-push scan (carried from parent).
- Worktree gap for Path B connectors (carried from parent; Path B is not in Cauchy's initial scope).

## 12. Suggested sequencing

1. Review and accept this design; file board issues per WI (S6).
2. Run the MVP spike (WI-0 / §8) before any sweep work lands.
3. WI-1..2 on green MVP; WI-3..6 in parallel after; WI-7..8 close it out.
