#!/usr/bin/env bash
# Deterministic check driver for the eval suites under tests/.
#
# Usage: tests/run-checks.sh <suite> <scenario> <pre|post> <scratch-dir>
#
# Sources tests/checks-prelude.sh, then tests/<suite>/checks/<scenario>.sh
# (which must define only pre() and post()), cds into <scratch-dir>, and runs
# the requested phase. Check paths inside pre()/post() are therefore relative
# to the scratch workspace.
#
# Exit codes — the crash band is load-bearing, keep it intact:
#   0    every check in the phase passed
#   1    at least one assertion failed (a graded result)
#   127  broken invocation: bad usage, missing checks file, phase function
#        undefined, or a command inside the phase crashed. Never grade a 127
#        as a fail — it means the check itself is broken (→ indeterminate).

set -u

usage() { echo "usage: run-checks.sh <suite> <scenario> <pre|post> <scratch-dir>" >&2; exit 127; }

[ $# -eq 4 ] || usage
suite="$1"
scenario="$2"
phase="$3"
scratch="$4"

case "$phase" in pre|post) ;; *) usage ;; esac

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
prelude="$HERE/checks-prelude.sh"
checks_file="$HERE/$suite/checks/$scenario.sh"

[ -f "$prelude" ] || { echo "broken: missing prelude at $prelude" >&2; exit 127; }
[ -f "$checks_file" ] || { echo "broken: missing checks file at $checks_file" >&2; exit 127; }
[ -d "$scratch" ] || { echo "broken: scratch dir does not exist: $scratch" >&2; exit 127; }

# shellcheck source=/dev/null
source "$prelude" || { echo "broken: prelude failed to source" >&2; exit 127; }
# shellcheck source=/dev/null
source "$checks_file" || { echo "broken: checks file failed to source" >&2; exit 127; }

declare -F "$phase" >/dev/null || { echo "broken: $checks_file defines no $phase()" >&2; exit 127; }

cd "$scratch" || { echo "broken: cannot cd into $scratch" >&2; exit 127; }

"$phase"
rc=$?
# Verbs always return 0, so a non-zero function return means a stray command
# inside the phase crashed — that is a broken check, not an assertion failure.
[ "$rc" -eq 0 ] || { echo "broken: phase $phase exited $rc" >&2; exit 127; }

[ "$_CHECK_FAILED" -eq 0 ] || exit 1
exit 0
