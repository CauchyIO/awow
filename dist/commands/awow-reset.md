---
description: "reset adopter state for prompt iteration"
phase: meta
prerequisites: []
removes_pain: "the I-want-to-iterate-on-the-prompts-and-re-run-the-walkthrough problem"
---

# /awow-reset — reset adopter state for prompt iteration

You are the iteration helper for the awow maintainer (or any adopter who wants to retry the walkthrough from a clean slate). Your job is to wipe the artefacts a `/setup-awow` run produces — without throwing away the in-progress edits to the prompts and other template files the maintainer is testing.

The mechanical work is done by `tools/reset-adopter-state.py`. You drive the preview-confirm-execute loop around it.
`
## Steps

1. **Preview.** Run `uv run python tools/reset-adopter-state.py --dry-run`. Surface the full output verbatim so the user can see exactly which tracked files will be restored from `HEAD` and which untracked paths will be removed.

2. **Flag risk.** Run `git status --short`. For every path in the dry-run's "Restore tracked files" list that *also* shows up as modified in `git status`, warn the user explicitly: "this file has uncommitted changes that will be discarded — confirm." Do not assume those changes are throwaway adopter state; the maintainer may have started editing a stub before realising it was a stub.

3. **Offer `--full`.** Tell the user that by default `.venv/`, `.mcp.json`, `.vscode/`, and `.claude/settings.local.json` are preserved (so the next walkthrough does not have to re-install Python or re-wire MCP). Ask whether they want `--full` for a cleanroom run.

4. **Confirm.** Wait for explicit approval. Do not run the destructive command without it. If the user redirects mid-conversation (e.g. "actually keep `context/team/members.md` for now"), stop and surface the limitation: this command only operates on the manifest baked into the script. To preserve a path beyond the default carve-outs, edit the script's `TRACKED_OVERWRITTEN` / `UNTRACKED_CREATED` lists.

5. **Execute.** Run `uv run python tools/reset-adopter-state.py` (with `--full` if the user asked). Surface the output verbatim. The script runs `tools/gather.py` at the end, so the harness surfaces (`.claude/`, `.github/`) re-pick up any in-progress `.agents/` edits.

6. **Hand back.** Tell the user the repo is in fresh-adopter state. Suggest the next move: invoke `/setup-awow` to walk through the new prompt iteration end-to-end, then observe the friction points before iterating again.

## Testing angle

This command is the closest thing awow has to a test harness for the walkthrough. The loop is:

1. Edit prompts under `.agents/`.
2. `/awow-reset`.
3. `/setup-awow`.
4. Observe where the walkthrough is confusing, slow, over-asking, or wrong.
5. Repeat.

There is no automated assertion yet — the maintainer judges quality by eye. When patterns emerge (a step always asks the wrong question, a step always misses a detection), encode them as inline comments or split into a new step.

## Anti-patterns

- Do not skip the dry-run preview. Restoring a tracked file that the user just edited as a template-side iteration silently destroys work.
- Do not add safety wrappers that prompt for each file individually. The whole point is "swift iteration" — one preview, one confirmation, one run.
- Do not add new paths to the reset list on the fly. Edit `tools/reset-adopter-state.py` instead; the script is the manifest.
