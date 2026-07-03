# Proposal — Adopt the hub-and-spoke distribution model (two-path feedback)

**Status:** Draft — awaiting review.
**Inputs:** Martijn's design proposal *"awow Multi-Project Setup — Two Paths"* (2026-06-11) plus its code-level audit *"Deep-dive: hub-and-spoke proposal vs the awow codebase"* (29 verified findings against `d297c38`, v0.2.0). Findings re-checked against `origin/main` (`56e07a1`) on 2026-07-03: only the KB-spine work landed since the audit, so every cited finding is still current.
**Scope:** decide how awow is distributed and connected across many projects — replace per-repo vendoring with a shared foundation (plugin machinery + private hub repo for team context) and a per-project fork: context committed in the repo (Path A) or held in the hub behind a gitignored connector (Path B).

---

## What the feedback says, in short

Today `/awowify` vendors ~150 files of machinery plus team context into every adopter repo. The proposal replaces that with:

- **Machinery** (commands, skills, tools, hooks) ships once, via the **awow plugin** — installed per developer, updated in one place.
- **Shared team context** (board.md, conventions, style, design system, glossary) lives in a private **hub repo**, cloned once per developer, located via `$AWOW_HUB` / a settings entry.
- **Per-project context** (mission, board-scope, do-not-propose) forks per project: **Path A** commits ~1–5 small public-safe files in the repo (`.claude/CLAUDE.md` connector with hub pointers — clone-and-go for teammates); **Path B** keeps it in the hub under `project_data/context_<project>/`, with only a gitignored connector in the repo (100 % awow-free published history, one connect step per teammate per machine).

The audit's verdict: the design is sound and its git mechanics verified workable, but the plugin that "ships the machinery" does not exist yet — today it ships only `/awowify` — and the real build effort is **plugin packaging + a ~139-reference path sweep + hook-detection rework**, not the setup-wizard split.

## Verified against this repo (2026-07-03, `origin/main`)

- `.claude-plugin/plugin.json` (0.2.0) declares only `"commands": "./commands/"`; that directory holds exactly one file, `awowify.md`. The 25+ real commands and 10 skills under `.agents/` are never scanned by the plugin loader. (A1)
- `.claude-plugin/marketplace.json` uses `"source": "./"` — every installer pulls the whole maintainer repo, including `meta/`, `context/team+company`, guides, and tests. (B2)
- `hooks/session-start` and `hooks/board-linkage-check.py` both key "adopted" on `.agents/AGENTS.md`, and the reflex injection is ungated. A connected spoke will never have that file. (A3) Note: the unmerged `feat/architecture-aware-development` branch renames the PreToolUse hook to `lifecycle-seam-check` and adds a second seam — the detection rework must land against whichever wins, and the sweep should be re-run after that branch merges.
- `tools/bootstrap-claude-md.py`, `gather.py`, `validate-context.py`, `reset-adopter-state.py`, `distribute.py` all derive REPO_ROOT from `__file__` — shipped in a plugin they would operate on the plugin install dir. (B6, B8)
- The KB spine that landed after the audit (PR #19) *helps* rather than hurts: `context/tooling/knowledge-base.md` already makes `kb_root`/`inbox` an indirection that commands resolve at runtime. That is exactly the CONTEXT_ROOT shape the sweep needs — the KB machinery is the template for the other ~139 references, but the committed `context/kb-inbox/` default must resolve through CONTEXT_ROOT too, or Path B's "awow-free" guarantee breaks the moment mining runs.

## Relationship to `plugin-distribution.md`

The existing draft proposes the plugin as a **second on-ramp** that *scaffolds* the vendored shape into the adopter's repo; hub-and-spoke proposes the plugin as the **sole machinery channel** with no vendoring at all. These are different end-states, but they share the entire critical path: a built plugin payload (its `build-plugin.py` ≈ this proposal's `gather.py --surface plugin`), version/drift discipline, and `${CLAUDE_PLUGIN_ROOT}` resolution. Two of its risks (skill-override resolution, mid-session scaffold visibility) apply unchanged here.

**Recommendation:** treat hub-and-spoke as the successor. When this proposal is accepted, mark `plugin-distribution.md` **Superseded** (by this file), carrying forward its build-pipeline section, dogfood loop, and the two open spikes. Its answer to the Copilot question ("Copilot stays template-based") becomes one input to Decision D1 below.

## The load-bearing problem: context availability

Maintainer review (Casper, 2026-07-03) confirmed the direction — hub-and-spoke, machinery as a plugin — and named the real challenge: **every command references context files, and whether those files are reachable at invocation time is what makes or breaks the model.** The plugin guarantees the *prompts* are everywhere; nothing yet guarantees the *context* is. The design must state, per availability state, exactly what a command does:

