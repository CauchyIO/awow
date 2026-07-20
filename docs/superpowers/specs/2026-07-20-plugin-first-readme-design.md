# Plugin-first README, payload self-sufficiency, and situational skill invocation

**Date:** 2026-07-20
**Branch:** `feat/plugin-first-readme`
**Base:** `main` @ `dc1edc7`
**Status:** design locked, awaiting implementation plan
**Revision:** v5

**Convention this spec follows:** every list states the rule that generates it. A list without its rule is a latent inconsistency — the next member has nothing to be checked against, and the omission stays invisible until something is added wrongly. Two of the five revisions below fixed instances of exactly that, in different sections, which is why it is written down here rather than left as a habit.

| Rev | Change |
|---|---|
| v5 | Corrected two §4.1 claims verified against the code: `lint-paths.py` needs no change, and `update-awow` is `channel: bootstrap` (which ships), not unmarked. §4.1's ship-list was asserted under a slogan that did not determine membership — and was wrong as stated, since `/setup-awow` tunes two files on the ships list. §4.1.2 now carries a testable predicate; §9 enforces it in CI. |
| v4 | `/update-context` became the tenth `autofire` command rather than a bespoke mechanism, and §4.5 gained the selection rule whose absence allowed that inconsistency through. |
| v3 | Added `/update-context` (§4.6) as PR 5. |
| v2 | Rewrote §4.1 around a path token after adversarial review found it had no addressing mechanism; D4 changed from one PR to one release across several. |
| v1 | Initial design. |

---

## 1. Problem

The README describes awow as *"A clone-and-go template for engineering teams adopting an agentic way of working"* (`README.md:3`) and routes adopters through a Python/`uv` bootstrap. That is no longer how awow is distributed. `main` ships a built `dist/` payload published to a public `awow-dist` repo, and three of four harnesses install as a plugin today.

The README does document plugin install — at `:113-117` for Claude Code and `:122-126` for Copilot — but buried below a clone-and-go lede, covering two harnesses, never mentioning `dist/`, `awow-dist`, Codex, or Pi.

Auditing the gap surfaced three defects that make a plugin-first README impossible to write honestly right now:

1. **The shipped payload is not addressable.** `dist/` contains zero `context/` and zero `setup/` paths. Nineteen of twenty shipped commands reference `context/` paths that ship empty; three hard-stop outright (`daily-digest:58`, `daily-routine:61`, `kb-mine:60`). Critically, there is no path token that resolves to the payload's own machinery — `{HUB}` resolves to the *adopter's repo root* in a plugin install (`.agents/AGENTS.md:24`, `using-awow/SKILL.md:14`), so simply copying files into `dist/` would place them where no command can address them.
2. **Session-start injection is broken by one path.** `hooks/session-start:19` reads `${PLUGIN_ROOT}/.agents/skills/using-awow/SKILL.md`; `dist/.agents/` contains exactly one file, `plugins/marketplace.json`. The skill ships at `dist/skills/` and `dist/agent-skills/`. Every plugin-installed session injects the literal string `Error reading using-awow skill` — reproduced by running `dist/hooks/session-start`. It works in the maintainer repo, where `hooks/` sits beside a real `.agents/`, which is why CI never caught it. `gather.py --check` validates that `dist/` matches its plan, not that the plan is sufficient.
3. **No command can fire situationally.** Zero of 24 commands (plus `awowify`) carry a `description:` frontmatter field. `gather.py:204` already prefers one and falls back to the H1 title, so today `process-transcript` advertises itself as *"gated pipeline for meeting transcripts"* — a label, not a trigger.

Two release blockers sit alongside these: `LICENSE` has never been committed on any branch (`git log --all -- LICENSE` returns empty) while the repo is public and four manifests declare MIT; and `README.md:111` recommends *"Use this template"* while the GitHub repo has `is_template: false`.

## 2. Goals

- A README that opens on the team problem, installs as a plugin on four harnesses, and tells a new user what to type next. ~700 words, down from 1,869.
- A plugin payload whose machinery is addressable and which produces value in an arbitrary repo with no vendoring and no `/setup-awow` gate.
- Commands and skills that fire from the situation the user is in, not only from a typed slash command.
- A smaller, honest surface: fewer shipped commands, and a skill surface that is not majority-telemetry.
- A path by which a rule stated in passing reaches the context tree instead of evaporating with the session (§4.6).

**Non-goals.** The hub-and-spoke adoption model (`meta/proposals/hub-and-spoke-adoption.md`) and the M365 Copilot harness (spec on branch `feat/m365-copilot-harness-spec`, not on `main`) are out of scope. Repairing `/awowify` is out of scope — see §4.1.4. This work does not preclude any of them.

## 3. Decisions taken

| # | Decision | Rationale |
|---|---|---|
| D1 | **The plugin is self-sufficient.** After install, the user gets value with no `/awowify` and no `/setup-awow` gate. `/setup-awow` becomes optional context-deepening; `/awowify` becomes an optional path for teams who want editable, git-tracked prompts. | The alternative — fixing `/awowify` to keep the vendoring on-ramp — puts three steps before any value. |
| D2 | **Telemetry ships as a second plugin,** `awow-telemetry@awow`. | Different audience, different dependency profile, different privacy posture. Accepted cost: two versions to sync, Tier 2 listing blocked twice. **Scope constraint discovered in review — see §4.3.** |
| D3 | **Fix Copilot before the README ships.** All four harnesses appear in the README. | Copilot is the only surface where command auto-firing already works end to end. |
| D4 | **One release, five PRs.** *(one PR in v1; four in v2; `/update-context` adds the fifth)* | v1 said one PR. Review established the diff touches ~40 command files, three separate `gather.py` features, three manifests, the hook, `tests/`, `LICENSE`, and a full README rewrite. That is not reviewable as one change. The release property D4 was protecting — the README never describes a state that does not exist — is preserved by the merge gate in §10. |
| D5 | **All work branches fresh off `main`.** | `feat/m365-copilot-harness-spec` is 80 commits behind. Its single commit is orthogonal. |
| D6 | **`/update-context` is the tenth `autofire` command, not a bespoke mechanism.** *(corrected in v4)* | v3 invented a special shape for it. The gate fires at a completion edge, which is exactly what `autofire` already does for nine others. Only the mid-task *noticing* needs resident prose, because invoking anything at that moment is the hijack. See §4.6. |
| D7 | **Not every command autofires.** | Two disqualifiers: consequential-and-hard-to-reverse (a misfire is damage), or trigger-too-broad (a misfire is noise, and noise is how the mechanism gets disabled). §4.5 states the rule; the list is its output. |

