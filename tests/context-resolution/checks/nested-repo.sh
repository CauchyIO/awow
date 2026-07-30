# Checks — nested-repo. Read-only command; the mechanical facts are fixture
# integrity plus the no-uninvited-scaffold guarantee. Conduct (declining to
# borrow the outer board) is the rubric's.

pre() {
  file-exists context/tooling/board.md
  file-exists vendor-tool/README.md
}

post() {
  file-exists context/tooling/board.md
  file-exists vendor-tool/README.md
  dir-absent vendor-tool/context
}
