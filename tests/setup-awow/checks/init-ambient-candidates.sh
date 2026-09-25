# Checks — init-ambient-candidates. The picked server cannot read the board, so
# the run stops at the install pointer: no board.md, no conventions, no AGENTS.md;
# no progress file, no proposals/setup/. Mirrors rubric Q8–Q9.

pre() {
  file-contains .mcp.json 'linear\.example\.invalid'
  file-contains .claude/settings.local.json 'jira\.example\.invalid'
  file-absent AGENTS.md
  file-absent context/tooling/board.md
  file-absent setup-progress.md
}

post() {
  file-absent context/tooling/board.md
  dir-absent context/team
  file-absent AGENTS.md
  file-absent setup-progress.md
  dir-absent proposals/setup
}