| State | What's reachable | Behaviour |
|---|---|---|
| Connected (A or B) | connector → CONTEXT_ROOT resolves; hub cloned | Full: commands read shared context from the hub, project context from repo (A) or `project_data/` (B). |
| Known but unconnected | hub registry recognises the remote; no local connector | Reflex still fires, but its content is "run `/connect-project`"; context-dependent commands stop there. |
| Hub missing / not set | plugin installed, no `$AWOW_HUB` and no settings entry | Fail loud at first context read: name the missing root and the one-line fix. Never silently improvise conventions. |
| Unknown repo | no connector, no registry hit | See D6 — silent vs a light generic reflex. |

Two rules follow: commands must resolve context through **one** indirection (CONTEXT_ROOT, WI-2) rather than each prompt guessing paths; and a missing context file is a **loud, actionable stop** — pointing at `/connect-project` or the hub clone step — never a silent degradation (consistent with the KB machinery's fail-loud posture).

### Reflex scope is the adopter's install decision (verified 2026-07-03)

Claude Code enables plugins at four persistent scopes (checked against the current plugin/hooks/settings docs), and **plugin hooks fire only where the plugin is enabled** — so how far the reflex reaches is not awow detection logic, it is the adopter's `enabledPlugins` choice:

| Scope | File | Reflex fires in | Fit |
|---|---|---|---|
| User | `~/.claude/settings.json` | every repo on the machine | maximal ubiquity; *requires* the tiered reflex content below to avoid dangling pointers in non-awow repos |
| Project, committed | `.claude/settings.json` | that repo, for every teammate (install prompt on folder trust) | natural for **Path A** — one more small committed awow file next to the connector |
| Project, local | `.claude/settings.local.json` (gitignored) | that repo, this machine only | natural for **Path B** — `/connect-project` writes it; history stays awow-free |
| Managed | enterprise managed settings | per policy | org-wide rollout |

Precedence is managed > local > project > user, and `"awow@…": false` disables without uninstalling — which gives Path A teammates and user-scope installers a clean per-machine opt-out, replacing the worktree decline-flag hack A3 criticised. What remains awow's job regardless of scope is the *content* tiering: at any scope the reflex must only assert what the availability table above says is reachable.

### Monorepo vs multi-repo cardinality

Adopters run both shapes, so repo↔project-context is **not 1:1** and the hub registry must model that from day one:

- **Monorepo:** one remote, several projects → registry entries are `(remote, subpath?) → context dir`; the connector (or a per-package connector) names which context is "mine". Claude Code's nested-CLAUDE.md loading fits Path A here naturally.
- **Multi-repo product:** several remotes, one project context → many registry rows pointing at the same `project_data/context_<p>/`; the connect step should offer "attach to existing project" alongside "new project".

## Incorporation plan — work items

The A/B fork does not block starting: WI‑1 through WI‑3 are path-independent and are where the effort actually lives.

### WI-1 — Plugin payload packaging (the critical path)
Extend `gather.py` with a `--surface plugin` emitter: `.agents/commands/*.md` → `dist/commands/` (excluding README.md and other non-commands), `.agents/skills/*` → `dist/skills/<name>/SKILL.md` (converting the 2 declarative skills, preserving `scripts/`), plus `tools/` and `hooks/`. Point `marketplace.json` at the built `dist/` payload so `meta/`, team context, and guides stop shipping to installers (B2). Add a session-start version self-check against the marketplace clone plus release discipline: every payload change bumps `plugin.json` (B1 — a stale 0.1.0 cache is live today). CI runs the emitter with `--check`, same drift pattern as the existing gather check.

### WI-2 — Two-root convention + path-reference sweep
Adopt one convention before touching any body: `${CLAUDE_PLUGIN_ROOT}` for machinery and scripts; **CONTEXT_ROOT** (connector's hub pointer, else repo root) for context and drafts. Sweep the ~139 repo-relative references across command/skill bodies (A2, B12), following the pattern `context/tooling/knowledge-base.md` already established. Add a grep-based lint (no bare `context/`, `tools/`, `.agents/` in plugin-shipped prompts) so regressions cannot land.

### WI-3 — Hook detection rework
One shared detection helper for both hooks and the reflex gate, implementing the availability-state table above: connector sentinel → *connected* (inject reflex with resolved context pointers); hub-registry hit → *known-but-unconnected* (nudge `/connect-project` only); unknown repo → per D6. What A3 flagged as the bug is not the ubiquity itself but that today's ungated reflex asserts "you are governed by awow" *with dangling context pointers* — the fix is tiering the reflex's content by what is actually reachable; how far it fires at all is the adopter's enablement-scope choice (see the scope table). Retire the worktree decline flag in favour of `"awow@<marketplace>": false` in the repo's `.claude/settings.local.json` — native, per-machine, survives clear/compact, and never touches published history.

### WI-4 — Setup split + hub plumbing
- `/hub-setup` and `/connect-project` **as plugin commands** (escapes the awowify chicken-and-egg, B3). Connect asks the ~3 questions + path + tracing opt-in; Path A writes a committed public-safe connector with `$AWOW_HUB` pointers, Path B writes hub `project_data/` + a gitignored connector carrying the literal absolute hub path + `.git/info/exclude` entries. Supports a no-questions teammate re-run and `--migrate` for the ~150-file vendored adopters, reusing `reset-adopter-state.py` manifest knowledge (B4).
- Re-spec `tools/bootstrap-claude-md.py` (currently an unimplemented skeleton aimed at `.agents/AGENTS.md`) as connect-project's connector writer (B8).
- **Hub registry** `project_data/registry.yml`: `(git remote, subpath?)` → context dir, path A|B, solo/team, board, tracing — many-to-one so multi-repo products share one context dir and monorepos scope by subpath (see cardinality section). The successor to per-repo `setup-progress.md` for `/awow-status`, validate-context, and deterministic teammate connects (B10). Connect offers "attach to existing project" alongside "new project".
- `tools/awow_paths.py`: `resolve_hub()` (`$AWOW_HUB` → settings key → fail loud) and `resolve_repo()` (`$CLAUDE_PROJECT_DIR` → `git rev-parse` → cwd), replacing the five `__file__`-derived roots (B6). Fail loud, never silent fallback.
- Connect installs the pre-push leak scan with hub-resolved patterns (warn loudly, never silent `exit 0`) and appends session-output ignores to `.git/info/exclude` (B7). Analytics invocations move to `${CLAUDE_PLUGIN_ROOT}/tools/...`; fix `awow_extract.py`'s `parents[4]` (B9). Retire `distribute.py`.

### WI-0 — Land the design docs
Convert the HTML proposal to markdown alongside this file (the HTML pulls a Google Fonts stylesheet — external links are not committed to this repo) and bring the findings report in as its appendix, with Martijn's machine-specific paths scrubbed before commit (public repo).

## Decisions the team must make explicitly

| # | Decision | Options | Lean |
|---|---|---|---|
| D1 | **GitHub Copilot** (A4) — a Claude Code plugin delivers nothing to Copilot, and awow is explicitly dual-harness today; maintainer expects reflex parity ("in GitHub Copilot I expect similar behaviour"), and Copilot has no hook mechanism — its reflex *is* its instruction files | (a) declare hub-and-spoke CC-only; (b) VS Code user-profile prompt/instruction delivery from hub-setup; (c) committed `.github/` stubs as a Path A option | (c) for Path A, (b) investigated for Path B — reflex parity rules out plain (a) |
| D2 | **Drafting home** (B11) — ~9 commands write to repo-root `proposals/` | ephemeral drafts → repo `proposals/` covered by connect's `.git/info/exclude`; durable artefacts → hub `project_data/context_<p>/proposals/` | as stated; bake the rule into the CONTEXT_ROOT convention |
| D3 | **Board reference data** (`boards/<tool>/reference/`) | plugin payload vs hub | plugin payload — it is generic wizard input |
| D4 | **Solo/board tailoring** (B5) — awowify's file-trimming and `/awow-add`'s copy-then-gather mechanic die with vendoring | capability flags in the hub registry; team commands check and decline gracefully; `/awow-add` becomes a flag toggle | as stated |
| D5 | **A/B default** | fix one path team-wide vs ask per project at connect | per project: Path A for private/internal repos, Path B for public ones |
| D6 | **Reflex scope guidance** — verified: enablement scope (user / project-committed / project-local / managed) decides where hooks fire, so ubiquity is the adopter's install choice, not awow gating | what awow *recommends* per situation: (a) user-scope + tiered content (fires everywhere, light generic reflex in unknown repos); (b) project-scope only (committed for Path A, local for Path B — reflex exactly where connected) | document both in `/hub-setup`; default recommendation (b), with (a) as the power-user option — either way every injected pointer is reachability-checked, and opt-out is `enabledPlugins: false` in local settings |

## Open questions carried from the feedback

- CI flows with no hub/plugin present degrade to no-awow — acceptable? (Likely yes; state it.)
- Path A on public repos: who reviews that committed context stays public-safe over time? (Candidate: the connect-installed pre-push scan owns this lint.)
- Worktree gap for Path B connectors (untracked file absent in new worktrees) — detection helper warns + `/connect-project` re-run, or a worktree hook copies it.

## Suggested sequencing

1. Review and accept this proposal; mark `plugin-distribution.md` superseded.
2. File board issues per work item (WI-1..4) plus one decision issue for D1–D5; WI-1..3 can start immediately, path-independent.
3. Spike first: the two carried-over verifications (skill-override resolution; mid-session file visibility) plus a dry run of `gather.py --surface plugin` against a scratch install.
