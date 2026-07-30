# Proposal — Context resolution: which installation, which board

**Status:** Draft — awaiting review.
**Scope:** define how any awow command — whether loaded from a template clone or a globally-installed plugin — resolves the context it operates against, when CWD no longer uniquely determines one `context/tooling/board.md`. Covers two real shapes and their composition: multiple boards inside one repo, and multiple repos — siblings under one working root, possibly nested — each with their own board.
**Related:** `proposals/plugin-distribution.md` (the "identity check at command entry" this composes with).

---

## Why

Today every command reads `context/tooling/board.md` relative to the repo it runs in. The assumption baked in everywhere is **one repo → one board → one context tree**. Two observed shapes break it:

1. **Two boards, one repo.** One team runs two workstreams (say a product board and an infra board) from a shared repo — shared conventions, shared knowledge base, two board pointers. The current data model has no place for the second board. A monorepo hosting two teams — each subtree with its own full context tree — is the same problem one level up.
2. **Several repos, one working root.** The observed shape is sibling repos under a common parent — `/root/board_1_awow` and `/root/board_2_awow`, each with its own board — with sessions sometimes launched from `/root` itself, above every repo. Nesting is the rarer variant of the same problem (a scaffolded repo checked out inside another). And the shapes compose: one of those siblings can itself be a two-board repo (shape 1 inside shape 2), so the user is realistically driving three boards from two teams' points of view. A globally-installed plugin makes its commands available in *every* one of these directories, so "which board wins where" needs a stated rule rather than luck.

The failure mode that matters is not a crash — it is a **silent wrong-board write**: a work item landing on a board the user (or their client) never intended. Every rule below is shaped to make that impossible or at least loudly visible.

## Two concepts, two rules

A command answers two questions at entry, in order:

