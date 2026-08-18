# Checks — plan-gate. Mechanical facts: fixture integrity before, execution
# evidence in the file-based board after. Gate conduct is the rubric's.

pre() {
  file-exists context/tooling/board.md
  file-exists notes/standup.md
  file-contains context/tooling/board.md "In Progress"
}

post() {
  file-exists context/tooling/board.md
  file-contains context/tooling/board.md "In Review"
  file-contains context/tooling/board.md "10 MB"
}
