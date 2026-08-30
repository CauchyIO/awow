# Checks — preflight-board-blocked. Recorded decoy identity (server + board URL
# naming team EX) must survive untouched and gain no verification line — preflight
# writes nothing; mission draft lands under proposals/setup/step-2/. Mirrors Q8–Q9.

pre() {
  file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
  file-contains setup-progress.md 'board-url: https://linear\.app/example-team/team/EX/all'
  file-contains setup-progress.md 'harnesses: claude-code, copilot, visual-studio'
  file-not-contains setup-progress.md 'surface-verification'
  file-absent context/tooling/board.md
}

post() {
  file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
  file-contains setup-progress.md 'board-url: https://linear\.app/example-team/team/EX/all'
  file-not-contains setup-progress.md 'surface-verification'
  file-exists context/team/mission.md
}
