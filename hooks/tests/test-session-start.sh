#!/usr/bin/env bash
# Tests for the SessionStart hook's generic overlay-reflex seam.
#
# The hook emits JSON to stdout. We drive it with a controlled REPO_DIR (via
# CLAUDE_PROJECT_DIR) and CAPTURE_LENSES, then assert on the emitted
# additionalContext. PLUGIN_ROOT is derived from the script's own location, so
# `using-awow` is read from this repo's real skill payload.

set -uo pipefail

HOOK="$(cd "$(dirname "$0")/.." && pwd)/session-start"
FIXROOT="$(mktemp -d)"
trap 'rm -rf "$FIXROOT"' EXIT

pass=0
fail=0
ok()   { printf '  ok   %s\n' "$1"; pass=$((pass+1)); }
bad()  { printf '  FAIL %s\n' "$1"; fail=$((fail+1)); }

# Run the hook for a given fixture repo. $1=repo dir, rest=env assignments.
run_hook() {
  local repo="$1"; shift
  env -i HOME="$HOME" PATH="$PATH" \
      CLAUDE_PLUGIN_ROOT="x" CLAUDE_PROJECT_DIR="$repo" \
      "$@" \
      bash "$HOOK" 2>/tmp/sshook.stderr
}

assert_contains()    { case "$1" in *"$2"*) ok "$3";; *) bad "$3";; esac; }
assert_not_contains(){ case "$1" in *"$2"*) bad "$3";; *) ok "$3";; esac; }

# A baseline fixture: adopted awow repo (suppresses the setup nudge).
mk_repo() {
  local d="$FIXROOT/$1"; mkdir -p "$d/.agents"; : > "$d/.agents/AGENTS.md"; echo "$d"
}

# ---- Case 1+2: capture fragment gated on CAPTURE_LENSES ---------------------
REPO=$(mk_repo capture)
mkdir -p "$REPO/.agents-overrides/reflex.d"
cat > "$REPO/.agents-overrides/reflex.d/capture.md" <<'EOF'
---
activate_when_env: CAPTURE_LENSES
---
CAPTURE-REFLEX-SENTINEL: lenses are active.
EOF

out=$(run_hook "$REPO" CAPTURE_LENSES="course")
assert_contains "$out" "CAPTURE-REFLEX-SENTINEL" "gated fragment injected when env set"
assert_contains "$out" "Go to the board" "using-awow reflex present (regression, env set)"
python3 -c "import json,sys; json.load(sys.stdin)" <<<"$out" && ok "valid JSON (env set)" || bad "valid JSON (env set)"

out=$(run_hook "$REPO")
assert_not_contains "$out" "CAPTURE-REFLEX-SENTINEL" "gated fragment skipped when env unset"
assert_contains "$out" "Go to the board" "using-awow reflex present (regression, env unset)"

# ---- Case 3: ungated fragment always injected ------------------------------
REPO=$(mk_repo always)
mkdir -p "$REPO/.agents/reflex.d"
printf 'ALWAYS-REFLEX-SENTINEL: no gate.\n' > "$REPO/.agents/reflex.d/always.md"
out=$(run_hook "$REPO")
assert_contains "$out" "ALWAYS-REFLEX-SENTINEL" "ungated fragment always injected"

# ---- Case 4: fragment gated on an unset var is skipped ---------------------
REPO=$(mk_repo unsetgate)
mkdir -p "$REPO/.agents-overrides/reflex.d"
cat > "$REPO/.agents-overrides/reflex.d/x.md" <<'EOF'
---
activate_when_env: SOME_VAR_THAT_IS_NOT_SET
---
UNSET-GATED-SENTINEL: should not appear.
EOF
out=$(run_hook "$REPO")
assert_not_contains "$out" "UNSET-GATED-SENTINEL" "fragment gated on unset var skipped"

# ---- Case 5: no reflex.d at all → clean no-op, valid JSON ------------------
REPO=$(mk_repo bare)
out=$(run_hook "$REPO")
assert_contains "$out" "Go to the board" "using-awow present with no reflex.d"
python3 -c "import json,sys; json.load(sys.stdin)" <<<"$out" && ok "valid JSON (no reflex.d)" || bad "valid JSON (no reflex.d)"

# ---- Case 6: malformed frontmatter → skipped, reason on stderr, exit 0 -----
REPO=$(mk_repo malformed)
mkdir -p "$REPO/.agents-overrides/reflex.d"
printf -- '---\nthis is not valid frontmatter\nMALFORMED-SENTINEL\n' > "$REPO/.agents-overrides/reflex.d/bad.md"
out=$(run_hook "$REPO"); rc=$?
[ "$rc" = 0 ] && ok "exit 0 on malformed fragment" || bad "exit 0 on malformed fragment"
python3 -c "import json,sys; json.load(sys.stdin)" <<<"$out" && ok "valid JSON (malformed)" || bad "valid JSON (malformed)"
assert_contains "$out" "Go to the board" "using-awow still present despite malformed fragment"
grep -qi "reflex" /tmp/sshook.stderr && ok "stderr explains the skip" || bad "stderr explains the skip"

echo
echo "passed=$pass failed=$fail"
[ "$fail" = 0 ]
