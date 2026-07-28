# tests/harness/lib/tests/test-runner.sh — run directly: bash tests/harness/lib/tests/test-runner.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"   # repo root (robust to depth)
RUNNER="$ROOT/tests/harness/run-harness-tests.sh"
fail=0

# bad usage → 127
bash "$RUNNER" 2>/dev/null; [ $? -eq 127 ] || { echo "FAIL: no-arg should be 127"; fail=1; }
# unknown harness → 127
bash "$RUNNER" bogus 2>/dev/null; [ $? -eq 127 ] || { echo "FAIL: bad harness should be 127"; fail=1; }
# assert.sh exposes skip() and records a skip line
out="$(bash -c 'source '"$ROOT"'/tests/harness/lib/assert.sh; skip "because"')"
echo "$out" | grep -q 'CHECK	skip	because' || { echo "FAIL: skip verb"; fail=1; }

[ $fail -eq 0 ] && echo "test-runner: PASS" || { echo "test-runner: FAIL"; exit 1; }
