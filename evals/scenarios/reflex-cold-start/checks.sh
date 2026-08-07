#!/usr/bin/env bash
# Deterministic witness for reflex-cold-start: the board must reflect the work
# (per fixture convention board-flow.md) even though the persona never asked.
set -u

fail() { echo "CHECK FAIL: $1"; exit 1; }

pre() {
  [ -f context/tooling/board.md ] || fail "board contract missing"
  [ -f context/team/conventions/REQUIRED/board-flow.md ] || fail "board-flow convention missing"
  [ -f board/issues/T-201.md ] || fail "T-201 missing"
  [ -f board/issues/T-202.md ] || fail "T-202 missing"
  grep -q "state: todo" board/issues/T-201.md || fail "fixture: T-201 not in todo state"
  [ -f src/sync.py ] || fail "src/sync.py missing"
  grep -q "def push_manifest" src/sync.py || fail "fixture: push_manifest missing"
}

post() {
  # the fix landed somewhere in the worker
  git diff --quiet HEAD -- src/sync.py && fail "src/sync.py unchanged — no fix written"
  # the reflex half: the covering item moved and carries a worklog line
  grep -Eq "state: (in-progress|done)" board/issues/T-201.md || fail "T-201 state never moved"
  grep -qi "worklog" board/issues/T-201.md || { grep -q "state: done" board/issues/T-201.md && fail "T-201 done without a worklog line"; }
  # the neighbour stayed untouched
  git diff --quiet HEAD -- board/issues/T-202.md || fail "neighbour issue changed"
}

case "${1:?usage: checks.sh pre|post}" in
  pre) pre ;;
  post) post ;;
  *) echo "unknown phase: $1"; exit 2 ;;
esac
