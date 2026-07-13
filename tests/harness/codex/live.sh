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

  # Disable codex's tool/app/plugin/exec features. codex 0.144 otherwise advertises a
  # `namespace` tool type that deepseek-v4-flash's OpenRouter endpoints reject (verified
  # 2026-07-13). A wiring smoke needs no tools — we assert the harness completes a turn,
  # not that it acts. `< /dev/null` because codex exec otherwise blocks reading stdin.
  local dis="" f
  for f in browser_use computer_use image_generation apps multi_agent plugins tool_suggest \
           unified_exec shell_tool code_mode_host in_app_browser tool_call_mcp_elicitation \
           remote_plugin plugin_sharing skill_mcp_dependency_install; do dis="$dis --disable $f"; done

  local out; out="$(mktemp)"
  OPENROUTER_API_KEY="$key" codex exec $dis \
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
    skip "codex tool format still unsupported for $TP_MODEL on OpenRouter even with tools disabled; needs a tool-capable model"
  else
    _record fail "codex exec turn failed unexpectedly (see run output)"
  fi
  rm -f "$out"

  skip "codex hub-spoke deploy: awaits hub-spoke WI-5 (.codex-plugin manifest)"
}
