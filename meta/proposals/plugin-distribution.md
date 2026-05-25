# Proposal — awow as a Claude Code plugin

**Status:** Draft — awaiting review.
**Scope:** add a *second* adoption path — a Claude Code plugin — alongside the existing GitHub-template clone. The plugin is Claude-Code-only; the Copilot path stays on the template. `/setup-awow` and the commands it surfaces are the load-bearing pieces that have to keep working under both distribution modes.

---

## Why

The template-clone model works, but it has a hard pre-commitment cost: the adopter has to clone an opinionated repo to *try* awow. That cost is paid before the team has seen a single ceremony run end-to-end. Several conversations have hit this — people want to see `/refinement-prep` or `/process-workitem` against their *own* repo before they restructure anything.

A plugin lowers activation energy:

1. **No clone.** `/plugin install awow` adds the commands to the user's existing Claude Code session, no template repo on disk.
2. **Reversible.** `/plugin uninstall awow` removes the commands; the adopter keeps anything `/setup-awow` scaffolded into their repo and decides what stays.
3. **Versioned.** Updates flow through the plugin marketplace, not by cherry-picking starter-owned paths back from upstream.

What it does **not** solve: Copilot users. GitHub Copilot has no plugin concept equivalent. The Copilot path stays template-based, served by `tools/gather.py` from the same `.agents/` source of truth.

This is a **second on-ramp**, not a replacement. The template still ships, the docs still lead with it for teams who want the full opinionated shape from day one.

---

## What changes shape, what doesn't

### Doesn't change

- `.agents/` remains the canonical source of truth for commands, skills, CLAUDE.md stub, board references.
- `tools/gather.py` continues to mirror `.agents/` → `.claude/` + `.github/` for the template path.
- The seed/spread/standardise organisation of commands. Phase frontmatter stays.
- The proposal-first culture. Drafts land under `proposals/` before going to final locations.

### Does change

