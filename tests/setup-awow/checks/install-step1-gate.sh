# Checks — install-step1-gate. board.md is already landed; the gate accepts
# `proceed`. Mirrors the mechanical half of rubric Q4 (board.md in place); the
# gate behaviour itself is judge territory.

pre() {
  file-exists context/tooling/board.md
  file-exists proposals/setup/step-1/board.md
  file-exists setup-progress.md
}

post() {
  file-exists context/tooling/board.md
  file-exists proposals/setup/step-1/board.md
}
