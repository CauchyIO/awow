# Updating awow

How a repo takes newer awow.

> **TL;DR** — With the plugin installed, updating is a single harness command:
> `/plugin update awow` (Copilot CLI: `copilot plugin update awow`). Nothing lives in your repo
> to reconcile — the plugin's files are replaced wholesale and your `context/` is never part of
> it.

## The plugin model: update is not a merge

The payload (commands, skills, handlers, runtime tools, reference context) is served from the
plugin install, not copied into your repo. Team-owned content — `context/team/`,
`context/company/`, `board.md`, `proposals/` — lives only in your repo, so
a plugin update cannot touch it. There is no lockfile, no 3-way compare, no conflict files left
behind.

One exception: if you keep your own edited copy of a command or skill in the repo, it overrides
the plugin's version — and stops getting updates. Contribute the change back to awow once it's merged, or re-diff your copy against the plugin
after big releases.

## What the version numbers mean

| Where | What it is |
| --- | --- |
| `.claude-plugin/plugin.json` → `version` | The canonical awow version. Bumped when payload files change; the plugin marketplace serves it. |
| Git tags (`v0.4.0`, …) | Pinnable release points on the awow repo, created by the release workflow when a version bump lands on `main`. |
| `CHANGELOG.md` | What each release changed, newest first — the section for a version is also the body of its GitHub release. |

Maintainers: bump the version in the same change that alters payload files and add that
version's section to `CHANGELOG.md` (`python tools/release-notes.py --changelog CHANGELOG.md`
drafts it from the merged PRs since the previous release; trim it in the PR). When the bump
lands on `main`, the release workflow opens the awow-dist publish PR, tags the commit, and
publishes the GitHub release with that section as its body — there is no tag to push by hand.

## Sources of truth

- [`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json) — the canonical version
- Companion guides: [how awow is built and shipped](guide-setup-and-two-harnesses.md) — how the payload reaches a repo in the first place; [SETUP.md](../SETUP.md) — the one setup page