## 4. Architecture

### 4.1 Addressing the payload

#### 4.1.1 The problem v1 missed

Prompt bodies never hardcode locations; they use three tokens (`.agents/AGENTS.md:16-24`):

- `{HUB}` — shared team context root
- `{PROJECT}` — this project's context and drafts
- `{AWOW_TOOLS}` — awow's runtime tool scripts

`{HUB}` and `{PROJECT}` resolve to **the repo root** in any vendored *or plugin* install. Only `{AWOW_TOOLS}` is substituted at build time (`gather.py:397` → `${CLAUDE_PLUGIN_ROOT}/tools`; `:413` → `../../tools` for the agent-skills channel).

So a command reading `{HUB}/context/tooling/activity-collection.md` in a plugin install looks in *the adopter's repo*, not the payload. Copying that file into `dist/context/` puts it at an address nothing reads. **There is no token for "machinery bundled with the plugin."** That is the actual gap, and it is why nineteen commands reference paths that ship empty.

#### 4.1.2 The rule

> **A file ships if a default exists that is useful before `/setup-awow` runs.**

"Machinery ships, team data doesn't" is the slogan, but it does not determine membership — and taken literally it is wrong, because `/setup-awow` Step 6 tunes `mining-policy.md` and relocates paths in `knowledge-base.md`, both of which must ship. Touched-by-setup is not the test. **Useful-by-default is.**

That resolves into three classes:

| Class | Test | Ships | Examples |
|---|---|---|---|
| **Contract** | Identical for every adopter; nobody edits it | yes | `boards/*/reference/**`, `activity-collection.md`, `mining.md`, `synthesis.md`, `retros/canon.md` |
| **Template** | Ships with a working default; `/setup-awow` tunes it | yes | `mining-policy.md` (`selectivity: 2`), `knowledge-base.md` (default `kb_root`), `design-system.md` (`mode: absent`) |
| **Team data** | No meaningful default — a generic version is worse than absence | no | `mission.md`, `members.md`, `conventions/`, `style/`, `board.md`, `company/`, `architecture.md` |

The team-data test is the sharp one. A stub `mission.md` reading *"describe your team's mission here"* is not a weak default, it is an active harm: every command that reads mission gets noise instead of a clean absence it could branch on. Absence is information. That is why `board.md` gets §4.2's ask-once fallback rather than a shipped placeholder.

**This is CI-enforceable, and §9 enforces it.** Every path under `context/` carries its class, and the build asserts the ship list is exactly the Contract ∪ Template set. A new `context/tooling/*.md` that declares no class fails the build rather than silently not shipping — which is the failure mode a hand-maintained list guarantees eventually.

Two files fall through the v3 lists and are classified here: `context/tooling/architecture.md` is **team data** (written by `/setup-awow` Step 8, no useful default), and `.agents/AGENTS.md` never ships under any class — §4.6 prohibits writing it and `gather.py` mirrors it.

#### 4.1.3 The fourth token

Add `{AWOW_ROOT}` — the payload's own root — substituted at build time exactly as `{AWOW_TOOLS}` is:

| Channel | Substitution | Table |
|---|---|---|
| Claude (`dist/commands/`, `dist/skills/`) | `${CLAUDE_PLUGIN_ROOT}` | `PLUGIN_TOKEN_SUBSTITUTIONS`, `gather.py:397` |
| Agent-skills (`dist/agent-skills/`, Codex/Pi) | `../..` | `AGENT_SKILLS_TOKEN_SUBSTITUTIONS`, `gather.py:413` |
| Vendored / this repo | repo root (ships as-is) | — |

**Resolution precedence for machinery contracts:** read `{HUB}/…` first so a vendored override wins; fall back to `{AWOW_ROOT}/…`. Team data has no fallback — absent means absent.

There are **three** channels in play, not two: `vendored` (6 files, excluded from the payload) and `bootstrap` (2 files — `setup-awow.md`, `update-awow.md` — which *do* ship, because they create the vendored tree and their literal paths are the deliverable, per `lint-paths.py:36-38`). §4.4's `update-awow` change is therefore **`bootstrap` → `vendored`**, not marking an unmarked file.

Dependent changes, all required for the token to function:

- `tools/lint-paths.py` — **no change needed.** Verified empirically: `BARE` at `:11` is `(?<![{/\w.\-])(context|tools|proposals)/`, and the `/` in `{AWOW_ROOT}/context/` falls inside the negative lookbehind, so the new token passes exactly as `{HUB}/` does. (v2 listed this as a required change; it was wrong.)
- `.agents/AGENTS.md:16-24` — the "Path tokens" section becomes four tokens.
- `using-awow/SKILL.md:14` — same amendment, plus §4.2's ask-once rule.
- Every command that reads a shipped contract must be rewritten to `{AWOW_ROOT}` with `{HUB}` precedence. Includes `process-workitem.md:11`, which currently hardcodes `.agents/commands/_workitem-archetypes/`.

#### 4.1.4 What ships

This list is the **output** of §4.1.2's predicate, not an independent decision. If the two ever disagree, the predicate wins and this list is the bug.

**Contract + Template — ships, addressed via `{AWOW_ROOT}`:**

```
context/tooling/boards/{linear,jira,azure-devops,github-issues}/**   contract
context/tooling/activity-collection.md                               contract
context/knowledge-base/{README,mining,synthesis}.md                  contract
context/kb-inbox/README.md                                           contract
context/retros/{canon,anti-patterns}.md                              contract
context/tooling/knowledge-base.md                                    template  (default kb_root)
context/knowledge-base/mining-policy.md                              template  (selectivity: 2)
context/tooling/design-system.md                                     template  (mode: absent)
.agents/commands/_workitem-archetypes/**  → dist/commands/_workitem-archetypes/
```

