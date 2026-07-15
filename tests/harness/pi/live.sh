# tests/harness/pi/live.sh
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/gateway.sh"
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/fixture.sh"

# WI-5: install the real awow package (package.json pi.skills) from the built dist/
# and assert Pi registers it. No model needed. `pi install -l` writes .pi/settings.json
# in the CWD and the trust store under HOME, so run fully inside temp dirs — real
# config untouched. No .ts extension: the package IS the integration (S3 decision).
_pi_install_discovery() {
  local stage work; stage="$(mktemp -d)/awow-dist"; work="$(mktemp -d)"
  cp -R "$HARNESS_REPO_ROOT/dist" "$stage" || { _record fail "stage dist/"; return 0; }
  git -C "$stage" init -q && git -C "$stage" add -A \
    && git -C "$stage" -c user.email=t@t -c user.name=t commit -qm dist >/dev/null 2>&1
  cmd-succeeds "pi install -l dist (package)" -- \
    env HOME="$work" bash -c "cd '$work' && pi install -l '$stage' --approve"
  # the package is registered project-locally
  file-contains "$work/.pi/settings.json" 'awow-dist'
  local out; out="$(mktemp)"
  ( cd "$work" && HOME="$work" pi list --approve >"$out" 2>/dev/null )
  file-contains "$out" 'Project packages'
  rm -f "$out"; rm -rf "$work" "$(dirname "$stage")"
}

# Model smoke (asserts a completed turn). gateway mode needs a models.json provider
# block (Pi ignores OPENAI_BASE_URL — see the gateway runbook), so it's OpenRouter-only for now.
_pi_turn_smoke() {
  resolve_transport || { skip "no transport resolved (model smoke)"; return 0; }
  if [ "$TP_MODE" != "openrouter" ]; then skip "pi gateway mode needs a models.json provider block (Task 12)"; return 0; fi

  local fx; fx="$(mktemp -d)/repo"
  make_template_fixture "$fx" || { _record fail "template fixture build"; return 0; }
  _record pass "template fixture built"

  # Run in the fixture with context discovery on (Pi reads AGENTS.md/CLAUDE.md — spec §7),
  # tools off for safety, ephemeral session. Assert a completed turn with assistant text.
  local out; out="$(mktemp)"
  ( cd "$fx" && pi -p --mode json --no-session --no-tools \
      --provider openrouter --model "deepseek/deepseek-v4-flash" --api-key "$(openrouter_key)" \
      "Respond with a short greeting." < /dev/null >"$out" 2>/dev/null )
  if python3 -c "
import json,sys
ok=False
for line in open('$out'):
    try: e=json.loads(line)
    except: continue
    if e.get('type')=='message_end' and e.get('message',{}).get('role')=='assistant':
        if ''.join(c.get('text','') for c in e['message'].get('content',[]) if isinstance(c,dict)).strip(): ok=True
sys.exit(0 if ok else 1)
"; then
    _record pass "pi -p completed a turn against deepseek-v4-flash in the awow fixture"
  else
    _record fail "pi -p turn produced no assistant text"
  fi
  rm -f "$out"
}

live() {
  command -v pi >/dev/null 2>&1 || { skip "pi CLI not installed"; return 0; }
  _pi_install_discovery
  _pi_turn_smoke
}
