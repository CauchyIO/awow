# tests/harness/opencode/live.sh
#
# Drives the real opencode binary through its headless server API. No model is
# needed: /command and /skill report what the harness discovered, which is
# exactly what this surface is responsible for. Verified against opencode 1.15.2.

# Start `opencode serve` in <dir>, poll until it answers, echo the port.
# Sets _OC_PID for the caller to kill.
_oc_serve() {  # <dir> <port>
  local dir="$1" port="$2" i code
  # disown so the later pkill does not print a job-control "Terminated" line
  # into the check output.
  ( cd "$dir" && exec opencode serve --port "$port" --hostname 127.0.0.1 ) >/dev/null 2>&1 &
  disown 2>/dev/null || true
  # curl returns immediately on connection-refused, so the sleep is load-bearing:
  # without it the whole loop burns in under a second while opencode is still
  # booting, and a healthy server reads as "never ready". ~60s of patience.
  for i in $(seq 1 60); do
    code="$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:$port/config" 2>/dev/null)"
    [ "$code" = "200" ] && return 0
    sleep 1
  done
  return 1
}

_oc_kill() { pkill -f "opencode serve --port $1" >/dev/null 2>&1 || true; }

# The payload, exercised in the shape an install actually produces: dist/ IS
# the published package, so running opencode inside a copy of it puts the plugin
# at .opencode/plugins/ with PACKAGE_ROOT resolving to the payload root. The copy
# deliberately has no root AGENTS.md — that is the global-install case the
# bootstrap exists for.
_oc_plugin_registers_skills() {
  local port=39142 stage out
  stage="$(mktemp -d)/awow-pkg"; out="$(mktemp)"
  cp -R "$HARNESS_REPO_ROOT/dist" "$stage" || { _record fail "stage dist/"; return 0; }
  file-absent "$stage/AGENTS.md"

  _oc_serve "$stage" "$port" || { _record fail "opencode serve (payload) did not become ready"; _oc_kill "$port"; rm -rf "$(dirname "$stage")"; return 0; }
  curl -s -m 10 -o "$out" "http://127.0.0.1:$port/config" 2>/dev/null
  cmd-succeeds "plugin config hook registers agent-skills" -- python3 -c "
import json, sys
paths = (json.load(open('$out')).get('skills') or {}).get('paths') or []
sys.exit(0 if any(p.endswith('awow-pkg/agent-skills') for p in paths) else 1)"

  curl -s -m 10 -o "$out" "http://127.0.0.1:$port/skill" 2>/dev/null
  _oc_kill "$port"
  cmd-succeeds "opencode discovers awow skills through the plugin" -- python3 -c "
import json, sys
d = json.load(open('$out'))
awow = [s for s in d if 'awow-pkg/agent-skills' in (s.get('location') or '')]
sys.exit(0 if len(awow) >= 20 and any(s['name'] == 'using-awow' for s in awow) else 1)"

  rm -f "$out"; rm -rf "$(dirname "$stage")"
}

# The plugin's own hooks, unit-style: cheaper and more precise than inferring
# them from server state, and it covers the double-injection guard the server
# cannot show without a model turn.
_oc_plugin_hooks() {
  local js="$HARNESS_REPO_ROOT/dist/.opencode/plugins/awow.js" t
  t="$(mktemp -d)/t.mjs"
  cat >"$t" <<EOF
import { AwowPlugin } from '$js';
const p = await AwowPlugin({});
const cfg = {};
await p.config(cfg); await p.config(cfg);
if (cfg.skills.paths.length !== 1) process.exit(1);           // idempotent
const out = { messages: [{ info: { role: 'user' }, parts: [{ type: 'text', text: 'hi' }] }] };
const tr = p['experimental.chat.messages.transform'];
await tr({}, out);
const txt = out.messages[0].parts[0].text;
if (!txt.startsWith('<awow-operating-reflex>')) process.exit(1);
if (txt.includes('description:')) process.exit(1);            // frontmatter stripped
if (!txt.includes('todowrite')) process.exit(1);              // tool mapping present
await tr({}, out);
if (out.messages[0].parts.length !== 2) process.exit(1);      // no double injection
EOF
  cmd-succeeds "plugin hooks: skills path idempotent, bootstrap injected once" -- node "$t"
  rm -rf "$(dirname "$t")"
}

live() {
  command -v opencode >/dev/null 2>&1 || { skip "opencode CLI not installed"; return 0; }
  command -v node >/dev/null 2>&1 || { skip "node not installed"; return 0; }
  _oc_plugin_registers_skills
  _oc_plugin_hooks
}
