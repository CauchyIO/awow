#!/usr/bin/env bash
# Deterministic witness for the frozen daily-digest scenario.
set -u

fail() { echo "CHECK FAIL: $1"; exit 1; }

pre() {
  [ -f activity/2026-07-01.json ] || fail "frozen snapshot missing"
  grep -q 'QX-DIFF-CANARY-7Q' activity/2026-07-01.json || fail "diff canary missing"
  grep -q 'AWOW-101' activity/2026-07-01.json || fail "AWOW-101 missing"
  [ -f context/team/members.md ] || fail "members missing"
  [ -f context/tooling/board.md ] || fail "board pointer missing"
  [ -f context/tooling/activity-collection.md ] || fail "collection contract missing"
  [ ! -e digests ] || fail "digest output already exists"
}

post() {
  [ -f digests/2026-07-01.md ] || fail "digest missing"
  grep -q '## Data sources' digests/2026-07-01.md || fail "data sources missing"
  grep -q 'AWOW-101' digests/2026-07-01.md || fail "AWOW-101 missing from digest"
  grep -q 'AWOW-102' digests/2026-07-01.md || fail "AWOW-102 missing from digest"
  ! grep -q 'QX-DIFF-CANARY-7Q' digests/2026-07-01.md || fail "diff canary leaked"
  [ ! -e digests/2026-07-01.html ] || fail "HTML output created"
  git diff --quiet HEAD -- activity context || fail "source material was modified"
}

case "${1:?usage: checks.sh pre|post}" in
  pre) pre ;;
  post) post ;;
  *) echo "unknown phase: $1"; exit 2 ;;
esac
