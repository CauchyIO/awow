#!/usr/bin/env bash
# Driver for the harness wiring suite.
#   tests/harness/run-harness-tests.sh <claude-code|codex|pi|all> [--live]
# Sources each selected harness's wiring.sh (always) and live.sh (with --live),
# each of which defines a wiring()/live() function that calls assert verbs.
# Exit: 0 all passed, 1 an assertion failed, 127 broken invocation.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
usage() { echo "usage: run-harness-tests.sh <claude-code|codex|pi|all> [--live]" >&2; exit 127; }

[ $# -ge 1 ] || usage
target="$1"; shift || true
live=0
[ "${1:-}" = "--live" ] && live=1
case "$target" in claude-code|codex|pi) harnesses="$target" ;; all) harnesses="claude-code codex pi" ;; *) usage ;; esac

# shellcheck source=/dev/null
source "$HERE/lib/assert.sh" || { echo "broken: assert.sh failed to source" >&2; exit 127; }

HARNESS_REPO_ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
export HARNESS_REPO_ROOT

run_phase() {  # <harness> <phase: wiring|live>
  local h="$1" phase="$2" file="$HERE/$1/$2.sh"
  [ -f "$file" ] || { echo "broken: missing $file" >&2; return 127; }
  # shellcheck source=/dev/null
  source "$file" || { echo "broken: $file failed to source" >&2; return 127; }
  declare -F "$phase" >/dev/null || { echo "broken: $file defines no $phase()" >&2; return 127; }
  echo "── $h/$phase ──"
  "$phase"
}

for h in $harnesses; do
  run_phase "$h" wiring; rc=$?; [ "$rc" -eq 127 ] && exit 127
  if [ "$live" -eq 1 ]; then run_phase "$h" live; rc=$?; [ "$rc" -eq 127 ] && exit 127; fi
done

echo "────────"
[ "$_CHECK_FAILED" -eq 0 ] && { echo "all checks passed"; exit 0; } || { echo "checks failed"; exit 1; }
