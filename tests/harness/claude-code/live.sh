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
}
