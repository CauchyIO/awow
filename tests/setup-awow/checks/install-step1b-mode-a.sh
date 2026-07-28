# Checks — install-step1b-mode-a. Phase 1b section walk in Mode A appends
# every reference section to the Phase 1a draft. Mirrors rubric Q4.

pre() {
  file-exists proposals/setup/step-1/board.md
  dir-exists context/tooling/boards/github-issues/reference
  file-exists context/tooling/boards/github-issues/reference/states.md
  file-exists context/tooling/boards/github-issues/reference/labels.md
}

post() {
  file-contains proposals/setup/step-1/board.md '## State machine'
  file-contains proposals/setup/step-1/board.md '## Hierarchy'
  file-contains proposals/setup/step-1/board.md '## Label taxonomy'
  file-contains proposals/setup/step-1/board.md '## Required fields'
  file-contains proposals/setup/step-1/board.md '## Team page conventions'
}
