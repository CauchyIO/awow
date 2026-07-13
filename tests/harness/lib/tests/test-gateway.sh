# tests/harness/lib/tests/test-gateway.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
GW="$ROOT/tests/harness/lib/gateway.sh"
fail=0

# 1) apim wins when base + token present
( AWOW_GATEWAY_BASE="https://x/litellm" AWOW_GATEWAY_TOKEN="tok" OPENROUTER_API_KEY="k" \
  bash -c 'source '"$GW"'; resolve_transport && echo "$TP_MODE $TP_MODEL"' ) \
  | grep -q '^apim worker$' || { echo "FAIL: apim not preferred"; fail=1; }

# 2) openrouter when only the key is present
( env -u AWOW_GATEWAY_BASE -u AWOW_GATEWAY_TOKEN OPENROUTER_API_KEY="k" \
  bash -c 'source '"$GW"'; resolve_transport && echo "$TP_MODE $TP_MODEL"' ) \
  | grep -q '^openrouter deepseek/deepseek-v4-flash$' || { echo "FAIL: openrouter fallback"; fail=1; }

# 3) neither → return 1, no crash (force empty key + no keychain probe)
( env -u AWOW_GATEWAY_BASE -u AWOW_GATEWAY_TOKEN -u OPENROUTER_API_KEY AWOW_NO_KEYCHAIN=1 \
  bash -c 'source '"$GW"'; resolve_transport; echo "rc=$?"' ) \
  | grep -q 'rc=1' || { echo "FAIL: no-transport should return 1"; fail=1; }

[ $fail -eq 0 ] && echo "test-gateway: PASS" || { echo "test-gateway: FAIL"; exit 1; }
