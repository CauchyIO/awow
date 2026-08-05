# Checks — planted-violation. Mechanical facts only: the corrected title verb,
# taxonomy labels, recap prose kept out, neighbours untouched. Search, citation,
# and gate behaviour are the rubric's to judge.

pre() {
  file-exists context/tooling/board.md
  file-exists context/team/conventions/REQUIRED/issue-titles.md
  file-exists context/team/conventions/REQUIRED/labels.md
  file-exists context/team/conventions/REQUIRED/output-discipline.md
  file-exists context/team/style/board-output.md
  dir-exists board/issues
  file-exists board/issues/T-101.md
  file-exists board/issues/T-102.md
  file-absent board/issues/T-103.md
}

post() {
  file-exists board/issues/T-103.md
  file-contains board/issues/T-103.md '^title: (Fix|Investigate|Add|Update|Implement) '
  file-contains board/issues/T-103.md 'type:(bug|chore|feature)'
  file-contains board/issues/T-103.md 'Acceptance criteria'
  # The planted violations must not survive into the written issue.
  file-not-contains board/issues/T-103.md 'URGENT'
  file-not-contains board/issues/T-103.md 'stuff broken maybe'
  file-not-contains board/issues/T-103.md 'standup'
  file-not-contains board/issues/T-103.md 'Jamie'
  # Neighbouring issues untouched.
  file-contains board/issues/T-101.md '^state: done'
  file-contains board/issues/T-102.md '^state: todo'
}