**Team data — never ships:**

```
context/team/**   context/company/**   context/tooling/board.md
context/tooling/architecture.md        setup-progress.md
```

**`setup/**` does not ship, and `/awowify` stays broken this release.** v1 claimed shipping `setup/` would unbreak it. It would not: `setup/awowify.sh:66` copies `.agents tools setup context mcps pyproject.toml SETUP.md REFERENCES.md` from `$CLAUDE_PLUGIN_ROOT`, and the payload has none of that shape — no `dist/mcps`, no `dist/pyproject.toml`, no `dist/SETUP.md`, no `dist/REFERENCES.md`, and a `dist/.agents/` holding one file. Worse, `/awowify`'s job is vendoring `context/team/**`, which this section forbids shipping. Repairing it is a separate design problem. **This release: `/awowify` is documented as clone-and-run (`setup/awowify.sh --target /path`), not as a plugin command.**

**The Copilot payload is generated, not globbed.** v1 said ship `.github/**`. That glob would ship `ci.yml` — which would then execute inside `awow-dist` against a repo with no `.agents/` — plus 35 dead pointer stubs linking `../.agents/…`, plus vendored-only prompts (`awow-add`, `awow-reset`, `awow-status`, `test-awow`, `update-awow`), bypassing the channel filter and undoing §4.4. Instead `gather.py` generates `dist/.github/plugin/plugin.json` and `dist/.github/prompts/*.prompt.md` from `.agents/` like every other surface, honouring `channel:`.

### 4.2 The board fallback

`context/tooling/board.md` is cited by **fourteen** command files — thirteen besides the `/setup-awow` that authors it. Three hard-stop on it (`daily-digest:58`, `daily-routine:61`, `kb-mine:60`). It is the one genuinely un-vendorable file: `/setup-awow` Step 1 generates it per-adopter, and it exists nowhere on `main`.

Replace each hard stop with:

> If `{HUB}/context/tooling/board.md` is absent, infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. If it cannot be inferred, ask the user once which board they use and how to reach it, and record the answer for the session. Do not halt, and do not ask again. Offer `/setup-awow` Step 1 to make the answer durable.
>
> This relaxation covers an absent board pointer only. A fatal auth failure on a data source still halts — do not synthesise from a half-snapshot.

The second paragraph is not optional. All three current hard stops read *"no `board.md`, **or a fatal auth failure on a source**"*; dropping the auth half would trade a startup gate for a correctness bug.

**Apply to eleven commands** (post-trim, so `daily-routine` and `project-manager` are excluded): `daily-digest`, `kb-mine`, `daily-checkin`, `my-work`, `process-workitem` (`:30`), `project-plan` (`:46`), `refinement-prep`, `coaching-review`, `process-retro`, `process-transcript`, `solution-design-flow`. The last four were missing from v1's list, and two of them are in the day-one six — §8's acceptance criterion is unreachable without them.

**Where the session answer lives.** "Do not ask again" is cross-command state and needs a mechanism. Use the existing repo-local flag pattern that `hooks/session-start:25` already reads: write the inferred or supplied board to a session-scoped note under `.awow/`. Without naming this, an implementer builds per-invocation asking, which is not what this section means.

**Inference rules.** GitHub remote → GitHub Issues via `gh`. GitLab, Bitbucket, Azure DevOps remotes → do not guess a board from the remote; ask. No remote → ask. `gh` absent or unauthenticated → ask, and do not offer the `gh` path.

### 4.3 The plugin split

`marketplace.json` gains a second entry:

```
awow@awow            → the way of working    (4 behavioural skills + 16 commands)
awow-telemetry@awow  → the evidence layer    (5 skills + their tooling)
```

**Scope constraint discovered in review: `awow-telemetry` is Claude-Code-only this release.** `dist/.agents/plugins/marketplace.json` declares one plugin at `source.url = "./"` — the dist root *is* plugin #1. `tools/sync-dist.sh` mirrors only `dist/` with `rsync --delete`, so a sibling `dist-telemetry/` never publishes, and a nested `dist/telemetry/` sits inside plugin #1's tree. Pi gets one `package.json` declaring `pi.skills: ["./agent-skills"]`. Solving Codex and Pi means restructuring the publish topology — out of scope. The README must say so.

`gather.py` gains `channel: telemetry` alongside `channel: vendored` (`gather.py:424`), building into a named second root. Three consequences:

- **Orphan detection must learn a second root.** `find_orphans:707` is the identity check `if surface == DIST_DIR`. A second root falls through to the `GENERATED_MARKER` branch, and full-copy payload content carries no marker (`plugin_command_copy:430`, `command_skill_stub:495`, `skill_stubs:453`). Orphans would be undetected, never removed, and `--check` still green. Also touches `SURFACE_ROOTS:667`, the `--surface` choices at `:727`, `filter_surface:684`, and the `DIST_DIR in surfaces` guard at `:735`.
- **`PLUGIN_TOOL_PATHS` must split.** `project-timeline` has no `scripts/` directory — its implementation is `{AWOW_TOOLS}/session_timeline.py`, `session_timeline_template.html`, and `mlflow_reader.py`, listed at `gather.py:123-129` interleaved with non-telemetry `hooks/leak-patterns.txt` and `hooks/pre-push`. That list splits by channel. Note `awow_extract.py:57-60` imports `mlflow_reader` from `<repo>/tools/`.
- **Telemetry soft-depends on base-plugin content.** Acceptable when only telemetry is installed? Decide before shipping.

**Moving:** `mlflow-export`, `prompt-skill-analysis`, `project-timeline`, `awow-usage-coach`, `session-export`.
**Staying:** `using-awow`, `board-aware-development`, `architecture-aware-development`, `user-story-template`.

**Dangling references — the real list.** v1 named two innocent files. `daily-digest.md` and `weekly-digest.md` reference none of the moving skills. Actual sites: `.agents/skills/session-correlation/SKILL.md`, `.agents/commands/setup-awow.md:262-264`, `.agents/AGENTS.md`, `.agents/skills/README.md`, `awow_extract.py:78` (`"weekly-digest": "standardise"` — a moving skill naming a deleted command), and `guides/guide-{trace-analysis,session-timeline,session-correlation,prompt-taxonomy}.html` plus `guides/index.html`.