- **`/setup-awow` becomes a scaffolder, not just a configurator.** When invoked from the plugin (i.e. when there is no `.agents/CLAUDE.md` and no `setup-progress.md` in the adopter's CWD), Step 0 changes: instead of running `setup/install.sh` against an awow-shaped repo, it *creates the awow shape* in the adopter's CWD. The current Step 0 (installer) only fires when the structural files already exist.
- **Templates move to a shipped resource.** `.agents/CLAUDE.md` stub, the `context/` skeleton, `proposals/setup/` placeholder structure, `setup-progress.md` initial content, and the `context/tooling/boards/<tool>/reference/` docs become files the plugin ships under a `templates/` directory. The commands read from `${CLAUDE_PLUGIN_ROOT}/templates/...` and write into the adopter's CWD.
- **A new build step.** A `tools/build-plugin.py` (or extension to `gather.py`) packages `.agents/` + selected `context/` slices + `templates/` into the plugin's manifest shape. The maintainer runs this before publishing; CI checks for drift.
- **Identity check at command entry.** Every command that has filesystem expectations adds a one-shot "am I running from a plugin against an unscaffolded repo, from a plugin against a scaffolded repo, or from a template clone?" branch at the top. Three modes, one prompt body, branching only where it matters.

---

## Plugin layout (proposed)

The plugin is a single directory the maintainer publishes. Structure:

```
awow-plugin/
├── .claude-plugin/
│   └── plugin.json              # manifest: name, description, version
├── commands/
│   ├── setup-awow.md            # the scaffold-or-configure wizard
│   ├── awow-add.md
│   ├── awow-status.md
│   ├── awow-reset.md
│   ├── refinement-prep.md       # seed
│   ├── process-workitem.md      # seed
│   ├── process-transcript.md    # seed
│   ├── board-skill.md           # spread
│   ├── coaching-review.md       # spread
│   ├── solution-design-flow.md  # spread
│   ├── cross-team-view.md       # standardise
│   ├── daily-digest.md          # standardise
│   └── weekly-digest.md         # standardise
├── skills/
│   ├── agent-directive-voice.md
│   ├── user-story-template.md
│   ├── mlflow-export/
│   ├── prompt-skill-analysis/
│   └── awow-usage-coach/
└── templates/
    ├── CLAUDE.md.stub           # → .agents/CLAUDE.md or .claude/CLAUDE.md
    ├── setup-progress.md.stub
    ├── context/                 # skeleton — every file the wizard later fills
    │   ├── team/…
    │   ├── company/…
    │   ├── knowledge-base/…
    │   └── tooling/
    │       └── boards/
    │           ├── linear/reference/…
    │           ├── jira/reference/…
    │           ├── azure-devops/reference/…
    │           └── github-issues/reference/…
    └── proposals/
        └── setup/.gitkeep
```

**Decision: include spread/standardise commands at install time.** Per the question above. Phase frontmatter on each command keeps `/awow-add` and `/awow-status` honest — invoking a spread command before Seed has shipped still triggers the soft warning from `awow-add`'s prerequisites read. The plugin ships them all; `/awow-add` decides which are *opted-in* (a state managed by `setup-progress.md` or a sibling file).

**Operational skills (`mlflow-export`, etc.) ship as-is.** They're opinionated about tracing backend and harness format. Step 9 of `/setup-awow` (Skills review) walks the user through keep / customise / drop. Customised versions land in the adopter's own `.agents/skills/` or equivalent and *shadow* the plugin's copy. Open question: does Claude Code's plugin loader support per-repo skill overrides cleanly? See **Risks** below.

---

## The big shift: `/setup-awow` as scaffolder

Current Step 0 detects `.venv/` + `.claude/commands/setup-awow.md` and either skips, restores the venv, or runs the full installer. From the plugin, none of that applies — the plugin's commands are already loaded by virtue of the plugin being installed, and `uv` / `gather.py` are template-clone machinery the adopter doesn't need.

The new Step 0, when running from a plugin, is **Scaffold**:

1. **Detect mode.** Probe `.agents/CLAUDE.md` and `setup-progress.md` in CWD.
   - **Both present** → "scaffolded repo, configurator mode" (current Step 0 logic, minus the installer pieces).
   - **Both absent** → "unscaffolded repo, scaffolder mode" (this section).
   - **One present** → refuse and ask the user what happened (partial scaffold is suspicious; better to stop than to overwrite their `.agents/CLAUDE.md` with the stub).
2. **Show the destination.** Print the tree the wizard is about to create under CWD. The user sees:
   ```
   ./
   ├── .agents/
   │   └── CLAUDE.md            (stub — Step 5 will regenerate)
   ├── context/
   │   ├── team/                (empty — Steps 2–4 fill)
   │   ├── company/             (empty — Step 7 fills)
   │   ├── knowledge-base/      (empty — Step 6 fills)
   │   └── tooling/             (empty — Step 1 fills board.md)
   ├── proposals/
   │   └── setup/               (empty — wizard drafts here first)
   └── setup-progress.md         (Step-0 complete only)
   ```
3. **Ask for confirmation.** "These paths don't exist yet in `<cwd>`. May I create them? Existing files at any of these paths will not be touched." Refuse to proceed without explicit yes.
4. **Copy.** For each `templates/<path>` in the plugin, write to `<cwd>/<path>` *if and only if* the target does not exist. Never overwrite.
5. **Record what was scaffolded.** Write to `setup-progress.md` the list of paths created, so a later `/awow-reset` knows what to unwind cleanly.
6. **Skip the installer.** No `.venv/`, no `uv sync`, no `gather.py`. The plugin's commands are already loaded.
7. **Continue to Step 1.** Phase 1a starts as today: detect harness (Claude Code), ask the user about board surface.

The scaffolder branch adds maybe 40 lines to `.agents/commands/setup-awow.md`. The configurator branch (current Step 0 and everything after) stays largely intact.

**Reference docs.** `context/tooling/boards/<tool>/reference/` is the most non-trivial scaffold. It's about 8 files per tool × 4 tools = 32 files. The plugin ships them all under `templates/context/tooling/boards/`. Step 0's scaffolder copies the *whole* `boards/` tree so the adopter can inspect every tool's reference; Step 1 then walks just the matching tool's reference. This costs ~80KB of markdown on disk in the adopter's repo. Worth it — the references are the meat of Step 1's value, and they should live alongside `context/tooling/board.md` in the adopter's repo for grep-ability anyway.

---

## What "the corresponding prompts" looks like

The plugin's `commands/` set covers four roles around `/setup-awow`:

| Role | Commands | Notes |
|---|---|---|
| **Bootstrap** | `setup-awow`, `awow-status` | Scaffold-or-configure; report where the team is in adoption |
| **Lifecycle** | `awow-add`, `awow-reset` | Promote opt-in commands; tear down scaffolded state for re-run |
| **Seed cycle** | `refinement-prep`, `process-workitem`, `process-transcript` | What the adopter runs on day two; the value demo |
| **Phase 3/4** | `board-skill`, `coaching-review`, `solution-design-flow`, `cross-team-view`, `daily-digest`, `weekly-digest` | Surface via `/awow-add`; not active until opted in |

The commands talk to each other through the same state file (`setup-progress.md`) and the same convention files in `context/`. Nothing in the plugin's interaction model is new — it's the same Phase 2/3/4 ladder that's in `.agents/commands/README.md`, just shipped via a different distribution channel.

**One thing the plugin adds that the template doesn't.** When the plugin scaffolds, it has the *chance* to ask "do you want me to keep this repo's existing CLAUDE.md and have awow's stub additions go into `.claude/CLAUDE.md.local` instead?" — i.e. **non-destructive scaffold into an existing-codebase repo**. The template clone always starts from `.agents/CLAUDE.md` as the canonical file; an adopter scaffolding into a working repo may already have a CLAUDE.md they care about. The wizard needs to be polite about this. Detail to be specced in a follow-up; flagged here as a real concern.

---

## Build pipeline

The plugin is built from `.agents/` plus a curated slice of `context/`. The maintainer never hand-edits the plugin directory. Proposed:

```
tools/build-plugin.py [--out awow-plugin/]
```

Steps:

1. Read `.agents/commands/{setup-awow,awow-add,awow-status,awow-reset}.md` plus `.agents/commands/{seed,spread,standardise}/*.md`. Copy to `awow-plugin/commands/`.
2. Read `.agents/skills/`. Copy all (declarative + operational) to `awow-plugin/skills/`. Preserve `scripts/` subdirs.
3. Read `.agents/CLAUDE.md` stub. Copy to `awow-plugin/templates/CLAUDE.md.stub`.
4. Read `context/tooling/boards/`. Copy the per-tool `reference/` subdirs to `awow-plugin/templates/context/tooling/boards/<tool>/reference/`.
5. Read `proposals/setup/`. Copy structure (not content) to `awow-plugin/templates/proposals/setup/`.
6. Generate `awow-plugin/.claude-plugin/plugin.json` with version pulled from `pyproject.toml` or a `VERSION` file.

Run in CI with `--check` to verify the published plugin tracks `.agents/`. Same drift-detection pattern as `gather.py --check`.

The output of `build-plugin.py` is what the maintainer publishes — either to a Git repo (for `/plugin install <url>`), to a marketplace, or as a local directory for dogfooding.

---

## Dogfood loop

The maintainer can run the plugin against itself for end-to-end testing:

```bash
# In the awow repo (this one):
uv run python tools/build-plugin.py --out /tmp/awow-plugin
# Then in a separate empty directory, install local:
claude code  # or via /plugin install /tmp/awow-plugin
> /setup-awow
```

The `tests/setup-awow/` regression suite (per `proposals/setup-awow-regression-tests.md`) extends naturally: add scenarios for "plugin scaffold into empty dir" and "plugin scaffold into dir with existing CLAUDE.md". Rubrics get new invariants for the scaffold step (e.g. "did the wizard print the file tree before creating files?", "did it refuse on partial-scaffold state?").

---

## Coexistence with the template path

Both paths produce the same shape in the adopter's repo:

| Surface | Template clone | Plugin install |
|---|---|---|
| `.agents/CLAUDE.md` | Already there, run `tools/bootstrap-claude-md.py` in Step 5 | Scaffolded in Step 0, run regeneration logic in Step 5 |
| Commands | In `.agents/commands/` + mirrored to `.claude/commands/` by gather | Loaded directly from plugin install dir |
| Skills | In `.agents/skills/` + mirrored to `.claude/skills/` by gather | Loaded directly from plugin install dir |
| Board references | In `context/tooling/boards/` | Scaffolded in Step 0 from `${CLAUDE_PLUGIN_ROOT}/templates/` |
| Wizard state | `setup-progress.md` at CWD | `setup-progress.md` at CWD |
| Proposals | `proposals/` at CWD | `proposals/` at CWD |
| Team context | `context/team/`, populated by wizard | `context/team/`, populated by wizard |

A team can switch from plugin to template (or vice versa) without losing state: the configurator branch of `/setup-awow` only checks for `.agents/CLAUDE.md` + `setup-progress.md`; it doesn't care how they got there.

**What the template path keeps as exclusive value.** Copilot support (no plugin equivalent), full repo-shaped reference (every file the wizard *would* touch is visible up front), and the maintainer's own `dogfood/` walkthrough. The plugin gets a faster on-ramp; the template gets completeness.

---

## Risks

1. **Skill override resolution.** If the adopter customises `mlflow-export` in their repo (Step 9), Claude Code needs to load *their* copy not the plugin's. Behaviour to confirm before committing: does the plugin loader respect per-repo `.claude/skills/<name>/` over `${CLAUDE_PLUGIN_ROOT}/skills/<name>/`? If not, the customise branch of Step 9 needs to instruct the user to `git rm` the plugin-shipped one and that's brittle. **Action: verify with a one-off spike before locking the design.**
2. **Existing-codebase pollution.** Scaffolding `.agents/`, `context/`, `proposals/`, `setup-progress.md` into a repo that already has a working dev loop is intrusive. The "show the tree, ask for confirmation, never overwrite" rule mitigates but doesn't eliminate. We should also offer a `/setup-awow --dry-run` that prints the tree without writing. (Note: dry-run aligns with the current branch name `feature/dry_run_awow`, which may be the right place to land this.)
3. **Plugin loader does not see scaffolded files.** A plugin's commands resolve at session start. If `/setup-awow` creates `.agents/CLAUDE.md` mid-session, does the harness pick it up on the next turn, or only on session restart? **Action: verify.** If restart is required, Step 0 should tell the user to `/restart` (or its equivalent) after scaffold completes.
4. **Drift between plugin-shipped templates and starter-pack reality.** If the plugin's `templates/context/tooling/boards/linear/reference/states.md` drifts from `.agents/`-canonical (because someone edited one not the other), the plugin's adopters get stale references. The `build-plugin.py --check` step is the defence; CI must run it.
5. **`/awow-reset` semantics.** Today, reset wipes adopter-produced state in the *template clone*. From a plugin install, reset has to know which paths were scaffolded (recorded in step 5 of the new Step 0) and tear those down too. Otherwise the adopter can never get back to "clean plugin-fresh" without manually deleting. **Action: extend `awow-reset.md` with a "scaffolded paths" branch.**

---

## Open questions for the user

1. **Versioning.** Lockstep with the template repo (one version number, every plugin release matches a template tag), or independent (plugin can iterate without template churn)? Lockstep is simpler; independent is more flexible. Recommendation: lockstep until there's a concrete reason to split.
2. **Marketplace listing.** Public marketplace from day one, or private/local-only for the first few adopters? Public lowers friction but locks the interface earlier. Recommendation: private (Git URL) for the first three adopters, then public.
3. **`/setup-awow --quickstart` behaviour from the plugin.** Today the quickstart bundles Steps 0 → 1 → 2 → 3 → 5 in one turn. From a plugin, Step 0 is the scaffold. Should quickstart also bundle the scaffold without per-file confirmation? Faster but riskier. Recommendation: keep the per-file confirmation gate even in quickstart; it's the *only* destructive-ish action in the wizard.

---

## Suggested next move

Land this proposal (move to `proposals/setup/` or accept as-is), file the corresponding board issue (`Implement awow as a Claude Code plugin`, type:feature, area:packaging), then spike the two risks marked **Action: verify** before sinking work into `tools/build-plugin.py`. Spike output: a one-page note appended to this proposal under `## Spike findings`.
