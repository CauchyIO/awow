#!/usr/bin/env bash
# Deterministic witness for setup-awow-walkthrough (night eval content spec §3).
# Invoked by the harness as `bash checks.sh pre|post`, cwd = the cell tree.
# Exit 0 = pass, 1 = assertion failed, anything else = broken check.
set -u

fail() { echo "CHECK FAIL: $1"; exit 1; }

pre() {
  # the fixture must still be the seed-stub state the rubric assumes
  [ -f context/mission.md ] || fail "fixture: context/mission.md missing"
  [ -f context/team.md ]    || fail "fixture: context/team.md missing"
  grep -q "SEED STUB" context/mission.md || fail "fixture: mission.md lost its SEED STUB marker"
  grep -q "SEED STUB" context/team.md    || fail "fixture: team.md lost its SEED STUB marker"
}

post() {
  # mechanical halves of rubric Q1/Q2: files exist, stubs replaced, board named
  [ -s context/mission.md ] || fail "mission.md missing or empty"
  [ -s context/team.md ]    || fail "team.md missing or empty"
  grep -q "SEED STUB" context/mission.md && fail "mission.md is still a seed stub"
  grep -q "SEED STUB" context/team.md    && fail "team.md is still a seed stub"
  grep -qi "github issues" context/team.md || fail "team.md does not name the board (GitHub Issues)"
  exit 0
}

case "${1:?usage: checks.sh pre|post}" in
  pre)  pre ;;
  post) post ;;
  *)    echo "unknown phase: $1"; exit 2 ;;
esac
