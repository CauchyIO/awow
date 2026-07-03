---
name: session-correlation
description: "Link agent-authored board entries (GitHub/Linear/ADO issues and PRs) back to the session trace that produced them, by stamping each entry with a session-ID footer. Use this skill to enable, wire up, or explain session-board correlation: the SessionStart accessor that exposes the harness session ID to the agent, the footer convention, and how the id joins board content to MLflow (or other backend) traces. Opt-in capability — enabling it installs an enforced footer rule into the team's conventions."
---

# Session-board correlation

> **Opt-in capability.** On its own this skill changes nothing about how the agent behaves. It becomes active only when a team **opts in** — during `/setup-awow` (Step 3) or later via `/awow-add`. Opting in (a) wires the SessionStart accessor hook and (b) writes the footer rule into *that team's* conventions, at which point it is a normal, enforced rule. Teams that never opt in carry none of it: no rule, no `$CLAUDE_SESSION_ID` expectation, no error.

Agent-originated board entries normally have no link back to the trace that produced them, so the downstream skills (`awow-usage-coach`, `daily-digest`, `weekly-digest`, `prompt-skill-analysis`) cannot join board content to session data. This skill closes that gap with a one-line **session footer** on every entry the agent authors.

## The footer

Every board entry the agent authors ends with a single italic line:

```
_session: <session-id>_
```

The `<session-id>` is the harness's session identifier. Under Claude Code with tracing enabled, that id is exactly what the MLflow Stop hook tags the trace with (`mlflow.trace.session`) — so the issue or PR links straight back to the session's prompts and tool calls. The footer is machine-parseable: the digest and coaching skills search for `_session: <id>_` to correlate.

## How the agent gets its own session ID

By default the agent has **no** access to its own session ID at runtime — no env var, no built-in. This skill solves that with a `SessionStart` hook, `scripts/session_env_hook.py`:

- The hook reads `session_id` from the SessionStart payload and appends `export CLAUDE_SESSION_ID=<id>` to `$CLAUDE_ENV_FILE`.
- Claude Code sources that file into **every** subsequent `Bash` tool call, so the agent reads `$CLAUDE_SESSION_ID` on demand.
- It is **shell-side, not context-side**: zero per-turn context cost, and it survives compaction and `/clear`. The hook re-runs on resume/clear/compact, so the variable stays populated.

At board-write time the agent reads `$CLAUDE_SESSION_ID` (e.g. `echo "$CLAUDE_SESSION_ID"`) and includes it in the footer of the body it writes — whether via the `gh` CLI, the GitHub MCP, or another board tool.

## Prerequisite — tracing must already be enabled

This skill does **not** set up tracing. It assumes the trace-writing stack is already wired and refuses to proceed if it is not — otherwise it would stamp footers whose `<id>` points at traces that were never written (dead links).

**Check before enabling.** Tracing is wired when `.claude/settings.local.json` contains both:
- `"MLFLOW_CLAUDE_TRACING_ENABLED": "true"` (plus a tracking URI and Databricks profile in `env`), and
- a `Stop` hook running the MLflow handler (`mlflow.claude_code.hooks` / `mlflow autolog claude`).

If both are present, proceed to "Enabling it". If not, **stop and tell the user tracing is not configured.** Point them at the team's `claudetracing` library (sibling repo, e.g. `../claudetracing`), which provisions the Databricks MLflow side; offer to help wire the local `.claude/settings.local.json` against it, but treat tracing setup as a **separate** step that this skill does not own. Do not install the footer rule until tracing is confirmed.

## Enabling it (what opt-in does)

0. **Confirm the prerequisite above.** Do not continue if tracing is not wired.

1. **Wire the accessor hook.** Add to `.claude/settings.local.json` (per-machine, gitignored — it sits alongside the MLflow Stop hook):

   ```json
   "SessionStart": [
     {
       "hooks": [
         {
           "type": "command",
           "command": "python3 \"$CLAUDE_PROJECT_DIR/.agents/skills/session-correlation/scripts/session_env_hook.py\""
         }
       ]
     }
   ]
   ```

   This takes effect on the next session (or on resume/clear/compact of the current one).

2. **Install the footer rule into the team's conventions.** Append the rule below to the team's `context/team/conventions/REQUIRED/output-discipline.md` and the shape note to `context/team/style/board-output.md`, then re-run `tools/gather.py` so it lands in the generated `CLAUDE.md` / `AGENTS.md`. The base templates stay clean — the rule is added only for teams that opted in.

   **Convention text to install (output-discipline.md, as a new Rule):**

   ```markdown
   ## Rule 4 — Session footer

   Every board entry you author — issue create, issue comment, PR create, PR
   comment — ends with a session footer linking it to the session that produced
   it:

       _session: <session-id>_

   Read the id from `$CLAUDE_SESSION_ID` (populated by the session-correlation
   SessionStart hook) or your harness's equivalent. The id matches the trace's
   `mlflow.trace.session` tag, so `awow-usage-coach`, `daily-digest`, and
   `weekly-digest` can join board content to session traces.

   **Exempt:** trivial metadata-only changes (label, state, project-add) and
   one-line status comments. The footer is required when the entry records a
   decision or finding, or runs two or more sentences.
   ```

   **Shape note to install (board-output.md, Shape section):**

   ```markdown
   - Session footer: entries that record a decision/finding (or run ≥ 2 sentences)
     end with `_session: <id>_` on its own line. See
     `conventions/REQUIRED/output-discipline.md` Rule 4.
   ```

## Verifying

- After enabling, start a fresh session and run `echo "$CLAUDE_SESSION_ID"` — it should print the current session id (the same id as the transcript filename under `~/.claude/projects/<project>/`).
- Author a test board comment and confirm the footer is present and the id resolves to a trace in the team's experiment.

## Harness-agnostic note

The *rule* is written harness-neutrally ("your harness's session ID"). The *accessor* here is Claude-Code-specific (`SessionStart` + `CLAUDE_ENV_FILE`). A team on GitHub Copilot or another harness keeps the same footer convention but supplies its own accessor for exposing the session id to the agent.

## Relationship to tracing

This skill correlates board entries to traces; it does **not** create the traces, and it does **not** configure tracing. Trace recording is the MLflow Stop hook (`MLFLOW_CLAUDE_TRACING_ENABLED=true` in `.claude/settings.local.json`); the Databricks MLflow side is provisioned by the team's `claudetracing` library (sibling repo `../claudetracing`). The footer is only useful when tracing is already on — hence the prerequisite check above. Exporting and analysing the traces is `mlflow-export` + `prompt-skill-analysis` / `awow-usage-coach`.
