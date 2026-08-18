# Checks — stale-move. PB-1's row must survive apply untouched; the stale-guard
# refusing the move is the rubric's to grade.

pre() {
  file-exists context/tooling/board.md
  file-contains context/tooling/board.md "| PB-1 | Wire retry budget into the export job | Done | dana |"
}

post() {
  file-contains context/tooling/board.md "| PB-1 | Wire retry budget into the export job | Done | dana |"
}
