# Checks — monorepo-two-trees. Read-only command; the mechanical facts are
# fixture integrity. Conduct (asking once, no cross-tree bleed) is the rubric's.

pre() {
  file-exists teams/alpha/context/tooling/board.md
  file-exists teams/beta/context/tooling/board.md
}

post() {
  file-exists teams/alpha/context/tooling/board.md
  file-exists teams/beta/context/tooling/board.md
}