### 4.4 Command consolidation

Twenty shipped commands become sixteen: −2 vendored, −2 merged. (`test-setup-awow` is already `channel: vendored` and absent from `dist/commands/`, so deleting it changes the shipped count by zero — it is a repo cleanup, not a surface cut.)

**Delete from the repo (1):** `test-setup-awow` — 18 lines, self-declared deprecated, forwards to `/test-awow setup-awow`. `meta/proposals/eval-baseline-and-prompt-cleanup.md:40` set the exit condition; the rename has settled. Remove generated stubs and update the two `meta/proposals/` references.

**Mark `channel: vendored` (2):**

- `update-awow` — actively corrupting in plugin-land. `backfill` writes a near-empty lockfile, `_compute_plan` walks `dist/`, classifies plugin internals as `new`, and `apply` dumps them into the user's repo under the banner "updating awow." Redundant too: its L37-38 tells plugin users to run `/plugin update awow`, which *is* their entire update.
- `project-manager` — L13 is a self-declared park notice: *"No active adopter runs this loop — the maintainer has never invoked it."* Keep the file; its re-entry condition is written into it.

**Merge (2 → 1):**

- `daily-routine` → `daily-digest`. Its sole justification is the gather-once optimisation, but both children already reuse the snapshot independently (`daily-digest.md:56`, `kb-mine.md:56-57`). Its own `:37` calls the phases *"independent projections… not a chain."* Fold in one closing offer — *"Run `/kb-mine` against the same snapshot?"* — and delete.
- `weekly-digest` → `daily-digest` as a window parameter. **This merge is larger than v1 claimed.** Not three templates: nine output subsections (`weekly-digest.md:81-181`), plus ISO-week/Mon–Fri resolution (`:32-40`), an extra primary source — every `digests/YYYY-MM-DD.md` in the window with a coverage-gap rule (`:46-48`) — last-week comparison (`:50-52`), a different metric set (`:58`), and a different output path (`:76`, `:190-192`). Weekly reads daily-digest's own prior outputs, which is a Phase-0 control-flow branch, not a fold-in. **No `/weekly-digest` alias — the command is removed outright.** The weekly window survives as a `/daily-digest` parameter; the name does not.

**Rework `daily-digest`'s delivery (Phases 4–6).** The team stopped sharing digests by email; digests now land as a markdown file for an eleventy site, delivered by PR. The existing phases are built for the abandoned path, and their rendering rules are *email-client* constraints that actively fight the new one (`:216-223`: *"Use **table layout** (not div-only)… All styles must be **inline** — email clients strip `<style>` blocks"*). `digests/TEMPLATE.html`, which Phase 4 reads, has never existed in git.

New shape:

| Phase | Was | Becomes |
|---|---|---|
| 3 | Markdown → `digests/YYYY-MM-DD.md` | Same, plus eleventy front matter |
| 4 | HTML render from `TEMPLATE.html` | **Deleted.** Review gate moves here |
| 5 | Browser review gate | Open the PR |
| 6 | Send email | **Deleted** |

No HTML rendering in `daily-digest` at all. A styled standalone digest is `/artifact`'s job — it already owns house-styled HTML and reads the design system, so duplicating that inside one command buys nothing. `digests/TEMPLATE.html` is never created; if a template is wanted it is an eleventy layout living in the eleventy site, not in awow.

Drop the now-dead frontmatter and boundary lines: email mode detection (`:35-39`), the `Never send email without explicit user approval` and `Never hardcode recipients` boundaries (`:278-279`), and the "Optional email rendering and delivery require explicit user approval" clause at `:14`.

Combined with the weekly-window merge above, `daily-digest` is the single largest file change in this release. Sequence the two edits — window parameter first, delivery rework second — so the phase renumbering happens once.

**Explicitly not culled** — recorded so it is not relitigated. `project-plan` and `kb-mine` are never-used but are the sole producers of what `process-workitem` and `kb-synthesize` consume. `design-system` is rare by design and the sole producer of `artifact`'s templates. `coaching-review` has a narrow trigger but works at zero context. `process-retro` must not merge into `process-transcript` — the former is board-independent, and merging would drag portable value behind a board dependency.

**Lockfile and starter manifests.** `tools/awow.lock.json` is git-tracked, says `awow_version: 0.2.0`, and still lists `cross-team-view.md`, `daily-routine.md`, and `weekly-digest.md`. `awow_lock.py:41-42` states the sync constraint; `awowify.sh:74` / `awow_lock.py:79` exclude `test-setup-awow.md`; `:83` / `:90` list `weekly-digest.md`. Regenerate the lock as part of this work and state what that means for vendored adopters mid-upgrade.

### 4.5 Situational invocation — three layers

**Layer 1 — fix the hook.** `hooks/session-start:19` tries `${PLUGIN_ROOT}/skills/using-awow/SKILL.md` first, falls back to `.agents/skills/…` so the maintainer repo still resolves. Read the **`dist/skills/`** copy specifically, not `dist/agent-skills/` — the two bodies differ by token substitution (`render_plugin_body` vs `render_agent_skills_body`), and injecting the agent-skills body gives a Claude session a tools path resolving nowhere.

Add a regression check invoking `dist/hooks/session-start` (the hook derives `PLUGIN_ROOT` from its own location at `:12-13`) and asserting no `Error reading` string. `--check` structurally cannot catch this class of bug. Lives in `tests/harness/`, which `ci.yml` already runs via `run-harness-tests.sh all`.

**Layer 2 — trigger-shaped descriptions.** Write a `description:` into the frontmatter of all sixteen shipped commands. `gather.py:204` and `:437` both prefer an explicit field, so one edit propagates to `dist/commands/*.md` (picker) and `dist/agent-skills/*/SKILL.md` (Codex/Pi/Copilot trigger) together.

The convention names the *situation the user is in*, not the mechanism:

