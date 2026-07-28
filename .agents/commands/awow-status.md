---
phase: meta
prerequisites: ["Step 1 of /setup-awow complete"]
removes_pain: "the where-am-I-in-the-rollout problem"
channel: vendored
---

# /awow-status — report current phase and readiness signals

Read `setup-progress.md`, the active commands in `.agents/commands/`, and recent activity in `proposals/` and `traces/` (if present). Tell the user:

- Which `/setup-awow` steps are complete, deferred, or untouched.
- Which Spread / Standardise commands are wired up.
- Which next commands the team has the prerequisites for but has not added (suggest `/awow-add <name>` for each).
- Soft observations: "you have been running `refinement-prep` weekly for two months — `process-workitem` is the natural next step", or "your board has been wired up for six weeks but you have not run a single `/process-workitem` — is there a friction worth surfacing?"

## Freshness — how current is the scaffolding

Run `python tools/awow_lock.py status` (read-only) and fold the result in:

- The recorded awow version (and commit) the repo is on.
- How many starter-owned files the team has **locally modified** since that
  baseline — useful context, not a problem to fix.

This runs offline against `tools/awow.lock.json`. It cannot tell whether a newer
awow exists — that needs a source to compare against. If the user wants to check
for and pull updates, point them at **`/update-awow`** (which refreshes the
plugin / an upstream checkout, shows a 3-way plan, and applies on approval). If
`tools/awow.lock.json` is missing, note the repo predates the lockfile and
`/update-awow` will seed it on first run.

This is a status report, not an enforcement step. Output to chat, do not write a file unless the user asks.
