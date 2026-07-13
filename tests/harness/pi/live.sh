# tests/harness/pi/live.sh
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/gateway.sh"
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/fixture.sh"

live() {
  command -v pi >/dev/null 2>&1 || { skip "pi CLI not installed"; return 0; }
  resolve_transport || { skip "no transport resolved"; return 0; }
  # apim mode needs a models.json provider block (Pi ignores OPENAI_BASE_URL — runbook §3).
  if [ "$TP_MODE" != "openrouter" ]; then skip "pi apim mode needs a models.json provider block (Task 12)"; return 0; fi

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

  skip "pi hub-spoke deploy: awaits hub-spoke WI-5 (.pi extension)"
}
