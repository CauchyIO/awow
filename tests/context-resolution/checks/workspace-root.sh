# Checks — workspace-root. Read-only command; the mechanical facts are fixture
# integrity. Conduct (picking once, no sibling bleed) is the rubric's.

pre() {
  file-exists repo-solo/context/tooling/board.md
  file-exists repo-mono/context/tooling/board.md
  file-exists repo-mono/context/tooling/board-product.md
  file-exists repo-mono/context/tooling/board-infra.md
}

post() {
  file-exists repo-solo/context/tooling/board.md
  file-exists repo-mono/context/tooling/board.md
  file-exists repo-mono/context/tooling/board-product.md
  file-exists repo-mono/context/tooling/board-infra.md
}
