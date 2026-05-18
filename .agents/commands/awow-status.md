---
phase: meta
prerequisites: ["Step 1 of /setup-awow complete"]
removes_pain: "the where-am-I-in-the-rollout problem"
---

# /awow-status — report current phase and readiness signals

Read `setup-progress.md`, the active commands in `.agents/commands/`, and recent activity in `proposals/` and `traces/` (if present). Tell the user:

- Which `/setup-awow` steps are complete, deferred, or untouched.
- Which Spread / Standardise commands are wired up.
- Which next commands the team has the prerequisites for but has not added (suggest `/awow-add <name>` for each).
- Soft observations: "you have been running `refinement-prep` weekly for two months — `process-workitem` is the natural next step", or "your board MCP has been wired for six weeks but you have not run a single `/process-workitem` — is there a friction worth surfacing?"

This is a status report, not an enforcement step. Output to chat, do not write a file unless the user asks.