```
mechanism-shaped (today):  "gated pipeline for meeting transcripts"
situation-shaped (target): "Use when the user hands over a meeting transcript
                            or recording notes (.vtt, .srt, pasted text), or asks
                            to turn a meeting, standup, refinement, or stakeholder
                            interview into board items."
```

**Format constraint — verified empirically.** `parse_frontmatter` (`gather.py:159-170`) is line-based. `description: >-` yields the literal string `'>-'`; I ran it. At 30–45 words an implementer will reach for a block scalar, and every stub, picker entry, and trigger silently becomes `">-"` with `--check` passing. **Descriptions are single-line, double-quoted. `parse_frontmatter` must reject block-scalar indicators rather than storing them.** Full table in §7.

**Layer 3 — mirror commands into `dist/skills/`.** Today `dist/agent-skills/` carries all twenty command mirrors and `dist/skills/` carries zero. Layers 1–2 therefore buy real auto-fire on Codex, Pi, and Copilot but only a better picker on Claude Code. `gather.py:517` must also emit selected command mirrors into `dist/skills/`.

Selection is a new frontmatter field, `autofire: true`, not a hardcoded list — the list would drift from the commands it names.

**The selection rule.** A command autofires unless it fails either test:

- **Consequential and hard to reverse.** A misfire is damage, not noise. `/setup-awow` rewrites the whole context tree; `/awowify` vendors ~150 files into the repo; `/design-system` stands up a house style; `/kb-synthesize` writes past a gate into the durable KB. Discovery is not worth a destructive misfire on a phrasing coincidence.
- **Trigger too broad.** `/my-work` would fire on any planning question, `/daily-digest` on any "what happened" question, `/kb-mine` on any "worth writing down" phrasing. Read-only, so the cost is noise rather than damage — but noise is how the whole mechanism gets switched off.

The list is the rule's output, not the rule. **Autofire:** `process-transcript`, `process-retro`, `coaching-review`, `artifact`, `refinement-prep`, `solution-design-flow`, `process-workitem`, `project-plan`, `daily-checkin`, and `update-context` (§4.6). **Explicit-invocation only:** `my-work`, `daily-digest`, `design-system`, `kb-mine`, `kb-synthesize`, `setup-awow`, `awowify`.

**Why not make every command a skill.** On Codex, Pi, and Copilot it already is — `gather.py:517` emits an agent-skill for every command. The question only bites on Claude Code, where commands sit in the `/` picker and cost nothing resident. Making all twenty resident there reintroduces exactly the context tax D2 removes by splitting telemetry out: every skill description loads into every session, whether or not it is ever used.

**Honest limitation.** `autofire` controls the Claude surface only. `gather.py:517` emits agent-skills for *every* command, so `my-work`, `kb-mine`, `kb-synthesize`, `setup-awow`, and `awowify` remain auto-fire candidates on Codex, Pi, and Copilot regardless. Either accept this asymmetry or add a second field suppressing the agent-skills description. **Recommend accepting it** and documenting the behaviour — suppression means a command invisible to three of four harnesses' triggers, which is worse.

Note `artifact` would then exist three times: `dist/commands/artifact.md`, `dist/skills/artifact/SKILL.md`, `dist/agent-skills/artifact/SKILL.md` — with `plugin_command_copy:430` preserving `phase`/`prerequisites` and `command_skill_stub:495` stripping them. Reconcile the frontmatter contract before implementing.

### 4.6 `/update-context` — catching rules stated in passing

**The gap.** Nothing captures a durable rule expressed mid-session. `/kb-mine` reads an activity snapshot of board/code/chat queries (`kb-mine.md:52-62`), never the conversation. `/process-retro` needs a retro transcript. `/setup-awow` is a one-time bootstrap. A user saying *"we always put the ticket ID in the branch name"* is captured by nothing, and the rule evaporates with the session.

**Two moments, two mechanisms.** The failure of an earlier draft was treating this as one thing and inventing a bespoke mechanism for it. It is two, and only the first needs anything unusual.

- **Noticing**, mid-task: spot a durable rule and fold a one-line note into the reply already being written. This cannot be an invocation — invoking anything here *is* the hijack. It is a behaviour modifier during other work, which is what session-resident prose is for.
- **The gate**, at a completion edge: route, diff, ask, write. A bounded job with a beginning and an end, run when the work is done and nothing competes for the turn. That is an ordinary command, and a completion edge is precisely when a skill election is cheap.

So `/update-context` is **the tenth `autofire` command** (§4.5 Layer 3), not a special case. No new mechanism.

| Piece | What | Why |
|---|---|---|
| Noticing | ~5 lines added to `.agents/skills/using-awow/SKILL.md` | Already `cat`-ed into every session by `hooks/session-start`. Covers the one moment an invocation cannot. Trigger and budget only — no workflow summary (`writing-skills` documents that summarising a process in a description makes the agent follow the summary instead of the content). |
| Machinery | `.agents/commands/update-context.md`, `autofire: true` | Routing, format inference, diff generation, the gate, provenance. Mirrored into `dist/skills/` like the other nine. |
| Queue | `context/kb-inbox/` with `kind: guidance` | One staging dir, one drain. `/kb-synthesize` grows a `kind: guidance` branch. |

**What remains unbuildable, and why it does not matter here.** Skill invocation is a model election at generation time, not an event subscription — the harness loads name+description into the system prompt and the model elects to call `Skill` during its own turn. There is no matcher on user text. The only true user-turn event is a `UserPromptSubmit` hook, which appears **nowhere** in awow or the Superpowers cache and is pre-model, hence regex-only. This rules out firing *the gate* at the moment a rule is spoken — which the completion-edge budget below rules out anyway, for independent reasons. **No new hook.**

**The discrimination rule** — three predicates, all must hold:

- **P1 residue:** after doing exactly what was asked, does something remain that changes behaviour in an unrelated session next week? Expressible as "when X, do Y" without naming this file or this ticket.
- **P2 asserted:** stated as a rule, not floated. *"We should probably standardise filenames at some point"* fails.
- **P3 normative and team-scoped:** a rule the team obeys, not a fact about the world (facts go to the KB lane), and not one person's preference.

Scoping words — *here, for this one, just this time, in this file* — veto unconditionally.

