# tests/harness/lib/tests/test-fixture.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
# shellcheck source=/dev/null
source "$ROOT/tests/harness/lib/fixture.sh"
fail=0
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

make_template_fixture "$tmp/repo" || { echo "FAIL: template fixture build"; fail=1; }
[ -f "$tmp/repo/.claude/CLAUDE.md" ] || { echo "FAIL: gather did not run in fixture"; fail=1; }
[ -d "$tmp/repo/.git" ] || { echo "FAIL: fixture not a git repo"; fail=1; }

make_spoke_fixture "$tmp/spoke" >/dev/null || { echo "FAIL: spoke fixture build"; fail=1; }
grep -q 'hub:' "$tmp/spoke/AGENTS.md" 2>/dev/null || { echo "FAIL: spoke AGENTS.md missing hub"; fail=1; }

[ $fail -eq 0 ] && echo "test-fixture: PASS" || { echo "test-fixture: FAIL"; exit 1; }
