# Checks — preflight-board-blocked. Recorded decoy identity must survive
# untouched; mission draft lands under proposals/setup/step-2/. Mirrors Q8–Q9.

pre() {
  file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
  file-contains setup-progress.md 'harnesses: claude-code, copilot, visual-studio'
  file-absent context/tooling/board.md
}

post() {
  file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
  file-exists context/team/mission.md
}
