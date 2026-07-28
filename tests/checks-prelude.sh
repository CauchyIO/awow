# Check verb prelude — sourced by tests/run-checks.sh before a scenario's checks file.
# NOT executable on purpose: this file is sourced, never run. See tests/README.md.
#
# Each verb records exactly one line to stdout:
#     CHECK	pass|fail	<verb> <args...>
# Verbs always return 0 — recording, not aborting, is their job. The driver
# owns the exit-code discipline (0 all pass / 1 assertion failed / 127 broken).
# A verb that cannot evaluate (missing file for a content check) records fail
# with a reason suffix rather than crashing.

_CHECK_FAILED=0

_record() {
  local status="$1"; shift
  printf 'CHECK\t%s\t%s\n' "$status" "$*"
  if [ "$status" = fail ]; then _CHECK_FAILED=1; fi
  return 0
}

file-exists() {
  if [ -f "$1" ]; then _record pass "file-exists $1"; else _record fail "file-exists $1"; fi
}

file-absent() {
  if [ ! -e "$1" ]; then _record pass "file-absent $1"; else _record fail "file-absent $1"; fi
}

dir-exists() {
  if [ -d "$1" ]; then _record pass "dir-exists $1"; else _record fail "dir-exists $1"; fi
}

dir-absent() {
  if [ ! -d "$1" ]; then _record pass "dir-absent $1"; else _record fail "dir-absent $1"; fi
}

# file-contains <path> <extended-regex>
file-contains() {
  if [ ! -f "$1" ]; then _record fail "file-contains $1 $2 (file missing)"; return 0; fi
  if grep -Eq -- "$2" "$1"; then _record pass "file-contains $1 $2"; else _record fail "file-contains $1 $2"; fi
}

# file-not-contains <path> <extended-regex> — the file must exist; a missing
# file is a broken precondition, not a vacuous pass.
file-not-contains() {
  if [ ! -f "$1" ]; then _record fail "file-not-contains $1 $2 (file missing)"; return 0; fi
  if grep -Eq -- "$2" "$1"; then _record fail "file-not-contains $1 $2"; else _record pass "file-not-contains $1 $2"; fi
}
