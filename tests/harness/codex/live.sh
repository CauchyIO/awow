# tests/harness/codex/live.sh
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/gateway.sh"
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/fixture.sh"

live() {
  command -v codex >/dev/null 2>&1 || { skip "codex CLI not installed"; return 0; }
  resolve_transport || { skip "no transport resolved"; return 0; }

  local base key
  if [ "$TP_MODE" = "openrouter" ]; then base="https://openrouter.ai/api/v1"; key="$(openrouter_key)"
  else base="$TP_OPENAI_BASE"; key="$TP_OPENAI_AUTH"; fi

  local fx; fx="$(mktemp -d)/repo"
  make_template_fixture "$fx" || { _record fail "template fixture build"; return 0; }
  _record pass "template fixture built"

  # `< /dev/null` because codex exec otherwise blocks reading stdin. read-only
  # sandbox + ignore-user-config keep the run reproducible and safe.
  local out; out="$(mktemp)"
  OPENROUTER_API_KEY="$key" codex exec \
    -C "$fx" -s read-only --skip-git-repo-check --ignore-user-config --json \
    -c model_providers.awow.name=awow \
    -c "model_providers.awow.base_url=\"$base\"" \
    -c model_providers.awow.env_key=OPENROUTER_API_KEY \
    -c 'model_providers.awow.wire_api="responses"' \
    -c model_provider=awow -m "$TP_MODEL" \
    "Respond with a short greeting." < /dev/null > "$out" 2>/dev/null
  if grep -q '"type":"turn.completed"' "$out"; then
    _record pass "codex exec completed a turn against $TP_MODEL in the awow fixture"
  elif grep -q 'No endpoints found that support' "$out"; then
    # codex 0.144 requires the Responses API and advertises namespace-format tools;
    # deepseek-v4-flash's OpenRouter endpoints reject that tool type (verified 2026-07-13).
    skip "codex 0.144 Responses-API tools incompatible with $TP_MODEL on OpenRouter; needs a tool-capable model or the APIM tier"
  else
    _record fail "codex exec turn failed unexpectedly (see run output)"
  fi
  rm -f "$out"

  skip "codex hub-spoke deploy: awaits hub-spoke WI-5 (.codex-plugin manifest)"
}
