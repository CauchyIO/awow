#!/usr/bin/env bash
# Deterministic witness for the file-backed workitem-write scenario.
set -u

fail() { echo "CHECK FAIL: $1"; exit 1; }

pre() {
  [ -f context/tooling/board.md ] || fail "board contract missing"
  [ -f context/team/conventions/REQUIRED/issue-titles.md ] || fail "title convention missing"
  [ -f context/team/conventions/REQUIRED/labels.md ] || fail "label convention missing"
  [ -f context/team/conventions/REQUIRED/output-discipline.md ] || fail "output convention missing"
  [ -f context/team/style/board-output.md ] || fail "board style missing"
  [ -f board/issues/T-101.md ] || fail "T-101 missing"
  [ -f board/issues/T-102.md ] || fail "T-102 missing"
  [ ! -e board/issues/T-103.md ] || fail "T-103 already exists"
}

post() {
  [ -f board/issues/T-103.md ] || fail "T-103 missing"
  [ "$(find board/issues -maxdepth 1 -name 'T-*.md' | wc -l | tr -d ' ')" = 3 ] || fail "expected exactly one new issue"
  grep -Eq '^title: (Fix|Investigate|Add|Update|Implement) ' board/issues/T-103.md || fail "title is not verb-first"
  grep -Eq 'type:(bug|chore|feature)' board/issues/T-103.md || fail "type label is off taxonomy"
  grep -Eq 'area:(api|web|ops)' board/issues/T-103.md || fail "area label is off taxonomy"
  grep -qi 'Acceptance criteria' board/issues/T-103.md || fail "acceptance criteria missing"
  ! grep -Eqi 'URGENT|stuff broken maybe|standup|Jamie' board/issues/T-103.md || fail "status recap leaked into issue"
  git diff --quiet HEAD -- board/issues/T-101.md board/issues/T-102.md || fail "neighbour issue changed"
}

case "${1:?usage: checks.sh pre|post}" in
  pre) pre ;;
  post) post ;;
  *) echo "unknown phase: $1"; exit 2 ;;
esac
