# Checks — install-step1a-cli. Phase 1a wires the gh CLI surface and drafts
# board.md proposal-first. Mirrors rubric Q7–Q8.

pre() {
  file-exists setup-progress.md
  file-contains setup-progress.md '\[x\].*Step 0'
  dir-exists .venv
  dir-exists context/tooling/boards/github-issues/reference
}

post() {
  file-exists context/tooling/board.md
  file-contains context/tooling/board.md 'CauchyIO'
  file-contains context/tooling/board.md 'gh-cli'
  file-contains context/tooling/board.md 'https://github\.com/orgs/CauchyIO/projects/3'
  file-exists proposals/setup/step-1/board.md
}
