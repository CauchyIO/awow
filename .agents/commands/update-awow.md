---
phase: meta
prerequisites: ["Step 0 of /setup-awow complete (tools/awow.lock.json exists)"]
removes_pain: "the how-do-I-pull-in-newer-awow-versions-without-clobbering-my-config problem"
---

# /update-awow — pull newer awow into an already-set-up repo

Bring the starter-owned files (commands, skills, tooling, reference context) up
to a newer awow version, **without touching anything the team owns**. Backed by
`tools/awow_lock.py`, which does a 3-way compare — baseline (what you last
reconciled against) vs. your local file vs. upstream — so a file you edited is
never silently overwritten and only genuine both-sides changes surface as
conflicts.

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
   refresh it first so the bundle is current:
   - Claude Code: `/plugin update awow`
   - Copilot CLI: `copilot plugin update awow`

   Then use the refreshed plugin clone as the source (its root is
   `$CLAUDE_PLUGIN_ROOT` when this command is plugin-provided).
2. **A fresh upstream checkout.** Otherwise ask the user to point at one, or to
   clone/pull it: `git clone <awow-upstream> /tmp/awow-upstream` (or
   `git -C <existing-clone> pull`). Pass its path as `--source`.

If neither is available, run the offline check (below) and stop — you cannot
apply an update without a source to compare against.

## Steps

1. **Confirm the baseline exists.** If `tools/awow.lock.json` is missing, this
   repo predates the lockfile. Run `python tools/awow_lock.py backfill` once to
   seed it from the current tree (this establishes "you are here" — it does not
   change any files), then continue.
2. **Show the plan (read-only, proposal-first).** Run:
   ```
   python tools/awow_lock.py status --source <path>
   ```
   Relay the version delta and the grouped verdicts to the user:
   - **update** — upstream changed, you didn't → will be overwritten.
   - **new** — a file upstream added → will be created.
   - **conflict** — both changed → upstream saved as `<file>.awow`; **your file
     is left untouched** for you to merge.
   - **keep-local / removed-local / unchanged** — no action.
   Nothing has been written yet. If invoked with `--check`, stop here.
3. **Get explicit approval.** Do not apply until the user confirms. This is the
   proposal-first gate (`input/PROPOSAL.md` §3).
4. **Apply.** Run:
   ```
   python tools/awow_lock.py apply --source <path>
   ```
   It overwrites `update`/`new` files, writes `.awow` sidecars for conflicts,
   leaves your edits alone, and rewrites `tools/awow.lock.json` to the new
   reconciled baseline + version.
5. **Re-mirror the harness stubs.** The command surfaces changed, so regenerate
   the pointer stubs:
   ```
   python tools/gather.py        # Windows: same command, tools/gather.py
   ```
6. **Report.** Summarise: version moved from → to, N updated, M added, and list
   every `<file>.awow` the user still needs to merge (then delete the `.awow`).
   If any conflicts landed, remind them the update is not "done" until each
   `.awow` is merged.

## Offline check (no source)

If there is no source to compare against, `python tools/awow_lock.py status`
still reports the recorded version and which starter files the team has locally
modified (baseline vs. local). It cannot say whether a newer awow exists — that
needs a source. Surface this honestly rather than implying the repo is current.

## Anti-patterns

- **Do not apply without showing the plan and getting approval.** Updates
  overwrite files; the user decides.
- **Do not hand-edit `tools/awow.lock.json`.** It is the reconciliation record;
  `backfill`/`apply` own it.
- **Do not touch team-owned paths to "resolve" a conflict.** A conflict lives in
  a starter-owned file; the `.awow` sidecar is the merge surface. Leave
  `context/team/`, `setup-progress.md`, and `proposals/` alone.
- **Do not skip `gather.py`.** Without it the harness still points at the old
  command/skill metadata.