P3 carries the two load-bearing negatives. *"The staging DB is eu-west-1"* is durable, general, and asserted — only P3 routes it to the KB instead of `conventions/`, and without it this races `/kb-mine`. *"Please stop saying 'You're absolutely right'"* passes P1 and P2 cleanly and would fire under a naive trigger, manufacturing a **team convention out of one person's dislike, committed to git, binding on everyone.** That is the worst available failure and P3 must exclude it structurally.

**Interrupt budget.** Silent capture is unlimited. Inline acknowledgement is unlimited — one line folded into a reply that was already happening, never its own message, never a question:

> …pushed to `feat/gather-mirror-fix`. (Noted "we always put the ticket ID in the branch name" as a standing rule — I'll offer to write it up when we wrap.)

**The gate fires once per session, at a completion edge only** — commit, PR, "that's it for today". Never mid-task; the exemption clause is not negotiable, because `writing-skills` is explicit that *"don't interrupt unless it's important"* reopens the negotiation and the skill will interrupt. It shows the actual diff and the verbatim source quote — a gate the user can approve without seeing the literal text is broken. Options: `1` / `all` / `none` / `none, stop asking` (writes `.awow/no-context-prompt`, silent for good) / `N → <path>` to retarget / `N defer` to stage for the next drain. If the session ends with no completion edge, candidates expire. **Losing a candidate is acceptable; interrupting is not.**

**Routing — three tiers, and tier 3 is the point.**

1. Unambiguous named destination → propose it with the diff.
2. Two or more candidates → present a picker, not a typed question.
3. **No suitable destination → stage as `suggested_target: UNROUTED` and stop.** Never create a new convention file. An agent inventing `conventions/REQUIRED/git-workflow.md` has made a file no README indexes, no command reads, and `setup-awow` does not know about — at the moment of least deliberation. Unrouted candidates accumulating is useful signal about what the context tree is missing.

The tree is genuinely not deterministic. `style/` vs `conventions/` canonicality is a parked question in `placement.md:27` — parked against `input/research/proposal_questionnaire.md`, which does not exist. Resolving it would collapse a class of tier-2 pickers into tier 1; worth doing, out of scope here.

**Hard prohibitions, written into the command body:**

- **Never write `.agents/AGENTS.md`, root `AGENTS.md`, `.claude/CLAUDE.md`, or `.github/copilot-instructions.md`.** The last three are `gather.py` mirrors (`gather.py:336-337`); edits there are destroyed on the next gather. Write to `context/`, let propagation happen.
- **Fix the same bug in `/process-retro` while here.** `process-retro.md:264`, `:284`, `:324` all target `CLAUDE.md` / `copilot-instructions.md` directly. Those instruction diffs have been silently discarded on every gather since the command shipped. Retarget to `.agents/AGENTS.md`.
- Resolve `kb_root`/`inbox` via `context/tooling/knowledge-base.md` before any KB-side write.
- Infer target format from the file's existing siblings — there is no convention-file template, three de-facto formats coexist. Add no frontmatter; the durable layer stays frontmatter-light.
- Handle documented-but-absent targets (`context/tooling/board.md`, `architecture.md` are referenced but do not exist here).
- Never autonomous. No `--auto` mode — `synthesis.md:65-72` already parks that for the KB drain on the same reasoning.

**Not built:** confidence scores (invents a number nobody can calibrate; a three-predicate boolean is testable), cross-session repetition counting (`awow-usage-coach` owns recurrence-based nudges with a defensible statistical bar), a second staging directory, a third SessionStart injector, agent-created convention files.

**Accretion duty.** The realistic three-month outcome is `output-discipline.md` carrying 40 rules, half contradictory, each individually defensible — and REQUIRED conventions are read every session, so bloat there taxes every future turn. Cap each convention file (10 rules), and on hitting the cap `/update-context` must propose a **merge or replacement**, not an append.

**Under-firing is the unbudgeted risk.** A resident paragraph fires when the model happens to weigh it; quiet is indistinguishable from working. `/update-context` invoked manually with no batch must report *"nothing captured this session"* rather than nothing at all — that single line is the difference between a feature you can tune and one you cannot.

## 5. The README

### 5.1 Voice

Rules lifted from the team writing guides (which live in a separate private repo) so this spec stands alone:

- **Primary:** practitioner energy, not vendor energy. *"Code blocks are documentation… Readers will come back for the code, not the paragraphs around it."* Excited about the problem, not the tooling. Name the gap, then fill it. Distinguish solid from rough inline, not in footnotes.
- **Floor:** never open by restating the topic, never close by summarising, max 1–2 bold elements, real numbers in lists rather than a reflexive five or seven.
- **Brevity mechanics:** lede under ten words, one idea per paragraph, cut adverbs and hedges, end at the action. Borrow the discipline, not the Axios furniture — no *"Why it matters:"* signposts.
- **Ban list:** no *ensures, enables, leverages, robust, seamless, cutting-edge, empower*; no *simply, just, easily*. Framing is **capability, not dependency**.

### 5.2 Structure

**Target ~700 words, gate at 750.** v1 said 600; the content inventory below does not fit in 600 without dropping something the release requires.

```
Title + lede            <10 words, states what it is
The problem             2-3 sentences, team-level, not tooling
Install                 4 code blocks, one per harness
Then what               the day-one six
What changes            the session-start injection, 3 sentences
Prerequisites           gh authenticated, or an MCP for your board
Going deeper            /setup-awow, explicitly optional
Status                  what's solid vs rough, inline
License
```

Four items the README must carry that v1's inventory missed:

- **Two install repos.** Claude Code installs from `CauchyIO/awow`; Codex and Pi from `CauchyIO/awow-dist`. A reader who notices assumes a typo. Explaining costs ~30 words; not explaining is a support burden.
- **`awow-telemetry`.** A second plugin ships in the same release. Name it, and state it is Claude-Code-only (§4.3).
- **Prerequisites.** Four of the day-one six touch a board.
- **Copilot's shape.** Copilot has skills, not slash commands. One clarifying sentence, or the day-one six read as broken there.

**Install** — the three verified paths plus Copilot once D3 lands:

```
Claude Code   /plugin marketplace add CauchyIO/awow
              /plugin install awow@awow
Codex         codex plugin marketplace add https://github.com/CauchyIO/awow-dist
              codex plugin add awow@awow
Pi            pi install git:github.com/CauchyIO/awow-dist
Copilot       copilot plugin marketplace add CauchyIO/awow
              copilot plugin install awow
```

The Copilot block is the *currently documented* one (`README.md:125-126`). It fails today because `.claude-plugin/marketplace.json` resolves `source: "./dist"` and `dist/` contains no `.github/` — the repo has `.github/plugin/plugin.json`, but installers no longer fetch the repo root. §4.1.4's generated Copilot payload is what makes this command true.

**The day-one six**, chosen for zero-context viability, distinct value slot, and because together they narrate a loop:

| Command | Why it earns a README line |
|---|---|
| `/my-work` | Highest value-per-dependency. Regrouping board rows into *Needs you now / In flight / Waiting / Next up* is pure reasoning over whatever rows come back. |
| `/process-workitem` | The flagship outer loop: board item → planned change → PR. |
| `/refinement-prep` | Self-described as the first prompt a team adopts, and runnable by one person alone. |
| `/process-transcript` | Ranks third in real usage. Parsing, re-attribution, and extraction templates degrade gracefully — `:71` instructs the agent not to gate on context. |
| `/solution-design-flow` | The only command converting an architecture argument into a durable record. Never writes to the board. |
| `/artifact` | The only one producing something a stakeholder sees. Its design-system dependency is a graceful fallback, not a gate — once §4.1.3's token lands. |

`/design-system` and `/coaching-review` are named in prose, not the headline list.

**Note on `/my-work`:** §4.5 excludes it from `autofire` as too broad a trigger, while §5.2 leads with it and §7 gives it a precise description. Both hold — it is the best *typed* first command and a poor *inferred* one. The README presents it as something you type.

### 5.3 Deletions

Cut from the README: the starter-owned/team-owned ownership table (`:99-109`), the pointer-stub architecture essay (`:84-93`), the *"Use this template"* recommendation (`:111` — `is_template: false`), `retro-reports/` from the tree (`:67` — never existed), and *"The design inputs that informed this repo live under `input/`"* (`:139` — `input/` holds one README).

Wider docs sweep, since these become wrong in the same release: `SETUP.md` (7.4 KB) still documents the clone-and-go wizard and cites the never-committed `input/PROPOSAL.md` at `:45`; `guides/index.html:638` still names `cross-team-view`, culled from `main`; `guides/guide-setup-and-two-harnesses.html` is titled for two harnesses in a four-harness release; `dist/README.md` is the payload's front page and unmentioned anywhere; `.agents/AGENTS.md` references deleted commands. Four commands vanish from the picker — add a deprecation note.

## 6. Release blockers

- **`LICENSE`.** Commit MIT, `Copyright (c) 2026 Casper Lubbers`. Four manifests declare MIT, the repo is public, and the file has never existed in git.
- **`is_template`.** Either flip it on the GitHub repo or remove the recommendation. §5.3 removes it.

## 7. Command descriptions

Written into `.agents/commands/<name>.md` frontmatter — except `awowify`, whose source is the top-level `commands/awowify.md`. Single-line, double-quoted (§4.5).

| Command | `description:` |
|---|---|
| `my-work` | Use when the user asks what they should work on, what is pending or waiting on them, or says they have lost track of the board and want to get oriented before starting a block of work. |
| `process-workitem` | Use when the user points at a board item — a ticket ID, issue link, or "let's pick up X" — and wants it carried from refinement through a planned code change to an opened PR. |
| `refinement-prep` | Use when the user has a feature brief, quarterly slidedeck, or board issue and wants it broken into right-sized stories before a refinement session, or asks to prep work for the next refinement. |
| `process-transcript` | Use when the user hands over a meeting transcript or recording notes (.vtt, .srt, pasted text), or asks to turn a meeting, standup, refinement, or stakeholder interview into board items. |
| `solution-design-flow` | Use when the user is weighing architectural or solution options, is about to lock a design decision, or points at a transcript of a design discussion — before the decision only exists in chat. |
| `artifact` | Use when the user asks for a deck, slides, a blog post, one-pager, or report as HTML or PDF — any styled document that should follow the team's house style instead of hand-written CSS. |
| `design-system` | Use when the user wants one house style for the HTML they generate — asks to stand up or adopt a design system, points at a site or brand to derive tokens from, or says every deck looks different. |
| `coaching-review` | Use when the user shares a transcript or recording of a coaching, pairing, mentoring, demo, or onboarding session and wants feedback on how the teaching went, not on what was decided. |
| `daily-digest` | Use when the user asks what the team shipped today or this week, wants a daily or weekly digest written up and raised as a PR, or says they have no idea what other people are working on. |
| `daily-checkin` | Use when the user recounts their day, points at a check-in note or voice memo, or wants the board to reflect today's work — end-of-day logging, standup prep, catching untracked work. |
| `project-plan` | Use when a design is locked and decomposed but nothing says what blocks what — the user asks for build order, sequencing, a delivery plan, or a critical path, or just finished /solution-design-flow. |
| `process-retro` | Use when the user points at or pastes a retrospective transcript or recording notes, or asks to turn a retro into named anti-patterns, owned actions, and diffs to their agent instructions. |
| `kb-mine` | Use when the user asks what's worth writing down from a day's work, wants to backfill knowledge-base candidates for a past day, or says hard-won insight is evaporating unrecorded. |
| `kb-synthesize` | Use when mined knowledge candidates are piling up unpromoted, or the user asks to drain the KB inbox, review staged candidates, or fold recent learnings into the durable knowledge base. |
| `setup-awow` | Use when a repo has awow files but no board wiring or team context yet, or the user asks how to get started with awow, connect their issue board, or resume an unfinished setup. |
| `awowify` | Use when the user wants awow's prompts vendored into this repo as editable, git-tracked files — adding awow to an existing codebase, or customising the commands rather than using them as shipped. |

Vendored-only commands (`awow-add`, `awow-reset`, `awow-status`, `test-awow`, `update-awow`, `project-manager`) also carry no description and fall back to the H1 in the vendored picker. Adding descriptions there improves picker quality but is out of scope; none should carry `autofire`.

## 8. Versioning, tests, rollback

**Channels.** Three, not two: `vendored` (excluded from payload), `bootstrap` (ships; creates the vendored tree), `telemetry` (new, §4.3). PR 3 must not assume a binary.

**Version.** `plugin.json` is `0.5.0`; `awow.lock.json` says `0.2.0`. Four commands leave `dist/commands/` and a second plugin ships — **`0.6.0` minimum**. `awow-telemetry` versions in lockstep with `awow` for this release.

**Tests affected.** `tests/daily-digest/` (four model-graded suites whose fixtures and rubrics reference `board.md` and `activity-collection.md` — the §4.2 fallback changes expected behaviour), `tests/setup-awow/`, `tests/harness/codex/wiring.sh`, `tests/awow-lock/`. `ci.yml` runs three jobs: `gather.py --check`, `lint-paths.py`, and `tests/harness/run-harness-tests.sh all`. `lint-paths.py` needs no change (§4.1.3).

**Rollback.** Revert on `awow`, re-run `tools/sync-dist.sh --apply`, merge the revert PR in `awow-dist`. `/plugin update awow` is the user-facing recovery and is not instant — installed users stay on the bad version until they update.

## 9. Verification

Split by owner, because four of these are live installs that no CI job currently performs.

**CI:**
- `python tools/gather.py --check` passes.
- `dist/hooks/session-start` emits no `Error reading` string (new, `tests/harness/`).
- **Payload classification.** Every path under `context/` carries a class (contract / template / team-data per §4.1.2), and the shipped set equals Contract ∪ Template exactly — both directions, so an unshipped contract fails as loudly as a shipped team-data file. An unclassified path fails the build. This replaces the v3 check, which was `grep -c 'context/team\|context/company\|setup-progress'` — a three-prefix denylist that would have passed a shipped `architecture.md` and passed a silently-omitted `mining.md`.
- `python tools/lint-paths.py` passes unchanged (the `{AWOW_ROOT}` token needs no lint change — see §4.1.3).
- README word count under 750.

**Human release checklist:**
- Live install of `awow@awow` into a scratch repo with no `context/`: each of the day-one six either completes or asks once and proceeds. None hard-stops.
- Live install of `awow-telemetry@awow` resolves its tooling.
- Codex and Pi installs resolve from `CauchyIO/awow-dist`.
- Copilot install resolves from the generated `dist/.github/`.

## 10. Sequence — five PRs, one release

**PR 1 — payload correctness, and all of `using-awow`.** The `{AWOW_ROOT}` token and both substitution tables; `lint-paths.py`; the machinery file list; the generated Copilot payload; `/setup-awow` path drift.

This PR makes **every** `using-awow/SKILL.md` edit in the release, in one coherent rewrite: the path-token amendment (§4.1.3), the board ask-once rule (§4.2), and the `/update-context` reflex paragraph (§4.6). PRs 2 and 5 then do not touch the file.

Landing the reflex paragraph before its command exists is safe because of the config-gate pattern `architecture-aware-development` already uses — *no pointer → do nothing, silently*. The paragraph checks for `/update-context`'s presence before offering, so it is inert until PR 5 and stays inert forever in a repo that skipped the command. This is also what makes `phase: standardise` opt-in work.

**PR 2 — surface trim and board fallback.** Delete `test-setup-awow`; `channel: vendored` on `update-awow` and `project-manager`; merge `daily-routine` and `weekly-digest` into `daily-digest`, then rework its delivery; regenerate `awow.lock.json`. **Then** apply the §4.2 fallback to the eleven survivors. Trim before fallback — v1 had these reversed, so step 1 edited files step 3 deleted.

**PR 3 — telemetry split.** `channel: telemetry`, second marketplace entry, orphan detection, `PLUGIN_TOOL_PATHS` split, the eleven dangling references.

**PR 4 — descriptions, hook, README.** §7 into frontmatter; `autofire` and the `dist/skills/` mirror; the Layer 1 hook fix; `LICENSE`; the README and the §5.3 docs sweep.

**PR 5 — `/update-context`.** The command (§4.6); the `kind: guidance` frontmatter widening in `context/kb-inbox/README.md`; the `/kb-synthesize` disposition branch; the `/process-retro` mirror-bug fix.

**Then:** run `tools/sync-dist.sh --apply` and merge the `awow-dist` PR.

**Merge gate.** PR 4 does not merge until PRs 1–3 are on `main`. **`awow-dist` syncs before or with PR 4, never after** — otherwise the README sends Codex and Pi users to a stale payload. This gate is what preserves D4's original property now that the work is five diffs.

Two independence rules. If PR 3 discovers a blocker it must not hold PR 4: drop `awow-telemetry` from the README and ship. **PR 5 is independent of PR 4** — it can land before or after, and if it slips, the reflex paragraph from PR 1 stays inert and nothing breaks. Do not let `/update-context` delay the README.

## 11. Open questions

- Does `/awow-add`'s two-tier active/inactive command premise survive self-sufficiency, where every command is live on install? Referenced from 24 files, so a follow-up, not part of this release.
- Where does the per-path class live — frontmatter on each `context/` file, or a manifest in `gather.py`? Frontmatter keeps the fact next to the file but adds it to a layer `kb-inbox/README.md` deliberately keeps frontmatter-light. A manifest centralises it but drifts. Resolve during PR 1; the predicate (§4.1.2) holds either way.
- What is the eleventy front-matter contract for `digests/YYYY-MM-DD.md` (layout name, permalink pattern, tags)? Needs one look at the eleventy site before PR 2 writes Phase 3.

## 12. Resolved

- **`LICENSE` holder** — Casper Lubbers, 2026. (§6)
- **`/weekly-digest`** — removed outright, no alias. The weekly window survives as a `/daily-digest` parameter. (§4.4)
- **`digests/TEMPLATE.html` and the email path** — deleted, not rebuilt. `daily-digest` produces markdown with eleventy front matter and opens a PR; styled HTML is `/artifact`'s job. (§4.4)
