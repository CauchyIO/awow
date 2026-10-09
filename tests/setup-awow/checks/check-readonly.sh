# Checks — check-readonly. `/setup-awow --check` writes nothing: the recorded decoy identity
# survives untouched and gains no verification line, and none of the places the wizard writes
# to — proposals/, .awow/, the team-profile fill — come into existence. Mirrors Q7.

pre() {
  file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
  file-contains setup-progress.md 'board-url: https://linear\.app/example-team/team/EX/all'
  file-not-contains setup-progress.md 'surface-verification'
  file-exists context/tooling/board.md
  dir-absent proposals
  dir-absent .awow
  dir-absent context/team
}

post() {
  file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
  file-contains setup-progress.md 'board-url: https://linear\.app/example-team/team/EX/all'
  file-contains setup-progress.md '\[ \] 1b\. Board configuration'
  file-not-contains setup-progress.md 'surface-verification'
  file-not-contains setup-progress.md 'write-'
  file-contains context/tooling/board.md 'frozen test fixture'
  dir-absent proposals
  dir-absent .awow
  dir-absent context/team
}
