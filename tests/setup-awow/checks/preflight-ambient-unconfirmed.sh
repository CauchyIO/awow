# Checks — preflight-ambient-unconfirmed. Explicit pick recorded as identity
# only; verification pending; the unpicked candidate stays unrecorded.
# Mirrors rubric Q7–Q9.

pre() {
  file-contains .mcp.json 'linear\.example\.invalid'
  file-contains .claude/settings.local.json 'jira\.example\.invalid'
  file-not-contains setup-progress.md 'surface:'
}

post() {
  file-contains setup-progress.md 'surface: mcp'
  file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
  file-contains setup-progress.md 'board-url: https://linear\.app/example-team/team/EX/all'
  file-contains setup-progress.md 'surface-verification: pending'
  file-not-contains setup-progress.md 'jira\.example\.invalid'
}
