# Updating awow

How a repo takes newer awow — and how a legacy vendored repo becomes one that can.

> **TL;DR** — With the plugin installed, updating is the harness's own gesture:
> `/plugin update awow` (Copilot CLI: `copilot plugin update awow`). Nothing lives in your repo
> to reconcile — the payload is replaced wholesale and your `context/` is never part of it. A
> repo that still carries vendored starter files runs `/migrate-to-plugin` once; after that,
> updates are plugin updates forever.

## The plugin model: update is not a merge

The payload (commands, skills, handlers, runtime tools, reference context) is served from the
plugin install, not copied into your repo. Team-owned content — `context/team/`,
`context/company/`, `board.md`, `setup-progress.md`, `proposals/` — lives only in your repo, so
a plugin update cannot touch it. There is no lockfile, no 3-way compare, no conflict sidecar:
those existed to merge upstream into vendored copies, and there are no vendored copies left to
merge into.

The one seam: a command or skill body you deliberately keep as a repo-local file (the parity
seam `/migrate-to-plugin` flags) shadows the plugin's copy and stops receiving updates. Fold it
back upstream when your change lands, or re-diff it against the payload after big releases.

## Legacy vendored repos: migrate once

A repo set up before plugin-first distribution still carries `.agents/`, vendored `tools/`, and
generated stubs. `/migrate-to-plugin` retires that surface in one approved pass:

```bash
/plugin update awow      # make sure the payload is current
/migrate-to-plugin       # classify → plan → approve → apply → parity report
```

Classification is read-only and shown, never assumed: lockfile baseline where
`tools/awow.lock.json` exists, the repo's own vendor commit where it does not, `--source`
history-matching as the fallback — and anything unresolved is treated as edited and preserved.
Edited files migrate to their plugin-era homes (archetypes → `context/team/workitem-archetypes/`,
meeting lenses → `context/team/meetings/`, edited command bodies → repo-local files); unedited
files are deleted because the payload now serves them. Nothing is written before you approve the
plan, and the run ends with a before/after parity table. The flow and its gates:
[`.agents/commands/migrate-to-plugin.md`](../.agents/commands/migrate-to-plugin.md).

Add `--check` to see the classification and plan without touching anything.

## What the version numbers mean

| Where | What it is |
| --- | --- |
| `.claude-plugin/plugin.json` → `version` | The canonical awow version. Bumped when payload files change; the plugin marketplace serves it. |
| Git tags (`v0.4.0`, …) | Pinnable release points on the awow repo, created by the release workflow when a version bump lands on `main`. |
| `CHANGELOG.md` | What each release changed, newest first — the section for a version is also the body of its GitHub release. |
| `tools/awow.lock.json` → `awow_version` | Legacy vendored repos only: the version the repo last reconciled against. `/migrate-to-plugin` reads it for classification and retires it. |

Maintainers: bump the version in the same change that alters payload files and add that
version's section to `CHANGELOG.md` (`python tools/release-notes.py --changelog CHANGELOG.md`
drafts it from the merged PRs since the previous release; trim it in the PR). When the bump
lands on `main`, the release workflow opens the awow-dist publish PR, tags the commit, and
publishes the GitHub release with that section as its body — there is no tag to push by hand.

## Sources of truth

- [`.agents/commands/migrate-to-plugin.md`](../.agents/commands/migrate-to-plugin.md) — the de-vendoring flow and its approval gate
- [`tools/awow_lock.py`](../tools/awow_lock.py) — the classification engine and lockfile format
- [`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json) — the canonical version
- Companion guides: [setup & the plugin model](guide-setup-and-two-harnesses.md) — how the payload reaches a repo in the first place
