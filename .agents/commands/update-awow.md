---
phase: meta
prerequisites: ["Step 0 of /setup-awow complete"]
removes_pain: "the how-do-I-pull-in-newer-awow-versions-without-clobbering-my-config problem"
channel: vendored
---

# /update-awow — pull newer awow into an already-set-up repo

Bring the starter-owned files (commands, skills, tooling, reference context) up
to a newer awow version, **without touching anything the team owns**. Backed by
`tools/awow_lock.py`, which does a 3-way compare — baseline (what you last
reconciled against) vs. your local file vs. upstream — so a file the team edited
is never silently overwritten and only genuine both-sides changes surface as
conflicts.

The user's job is two actions: invoke this command, approve (or reject) the
plan. Everything else — bootstrapping the tool, seeding the lockfile, applying,
re-mirroring — is yours. Do not hand the user setup chores the command can do
itself.

This is the counterpart to `/setup-awow`: setup configures the repo the first
time; update keeps the scaffolding current afterward. It never re-runs the
wizard and never rewrites `context/team/`, `context/company/`, `board.md`,
`setup-progress.md`, or a bootstrapped `AGENTS.md`.

## Inputs

- `--source <path>` (optional) — an upstream awow checkout to update *from*.
- `--check` (optional) — report drift and available updates, then stop. No writes.

## Resolve the source

`awow_lock.py` needs a clean, newer awow tree to compare against. In order:

1. **Installed plugin.** If the awow plugin is installed, tell the user to
   refresh it first (`/plugin update awow`; Copilot CLI:
   `copilot plugin update awow`), then use the refreshed plugin clone as the
   source (its root is `$CLAUDE_PLUGIN_ROOT` when this command is
   plugin-provided).
2. **`--source <path>`.** Use the given checkout. If it is a git clone, run
   `git -C <path> pull` first so you compare against current upstream, and
   confirm it is clean (`git -C <path> status --porcelain` empty) — a dirty or
   mid-branch source produces a garbage plan.
3. **Neither available.** Run the offline check (below) and stop — you cannot
   apply an update without a source.

## Steps

1. **Self-bootstrap — never ask the user to do this.** If `tools/awow_lock.py`
   is missing locally (the repo predates the update machinery), copy it from
   `<source>/tools/awow_lock.py` yourself. If `tools/awow.lock.json` is missing,
   seed it — the mode matters, because a repo that customized starter files
   before the lockfile existed must not baseline those edits as pristine:
   - **Fresh install, nothing customized yet:** `python tools/awow_lock.py
     backfill` hashes the working tree — correct only when local still equals
     the vendored upstream.
   - **The vendor commit is findable** (search the repo's history for the
     commit that introduced the awow starter files, e.g. `git log --oneline
     --diff-filter=A -- .agents/AGENTS.md`): run `python tools/awow_lock.py
     backfill --baseline-ref <commit>`. The baseline is the tree as vendored,
     so every later team edit correctly classifies as keep-local or conflict.
   - **Vendor commit not findable:** run `python tools/awow_lock.py backfill
     --source <path>`. Each local file is matched against upstream's full
     history — a match means pristine, no match means team-edited and
     protected. One blind spot: a starter file the team deliberately deleted
     is indistinguishable from one never vendored and returns as `new`;
     re-delete it after apply.
   Backfill only writes the lockfile — no other file changes. Report which
   mode you used and why in one line.
2. **Show the plan (read-only, proposal-first).** Run:
   ```
   python tools/awow_lock.py status --source <path>
   ```
   Relay the version delta and the grouped verdicts to the user:
   - **update** — upstream changed, you didn't → will be overwritten.
   - **new** — a file upstream added → will be created.
   - **conflict** — both changed → upstream saved as `<file>.awow`; **your file
     is left untouched** for you to merge.
   - **keep-local / removed-local / removed-upstream / unchanged** — no action.

   **First-run caution:** when step 1 just seeded the lockfile from the
   working tree (plain `backfill` on a repo that was not actually pristine),
   the compare cannot distinguish "the team edited this" from "upstream moved"
   — every locally-diverged starter file classifies as `update`. Prefer the
   retrofit modes in step 1; if you had to seed from the working tree anyway,
   walk the `update` list against the team's known customisations and call out
   high-risk entries yourself (`pyproject.toml` in a repo with its own Python
   project; anything under `context/` the team filled in) rather than letting
   the user discover the clobber in review.

   Nothing has been written yet. If invoked with `--check`, stop here.
3. **Get explicit approval.** Do not apply until the user confirms. This is the
   proposal-first gate (`input/PROPOSAL.md` §3).
4. **Apply and re-mirror.** Run:
   ```
   python tools/awow_lock.py apply --source <path>
   python tools/gather.py
   ```
   Apply overwrites `update`/`new` files, writes `.awow` sidecars for conflicts,
   leaves team edits alone, and rewrites `tools/awow.lock.json` to the new
   reconciled baseline + version. Gather re-mirrors the harness stubs — never
   skip it; without it the harness still points at old command metadata.
5. **Report.** Summarise: version moved from → to, N updated, M added, and list
   every `<file>.awow` the user still needs to merge (then delete the `.awow`).
   If any conflicts landed, remind them the update is not "done" until each
   `.awow` is merged. Recommend reviewing the whole update as one `git diff` on
   a branch — git is the backstop for anything step 2's caution missed.

   **Call out `removed-upstream` explicitly.** Files upstream has dropped are
   left in place by design — `apply` never deletes. As of 0.6.0 that covers
   `.agents/commands/daily-routine.md`, `weekly-digest.md`, and
   `cross-team-view.md`: `/daily-routine` and `/weekly-digest` merged into
   `/daily-digest` (the weekly view is now `/daily-digest --week`), and
   `/cross-team-view` was never built. Name each one, say it is now unmaintained,
   and offer to delete it and re-run `python tools/gather.py`. Silence here
   leaves a team invoking a command upstream no longer supports.

## Offline check (no source)

If there is no source to compare against, `python tools/awow_lock.py status`
still reports the recorded version and which starter files the team has locally
modified (baseline vs. local). It cannot say whether a newer awow exists — that
needs a source. Surface this honestly rather than implying the repo is current.

## Anti-patterns

- **Do not apply without showing the plan and getting approval.** Updates
  overwrite files; the user decides.
- **Do not bounce setup chores to the user.** Missing tool, missing lockfile,
  stale source clone — you fix those in step 1 and the source resolution, and
  report what you did. The user invokes and approves; that is the whole flow.
- **Do not hand-edit `tools/awow.lock.json`.** It is the reconciliation record;
  `backfill`/`apply` own it.
- **Do not touch team-owned paths to "resolve" a conflict.** A conflict lives in
  a starter-owned file; the `.awow` sidecar is the merge surface. Leave
  `context/team/`, `setup-progress.md`, and `proposals/` alone.
- **Do not skip `gather.py`.** Without it the harness still points at the old
  command/skill metadata.
