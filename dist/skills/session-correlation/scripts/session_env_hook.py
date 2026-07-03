#!/usr/bin/env python3
"""SessionStart hook: expose the Claude Code session ID to Bash as $CLAUDE_SESSION_ID.

Reads the SessionStart payload from stdin and appends an ``export`` line to the
file named by ``$CLAUDE_ENV_FILE``. Claude Code sources that file into every
subsequent Bash tool call, so the agent can read ``$CLAUDE_SESSION_ID`` on
demand -- no per-turn context injection, and it survives compaction because it
lives shell-side, not in context.

This is the runtime *accessor* behind the board session-footer convention: the
agent stamps each board entry it authors with ``_session: <id>_``, and that id
is exactly what the MLflow Stop hook tags the trace with
(``mlflow.trace.session``) -- so the issue links back to the session trace.

Wire in .claude/settings.local.json (per-machine, gitignored):

  "SessionStart": [
    {"hooks": [{"type": "command",
                "command": "python3 \"$CLAUDE_PROJECT_DIR/.agents/skills/session-correlation/scripts/session_env_hook.py\""}]}
  ]

The hook re-runs on resume/clear/compact, so the variable stays populated.
"""

import json
import os
import sys

# Fail loud, never swallow: a malformed payload or missing field should crash
# with a traceback rather than silently leave the accessor unset.
payload = json.load(sys.stdin)
session_id = payload["session_id"]

env_file = os.environ.get("CLAUDE_ENV_FILE")
if not env_file:
    print(
        "session_env_hook: CLAUDE_ENV_FILE is unset; cannot persist "
        "CLAUDE_SESSION_ID (is this a SessionStart hook?)",
        file=sys.stderr,
    )
    sys.exit(1)

# Append, never overwrite -- other hooks may write to the same file.
with open(env_file, "a") as fh:
    fh.write(f"export CLAUDE_SESSION_ID={session_id}\n")
