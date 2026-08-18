---
name: awowify
description: Set up or extend awow (the Agentic Way of Working) in the current repo — vendor the agent-setup files non-destructively, then run setup. Use when the user wants to add awow to, or awowify, a project (new or existing).
---

# awowify — set up or extend awow in this repo

Use this skill when the user wants to bring awow into the current repository, new or existing. It copies awow's starter files in without overwriting anything, then continues into setup. This is the Copilot CLI counterpart of the `/awowify` command; the engine and flow are shared.

## 1. Confirm the target

The target is the current working directory. Confirm it is the repo the user means. If awow is already present here (`.agents/commands/setup-awow.md` exists), there is nothing to vendor — skip to step 4 and continue into setup. If the directory is not under git, say once that committing first makes the vendored tree and any `.awow` files easy to review, then continue; do not block.

## 2. Tailor what gets copied

Ask the user two things before copying, so awow brings only what they will use:

1. **Solo or team?** Solo drops the team-coordination files — neighbouring teams, the member roster, and the digest / cross-team / coaching / transcript commands. Pass `--solo` for solo; omit it for team.
2. **Which board?** Linear, Jira, Azure DevOps, or GitHub Issues — pass `--board <linear|jira|azure-devops|github-issues>`. If the user is unsure, omit the flag so all four references are kept.

## 3. Vendor

This plugin ships the vendoring engine. Locate it within the installed plugin and run it by absolute path — it resolves its own source tree from its location, so an absolute invocation copies the right files:

```
engine="$(find ~/.copilot/installed-plugins -path '*/setup/awowify.sh' 2>/dev/null | head -1)"
"$engine" --target "$PWD" [--solo] [--board <tool>] --dry-run
```

Show the dry-run output, summarise what will be copied and what is trimmed, and get the user's OK. Then run again without `--dry-run`. Existing files are saved as `<file>.awow` (never overwritten) and `README.md` is never copied; surface any conflicts so the user can merge them.

## 4. Continue into setup

The files are in place but the harness stubs are not generated yet. Read `.agents/commands/setup-awow.md` and follow it from the top — its Step 0 runs `setup/install.sh` (asking permission first) to wire Python and generate the Copilot stubs under `.github/`, then walks the rest of the wizard. You already know the user's solo/team and board choices from step 2: record them and do not re-ask.
