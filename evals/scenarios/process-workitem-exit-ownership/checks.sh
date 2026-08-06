#!/usr/bin/env bash
# Deterministic witness for process-workitem exit ownership.
set -u

fail() { echo "CHECK FAIL: $1"; exit 1; }

pre() {
  [ -f board/issues/T-204.md ] || fail "T-204 missing"
  grep -q '^state: todo' board/issues/T-204.md || fail "T-204 not todo"
  [ -f src/slug.py ] || fail "slug source missing"
  [ -f tests/test_slug.py ] || fail "acceptance test missing"
  if python3 -m unittest discover -s tests -v >/dev/null 2>&1; then
    fail "fixture acceptance test unexpectedly passes"
  fi
}

post() {
  [ -f proposals/T-204.md ] || fail "approved plan artefact missing"
  python3 -m unittest discover -s tests -v || fail "acceptance test failed"
  grep -q '^state: in-review' board/issues/T-204.md || fail "T-204 not in review"
  grep -Eqi 'verified.*python3 -m unittest discover -s tests -v' board/issues/T-204.md || fail "verification evidence missing from Activity"
}

case "${1:?usage: checks.sh pre|post}" in
  pre) pre ;;
  post) post ;;
  *) echo "unknown phase: $1"; exit 2 ;;
esac
