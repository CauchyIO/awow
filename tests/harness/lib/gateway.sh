# tests/harness/lib/gateway.sh — sourced. Resolves the transport for live runs.
# Commits nothing: every value is env/keychain-sourced. AWOW_NO_KEYCHAIN=1 disables
# the keychain probe (used by tests and by CI where no keychain exists).

openrouter_key() {
  if [ -n "${OPENROUTER_API_KEY:-}" ]; then printf '%s' "$OPENROUTER_API_KEY"; return 0; fi
  if [ "${AWOW_NO_KEYCHAIN:-0}" != "1" ] && command -v security >/dev/null 2>&1; then
    security find-generic-password -l OPENROUTER_API_KEY -w 2>/dev/null | tr -d '\n'
  fi
}

resolve_transport() {
  TP_MODE=""; TP_MODEL=""; TP_OPENAI_BASE=""; TP_OPENAI_AUTH=""
  local have_sp=0
  [ -n "${AWOW_SP_CLIENT_ID:-}" ] && [ -n "${AWOW_SP_CLIENT_SECRET:-}" ] && [ -n "${AWOW_SP_TENANT:-}" ] && have_sp=1
  if [ -n "${AWOW_GATEWAY_BASE:-}" ] && { [ -n "${AWOW_GATEWAY_TOKEN:-}" ] || [ "$have_sp" = 1 ]; }; then
    TP_MODE="apim"; TP_MODEL="${AWOW_GATEWAY_TIER:-worker}"
    TP_OPENAI_BASE="${AWOW_GATEWAY_BASE%/}/v1"
    TP_OPENAI_AUTH="${AWOW_GATEWAY_TOKEN:-}"        # SPN-mint path filled by apim_mint_token (Task 12)
    return 0
  fi
  if [ -n "$(openrouter_key)" ]; then
    TP_MODE="openrouter"; TP_MODEL="deepseek/deepseek-v4-flash"; return 0
  fi
  return 1
}

# --- openrouter mode: box-local litellm Anthropic shim for Claude Code ---
shim_start() {  # echoes base URL; sets SHIM_PID; returns 1 if litellm missing
  command -v litellm >/dev/null 2>&1 || return 1
  local port="${AWOW_SHIM_PORT:-4111}" dir; dir="$(mktemp -d)"
  cat > "$dir/config.yaml" <<YAML
model_list:
  - model_name: deepseek-flash
    litellm_params:
      model: openrouter/deepseek/deepseek-v4-flash
      api_key: os.environ/OPENROUTER_API_KEY
litellm_settings:
  drop_params: true
YAML
  OPENROUTER_API_KEY="$(openrouter_key)" litellm --config "$dir/config.yaml" --port "$port" \
    > "$dir/litellm.log" 2>&1 &
  SHIM_PID=$!
  # wait for readiness without sleep
  curl -s --retry 20 --retry-delay 2 --retry-connrefused --retry-all-errors --max-time 90 \
    "http://127.0.0.1:$port/v1/models" >/dev/null 2>&1 || { kill "$SHIM_PID" 2>/dev/null; return 1; }
  printf 'http://127.0.0.1:%s' "$port"
}

shim_stop() { [ -n "${SHIM_PID:-}" ] && kill "$SHIM_PID" 2>/dev/null; SHIM_PID=""; return 0; }
