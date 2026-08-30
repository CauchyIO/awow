# tests/harness/claude-code/live.sh
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/gateway.sh"
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/fixture.sh"

live() {
  command -v claude >/dev/null 2>&1 || { skip "claude CLI not installed"; return 0; }
  resolve_transport || { skip "no transport resolved (set OPENROUTER_API_KEY or gateway creds)"; return 0; }

  # Claude needs an Anthropic endpoint. openrouter mode → local shim; apim mode → gateway (Task 12).
  local base token model
  if [ "$TP_MODE" = "openrouter" ]; then
    shim_start || { skip "litellm shim unavailable"; return 0; }
    base="$SHIM_BASE"; token="sk-local-noauth"; model="deepseek-flash"
  else
    base="$AWOW_GATEWAY_BASE"; token="$AWOW_GATEWAY_TOKEN"; model="$TP_MODEL"
  fi
  trap 'shim_stop' RETURN

  local fx; fx="$(mktemp -d)/repo"
  make_template_fixture "$fx" || { _record fail "template fixture build"; return 0; }
  _record pass "template fixture built"

  # Wiring signal: a successful headless turn against the model (is_error=false,
  # non-empty result) — NOT exact content, which is eval territory (spec §4).
  # `< /dev/null` because claude -p otherwise blocks waiting on stdin.
  local out; out="$(mktemp)"
  ( cd "$fx" && env -u ANTHROPIC_API_KEY \
      ANTHROPIC_BASE_URL="$base" ANTHROPIC_AUTH_TOKEN="$token" ANTHROPIC_MODEL="$model" \
      claude -p "Respond with a short greeting." --model "$model" --output-format json < /dev/null >"$out" 2>/dev/null )
  if python3 -c "import json,sys; d=json.load(open('$out')); sys.exit(0 if (not d.get('is_error') and d.get('result')) else 1)" 2>/dev/null; then
    _record pass "claude -p completed a turn against $model in the awow fixture"
  else
    _record fail "claude -p turn failed or empty"
  fi
  rm -f "$out"

  # --- anchored deploy wiring (deterministic, through the shipped hook) ---
  if [ ! -d "$HARNESS_REPO_ROOT/dist/commands" ]; then skip "dist/ payload absent (payload not built on this branch)"; return 0; fi
  cmd-succeeds "dist plugin.json valid" -- python3 -c "import json; json.load(open('$HARNESS_REPO_ROOT/dist/.claude-plugin/plugin.json'))"
  if ls "$HARNESS_REPO_ROOT"/dist/commands/*.md >/dev/null 2>&1; then _record pass "dist payload carries commands"; else _record fail "dist payload has no commands"; fi
  local anchored; anchored="$(make_anchored_fixture "$(mktemp -d)/anchored")" || { _record fail "anchored fixture build"; return 0; }
  # T1-equivalent (read path): the shipped dist hook resolves {ANCHOR} for a
  # connected anchored repo — identity from the committed connector, path from
  # the gitignored .awow/anchor.json, origin verified. No model needed.
  local anchordir tier_out
  anchordir="$(python3 -c "import json; print(json.load(open('$anchored/.awow/anchor.json'))['path'])")"
  file-exists "$anchordir/context/tooling/board.md"
  tier_out="$(mktemp)"
  ( CLAUDE_PLUGIN_ROOT="$HARNESS_REPO_ROOT/dist" CLAUDE_PROJECT_DIR="$anchored" \
      bash "$HARNESS_REPO_ROOT/dist/hooks/session-start" ) >"$tier_out" 2>/dev/null
  file-contains "$tier_out" 'resolves to'
  # T3-equivalent (fail-loud): with the link gone the hook prompts to map the
  # anchor — never a scan, never improvised conventions.
  rm -f "$anchored/.awow/anchor.json"
  ( CLAUDE_PLUGIN_ROOT="$HARNESS_REPO_ROOT/dist" CLAUDE_PROJECT_DIR="$anchored" \
      bash "$HARNESS_REPO_ROOT/dist/hooks/session-start" ) >"$tier_out" 2>/dev/null
  file-contains "$tier_out" 'not mapped on this machine'
  # Legacy regression (CAU-1415): the pre-rename spoke forms still resolve
  # through the shipped hook, silently — upgraded adopters keep working.
  local spoke; spoke="$(make_legacy_spoke_fixture "$(mktemp -d)/spoke")" || { _record fail "legacy spoke fixture build"; return 0; }
  ( CLAUDE_PLUGIN_ROOT="$HARNESS_REPO_ROOT/dist" CLAUDE_PROJECT_DIR="$spoke" \
      bash "$HARNESS_REPO_ROOT/dist/hooks/session-start" ) >"$tier_out" 2>/dev/null
  file-contains "$tier_out" 'resolves to'
  file-not-contains "$tier_out" 'deprecat'
  rm -f "$tier_out"
}
