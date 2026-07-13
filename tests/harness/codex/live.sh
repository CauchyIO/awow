# tests/harness/codex/live.sh
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/gateway.sh"
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/fixture.sh"

# Stage the built dist/ as its OWN git repo — codex git-clones the marketplace
# source, so a bare subdir won't install. This mirrors exactly what
# tools/sync-dist.sh publishes to CauchyIO/awow-dist. Echoes the staged repo path.
_stage_dist_repo() {
  local stage; stage="$(mktemp -d)/awow-dist"
  cp -R "$HARNESS_REPO_ROOT/dist" "$stage" || return 1
  git -C "$stage" init -q \
    && git -C "$stage" add -A \
    && git -C "$stage" -c user.email=t@t -c user.name=t commit -qm dist >/dev/null 2>&1 || return 1
  printf '%s' "$stage"
}

# WI-5: install the real awow plugin from the built dist/ marketplace and assert an
# awow flow is discoverable. No model needed. Isolated CODEX_HOME — real config untouched.
_codex_install_discovery() {
  local stage ch; stage="$(_stage_dist_repo)" || { _record fail "stage dist/ as git repo"; return 0; }
  ch="$(mktemp -d)"
  cmd-succeeds "codex marketplace add dist/"   -- env CODEX_HOME="$ch" codex plugin marketplace add "$stage"
  cmd-succeeds "codex plugin add awow@awow"    -- env CODEX_HOME="$ch" codex plugin add awow@awow
  local out; out="$(mktemp)"
  CODEX_HOME="$ch" codex plugin list >"$out" 2>/dev/null
  file-contains "$out" 'awow@awow[[:space:]]+installed'
  # the setup-awow flow ships inside the installed plugin (commands-as-skills surface)
  cmd-succeeds "installed plugin carries the setup-awow skill" -- \
    bash -c "find '$ch' -path '*agent-skills/setup-awow/SKILL.md' | grep -q ."
  rm -f "$out"; rm -rf "$ch" "$(dirname "$stage")"
}

# Model smoke against the gateway/APIM transport (or OpenRouter). Asserts a turn
# completes; needs a resolved transport, else skips.
_codex_turn_smoke() {
  resolve_transport || { skip "no transport resolved (model smoke)"; return 0; }
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
}

live() {
  command -v codex >/dev/null 2>&1 || { skip "codex CLI not installed"; return 0; }
  _codex_install_discovery
  _codex_turn_smoke
}
