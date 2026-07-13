# tests/harness/lib/assert.sh — sourced, never executed.
# Extends the shared check prelude with a skip verb and command/output verbs.
_ASSERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$_ASSERT_DIR/../../checks-prelude.sh"

# skip <reason...> — records a non-failing CHECK line (absence is not failure).
skip() { printf 'CHECK\tskip\t%s\n' "$*"; return 0; }

# cmd-succeeds <label> -- <cmd...> : run cmd, record pass iff exit 0.
cmd-succeeds() {
  local label="$1"; shift; [ "$1" = "--" ] && shift
  if "$@" >/dev/null 2>&1; then _record pass "cmd-succeeds $label"; else _record fail "cmd-succeeds $label"; fi
}

# output-contains <file> <extended-regex> : alias of file-contains with a clearer name for captured output.
output-contains() { file-contains "$1" "$2"; }
