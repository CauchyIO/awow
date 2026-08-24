# Updating awow

Pull newer awow into a repo that is already set up — without losing anything your team owns.

> **TL;DR** — `/setup-awow` configures a repo once; `/update-awow` keeps the scaffolding current
> afterwards. Your two actions are invoke and approve; `tools/awow_lock.py` does the rest against
> a lockfile recording what you last reconciled, so only starter-owned paths move, your edits
> survive, and conflicts land as sidecars you merge by hand.

## How the update decides what to touch

The lockfile — `tools/awow.lock.json` — records a hash of every starter-owned file as you last
reconciled it. Each update compares three versions of each file:

```mermaid
flowchart LR
  baseline[Lockfile baseline] --> compare{3-way compare}
  local[Local copy] --> compare
  upstream[Upstream] --> compare
  compare -->|only upstream changed| apply[update / new]
  compare -->|only you changed| keep[keep-local]
  compare -->|both changed| sidecar[".awow conflict sidecar"]
```

| Verdict | Meaning | What happens |
| --- | --- | --- |
| **update** | Upstream changed; you didn't | Overwritten with the new version |
| **new** | Upstream added a file | Created |
| **keep-local** | You edited; upstream didn't | Left alone — your edit wins |
| **conflict** | Both changed | Your file untouched; upstream saved beside it as `<file>.awow` to merge |
| **removed-local** | You deleted it | Not re-added |
| **removed-upstream** | Upstream deleted it | Your copy left alone (delete by hand if you want to follow) |

Only **starter-owned paths** are managed: `.agents/`, `tools/`, `setup/`, `context/` reference
material, `mcps/`, `pyproject.toml`, `SETUP.md`, `REFERENCES.md`. Team-owned content —
`context/team/`, `context/company/`, `board.md`, `setup-progress.md`, a bootstrapped
`AGENTS.md`, everything under `proposals/` — is never rewritten by an update.

## The human flow — two actions

With the awow plugin installed:

```bash
/plugin update awow     # refresh the bundle (Copilot CLI: copilot plugin update awow)
/update-awow            # agent shows the plan; you approve or reject
```

Without the plugin, point at a checkout: `/update-awow --source ../awow`. The agent pulls the
source current, verifies it is clean, and takes it from there. Either way it presents a grouped
plan — what updates, what is new, what conflicts — and **writes nothing until you approve**.
After apply it re-mirrors the harness stubs (`tools/gather.py`) and reports the version delta
plus any `.awow` conflict files left to merge.

Run it on a branch and read the `git diff` as your final review; git is the backstop. Add
`--check` to see the plan and stop — "how far behind are we?" without touching anything.

## First run in an older repo

A repo set up before the update machinery existed has no lockfile and no `tools/awow_lock.py`.
You prepare nothing: the agent self-bootstraps — copies the tool from the source, then seeds the
lockfile from your current tree (`backfill`, which establishes "you are here" and changes no
other file).

**The one first-run caveat.** A freshly seeded baseline equals your local state, so the first
compare cannot distinguish "we edited this" from "upstream moved" — files your team deliberately
changed show up as *update (will overwrite)* instead of *conflict*. The agent is instructed to
walk that list against your known customisations and flag high-risk entries (a real product
`pyproject.toml`, reference `context/` you filled in) before you approve. From the second update
on, the lockfile holds a true reconciliation point and your edits classify as *keep-local*.

## Merging a conflict

The upstream version lands next to your untouched file as `<file>.awow`; you diff the two, take
what you want, and delete the sidecar. The update is not done until every `.awow` is gone — the
report lists them so none are forgotten.

```bash
diff .agents/commands/daily-digest.md .agents/commands/daily-digest.md.awow
# merge what you want, then:
rm .agents/commands/daily-digest.md.awow
```

## What the version numbers mean

| Where | What it is |
| --- | --- |
| `.claude-plugin/plugin.json` → `version` | The canonical awow version. Bumped when starter-owned files change; the plugin marketplace serves it and `status` reports it as the "to" side. |
| `tools/awow.lock.json` → `awow_version` | The version *your repo* last reconciled against — the "from" side of every plan. |
| Git tags (`v0.4.0`, …) | Pinnable release points on the awow repo, created by the release workflow when a version bump lands on `main`. Pass a tag checkout as `--source` to update to a specific version instead of whatever `main` is. |
| `CHANGELOG.md` | What each release changed, newest first — the section for a version is also the body of its GitHub release. |

Correctness never depends on the numbers — the compare is content-hash based — but a plan reading
`0.3.0 → 0.4.0` tells you you're taking a real release. Maintainers: bump the version in the same
change that alters starter files and add that version's section to `CHANGELOG.md`
(`python tools/release-notes.py --changelog CHANGELOG.md` drafts it from the merged PRs since the
previous release; trim it in the PR). When the bump lands on `main`, the release workflow opens
the awow-dist publish PR, tags the commit, and publishes the GitHub release with that section as
its body — there is no tag to push by hand.

## Sources of truth

- [`.agents/commands/update-awow.md`](../.agents/commands/update-awow.md) — the flow and its approval gate
- [`tools/awow_lock.py`](../tools/awow_lock.py) — the 3-way compare and lockfile format
- [`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json) — the canonical version
- Companion guides: [setup & the plugin model](guide-setup-and-two-harnesses.md) — the wizard that installed what this updates
