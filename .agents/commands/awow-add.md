---
phase: meta
prerequisites: ["Step 1 of /setup-awow complete"]
removes_pain: "the I-want-the-daily-digest-but-don't-want-the-whole-phase-4-stack problem"
---

# /awow-add — opt into a Spread or Standardise command

Promote a phase-tagged command from "documented but inactive" to "wired up and ready to invoke." Used when the team is ready for a command that `/setup-awow` deliberately leaves off the seed set.

## Inputs

- The command name (e.g. `daily-digest`, `board-skill`, `claudetracing-setup`)

## Steps

1. Locate the command file in `.agents/commands/{spread,standardise}/<name>.md`. If not found, list available options grouped by phase.
2. **Stub guard.** Check whether the body matches the stub sentinel — a line beginning with `Stub.` followed by a version string (e.g. `Stub. v0.2 ships the working version.`). If it does, tell the user the command is documented but not yet implemented, name the version that ships it, and stop. Do not write a brief and do not copy the file. The team can re-run `/awow-add <name>` once the working version lands.
3. Read the frontmatter `prerequisites:` block.
4. Check each prerequisite. If any fail, surface the failures and ask whether to proceed anyway (soft warning, not hard gate — per `input/PROPOSAL.md` §6 Q13).
5. Write a one-page brief to `proposals/awow-add/<name>.md` explaining what the command does, what it changes about the team's workflow, and what the team should be prepared for. Reference the "removes_pain" line from frontmatter.
6. Wait for user approval.
7. On approval: copy the command into the active command surface (mirror via `tools/gather.py`). Update `setup-progress.md` with a note that `<name>` was added.

## Anti-patterns

- Do not bypass the prerequisite check silently. If the wizard misreads the team's substrate, the user can override — but they should know what they are overriding.
- Do not skip the stub guard. A stub command surfaced as "wired up" misleads the user; the brief renders the placeholder `removes_pain` verbatim and the command itself does nothing on invocation.
