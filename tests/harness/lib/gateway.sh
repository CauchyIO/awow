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
    TP_OPENAI_AUTH="$(apim_mint_token)"; [ -n "$TP_OPENAI_AUTH" ] || return 1
    return 0
  fi
  if [ -n "$(openrouter_key)" ]; then
    TP_MODE="openrouter"; TP_MODEL="deepseek/deepseek-v4-flash"; return 0
  fi
  return 1
}

# --- openrouter mode: box-local litellm Anthropic shim for Claude Code ---
# Sets globals SHIM_BASE + SHIM_PID (NOT echoed) so the PID survives — callers
# must invoke `shim_start` directly, never as `$(shim_start)` (a command-sub
# subshell would lose SHIM_PID and orphan the litellm process). Returns 1 if
# litellm is missing or the shim never becomes ready.
shim_start() {
  SHIM_BASE=""; SHIM_PID=""
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
    "http://127.0.0.1:$port/v1/models" >/dev/null 2>&1 || { kill "$SHIM_PID" 2>/dev/null; SHIM_PID=""; return 1; }
  SHIM_BASE="http://127.0.0.1:$port"
}

shim_stop() {
  # litellm forks a uvicorn worker, so killing the launcher PID alone leaves the
  # port held. Kill children + launcher, then free the port as a backstop.
  if [ -n "${SHIM_PID:-}" ]; then
    pkill -P "$SHIM_PID" 2>/dev/null; kill "$SHIM_PID" 2>/dev/null
    wait "$SHIM_PID" 2>/dev/null   # reap synchronously so no async "Terminated" notice leaks
  fi
  local port="${AWOW_SHIM_PORT:-4111}" pids
  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti "tcp:$port" 2>/dev/null)"; [ -n "$pids" ] && kill $pids 2>/dev/null
  fi
  SHIM_PID=""; return 0
}

# --- gateway mode: obtain an OIDC bearer token for a self-hosted OpenAI-compatible gateway ---
# Auth model: see your team's private gateway auth runbook.
# Precedence: an explicit token, else an OIDC client-credentials mint from the credentials triple.
# Nothing is committed — every value is env-supplied; the scope uses .default.
apim_mint_token() {
  if [ -n "${AWOW_GATEWAY_TOKEN:-}" ]; then printf '%s' "$AWOW_GATEWAY_TOKEN"; return 0; fi
  [ -n "${AWOW_SP_CLIENT_ID:-}" ] && [ -n "${AWOW_SP_CLIENT_SECRET:-}" ] && [ -n "${AWOW_SP_TENANT:-}" ] && [ -n "${AWOW_GATEWAY_AUD:-}" ] || return 1
  curl -s -X POST "https://login.microsoftonline.com/$AWOW_SP_TENANT/oauth2/v2.0/token" \
    -d grant_type=client_credentials -d client_id="$AWOW_SP_CLIENT_ID" \
    -d client_secret="$AWOW_SP_CLIENT_SECRET" -d scope="api://$AWOW_GATEWAY_AUD/.default" \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))"
}