- **Which installation?** An *installation root* is a directory containing `context/tooling/board.md` (alongside the usual `context/` tree and `setup-progress.md`). Today that is implicitly the repo root; this proposal makes it explicit and allows a repo to contain several (two-teams monorepo) or none (unscaffolded repo visited with the plugin installed).
- **Which board?** Within one installation, `board.md` declares one board (today's file, byte-for-byte unchanged) or several (index form, below).

**Compatibility invariant:** a single-board repo with `board.md` at the repo root sees zero behavior change from this proposal.

## Discovery rule — which installation

Walk upward from CWD, directory by directory, stopping hard at the first `.git` root:

1. The **nearest** directory on that path containing `context/tooling/board.md` is the installation root. A scaffolded repo nested inside another scaffolded repo → the inner one wins, always.
2. The walk **never crosses the repo boundary**. An unscaffolded inner repo under a scaffolded outer repo resolves to: "this repo has no awow context; run `/setup-awow` here or cd to the repo that has one." The outer installation's board is never named and never used — inheriting it across a repo boundary is exactly the silent wrong-board write this proposal exists to prevent, and the outer context is invisible to any teammate who clones only the inner repo.
3. **Downward probe, monorepo edge.** If the upward walk finds nothing and CWD is inside a git repo, probe shallowly downward for `*/context/tooling/board.md` (up to three directory levels, git-tracked files only). Exactly one hit → use it, stating which in one line. Several hits → selection picker. None → unscaffolded, as in rule 2.
4. **Workspace root, outside any repo.** When CWD is not inside a git repo at all (the `/root` above sibling repos), enumerate the immediate child directories that are git repos containing an installation. Exactly one → use it, stating which in one line. Several → resolve with the same ladder used for boards below: explicit reference in the prompt, then path evidence (the files the work names), then the session pin, then a picker. The chosen installation supplies *all* context for the invocation — sibling repos' boards and conventions are never mixed in, so the repo-boundary invariant of rule 2 survives the workspace view.

## Board ladder — which board

Resolution is two-stage with one ladder shape: when several installations are reachable (discovery rule 4), the ladder first picks the installation, then runs again to pick the board within it. Pins are kept per stage (an installation pin and a board pin), and an explicit reference resolves the current invocation only — it never silently re-pins the session.

If `board.md` is the single-board form: done, no new behavior. If it is the index form, resolve top-down; the first rung that produces exactly one board wins:

1. **Explicit reference** in the user's prompt — a ticket id whose prefix belongs to one board ("work on PLAT-7"; prefixes and workspace identifiers live in each `board-<name>.md`), or the board named outright ("on the infra board").
2. **Scope match** — each index entry declares scope globs; match against CWD and the files the work touches. Zero or overlapping matches → ambiguous, fall through.
3. **Session pin** — the answer the user gave a picker earlier in this conversation.
4. **Picker** — one selection question, "Which board is this for?". The answer becomes the session pin.

Two deliberate properties:

- **The pin is conversational state, not a file.** Nothing is written to disk, so nothing can be committed or go stale. It evaporates with the session; worst case is one redundant question next session. A persisted pin's failure mode is a stale silent wrong-board write — the worse trade in every case.
- **Silent resolution is announced.** Whenever rung 1 or 2 resolves without asking, the command states `targeting board: <name>` in one line before its first board write. No confirmation gate — just visibility, so a wrong inference is catchable before it matters.

**No `default:` field.** A default board silently swallows scope-miss cases and lands workstream-B items on board A. The picker-once-per-session cost is acceptable; determinism failures should be visible, not papered over.

## File format — `board.md` index form

Adding a second board converts `context/tooling/board.md` into a short index; the full per-board specs move to sibling files that keep exactly today's single-board shape:

```
context/tooling/
├─ board.md            index when N>1, full spec when N=1
├─ board-product.md    full spec (today's board.md shape)
├─ board-infra.md      full spec
└─ boards/             wizard reference material — unchanged
```

The index form:

```markdown
# Board tooling — index

This repo runs two boards. Resolution rules: AGENTS.md §Context resolution.

## Boards

- **product** — scope: `packages/app/**` — customer-facing backlog → [board-product.md](board-product.md)
- **infra** — scope: `infra/**` — platform/tooling backlog → [board-infra.md](board-infra.md)
```

An index entry whose `board-<name>.md` is missing is a **hard error naming the file** — never a fallback to another board. The per-tool wizard references under `context/tooling/boards/` are untouched; no naming collision.

## Where the instructions live

- The `AGENTS.md` stub gains a `## Context resolution` section carrying the discovery rule and the board ladder verbatim. It ships to every adopter through both distribution paths (template clone; plugin scaffold), and the `tools/bootstrap-claude-md.py` template carries it through regeneration.
- Every board-touching command opens with a two-line entry rule: *"Resolve the installation root and active board per §Context resolution in AGENTS.md before any board read or write."* One place to evolve the rules; the commands stay short.
- The unscaffolded outcome composes with the plugin proposal's "identity check at command entry": discovery finding nothing *is* that check's "plugin against unscaffolded repo" branch.

## Out of scope

- Cross-repo inheritance and workspace-level boards living outside any repo (a `~/clients/acme/` umbrella governing repos beneath it) — breaks the "context is committed where teammates see it" invariant.
- Per-user board configuration outside the repo.
- Pin-state files, in any form.
- A cross-installation aggregation lens ("everything I must act on across all three boards"). Resolution always targets one installation per invocation; an aggregate view over several installations is a separate follow-up, not a resolution concern.
- A guided flow for converting single-board `board.md` into index form. For now that conversion is a documented manual edit; a `/awow-add board` flow is a named follow-up, not specced here.

## Testing

Three new fixture shapes for the regression suite:

1. **Nested repo** — outer scaffolded, inner not. Rubrics: command declares the inner repo unscaffolded; the outer board is never mentioned in the transcript.
2. **Monorepo, two context trees.** Rubrics: from a subtree CWD the correct root resolves silently; from the repo root the downward probe finds both and a picker appears.
3. **Index-form `board.md`.** Rubrics: scope match resolves silently and emits the `targeting board:` one-liner; the picker fires at most once per session; a missing `board-<name>.md` produces the hard error; existing single-board fixtures pass unchanged.
4. **Workspace root over sibling repos.** A parent directory holding a single-board repo and a two-board repo (three boards total, two "teams"). Rubrics: from the parent, the installation picker lists both repos; an explicit ticket reference resolves the right installation *and* board in one step without re-pinning; the resolved installation's output never cites the sibling's context.

## Suggested next move

Review this proposal, then: add the `## Context resolution` section to the AGENTS.md stub and bootstrap template, add the two-line entry rule to the board-touching commands, and extend the regression suite with the three fixture shapes. The plugin proposal's identity-check spike should exercise the nested-repo case explicitly.
