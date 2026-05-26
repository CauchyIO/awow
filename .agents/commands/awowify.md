---
phase: kickoff
prerequisites: []
removes_pain: "the I-already-have-a-repo-so-Use-this-template-cannot-help problem"
---

# /awowify — drop awow onto an existing repo

You are the awowify bootstrap. This command exists for the one case "Use this template" cannot serve: adding awow to a repo that already has code and history. You ship as a Claude Code **plugin** command, so you are available before any awow files exist in the target repo. The awow starter tree is at `${CLAUDE_PLUGIN_ROOT}` — the installed plugin clone.

Your job: vendor the starter tree into the user's current repo without overwriting anything, wire it up, then continue straight into the `/setup-awow` wizard. The user types one command and lands in configuration.

## Step 1 — Confirm the target and locate the starter tree

The target is the current working directory; confirm it is the repo the user means. The starter tree to vendor from is at `${CLAUDE_PLUGIN_ROOT}` — the installed plugin clone.

**If awow is already present here** — `${CLAUDE_PLUGIN_ROOT}` is unset or resolves to the current directory, or `.agents/commands/setup-awow.md` already exists — there is nothing to vendor. Skip to Step 4 and continue into the wizard. Never bounce the user to a different command; awowify carries the flow through itself.

If the directory is not under git, say once that committing first makes the vendored tree and any `.awow` files easy to review, then continue. Do not block on it.

## Step 2 — Preview (dry run)

Run the engine in dry-run mode and show the output verbatim:

```
"${CLAUDE_PLUGIN_ROOT}/setup/awowify.sh" --source "${CLAUDE_PLUGIN_ROOT}" --target "$PWD" --dry-run
```

Summarise three things: how many files will be copied, which existing files will be saved as `<file>.awow` (their originals are never touched), and that `README.md` is never vendored. Ask for explicit permission before the real copy. Write nothing until the user approves.

## Step 3 — Vendor

On approval, run the same command without `--dry-run`. Surface its output. If it reported conflicts, name each `.awow` file: these are awow's versions saved beside the user's own to merge later — they do not block setup. `pyproject.toml.awow` matters only if the user later wants the skills that need extra Python dependencies.

## Step 4 — Hand off to the wizard

Whether you vendored just now or awow was already here, continue in the same session — do not wait for the user to type anything. Read `.agents/commands/setup-awow.md` and execute it from the top. Its Step 0 detection runs `setup/install.sh` (asking permission first, as it always does) only when the stubs or `.venv` are missing — that wires `uv` / `.venv` and runs `tools/gather.py` — and skips straight ahead when they are already in place. Continue through Step 1 and onward, including the solo-or-team question the wizard asks on entry.

Tell the user once, at the handoff:

> awow is vendored in. I'm continuing straight into setup — the same flow as `/setup-awow`. You can stop after the board is wired (Step 1) and resume anytime.
