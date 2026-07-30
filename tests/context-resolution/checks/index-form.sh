# Checks — index-form. Read-only command; the mechanical facts are fixture
# integrity. Conduct (targeting line, no cross-board bleed) is the rubric's.

pre() {
  file-exists context/tooling/board.md
  file-exists context/tooling/board-product.md
  file-exists context/tooling/board-infra.md
  file-exists setup-progress.md
}

post() {
  file-exists context/tooling/board.md
  file-exists context/tooling/board-product.md
  file-exists context/tooling/board-infra.md
}
