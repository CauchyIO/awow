# Harness Wiring Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A per-harness (Claude Code / Codex / Pi) headless test suite that proves awow's setup + hub-spoke wiring is correctly generated (deterministic, CI-safe) and — opt-in — actually runs against `deepseek-v4-flash`.

**Architecture:** Two layers under `tests/harness/`, mirroring superpowers' `tests/` vs `evals/` split. Layer 1 = deterministic wiring checks (no model, runs in CI). Layer 2 = opt-in `--live` smoke that drives each real CLI headless through a credential-resolved gateway. A shared `lib/` (transport resolver, fixture builder, assertion verbs) backs all three harnesses; one `run-harness-tests.sh` driver dispatches and owns the exit-code discipline.

**Tech Stack:** Bash (matches awow's `tests/` infra and superpowers' harness tests), the three CLIs (`claude`, `codex`, `pi`), `litellm` (local Anthropic shim for Claude in `openrouter` mode), `az`/`curl`/`python3`/`jq` for transport, `deepseek-v4-flash` via OpenRouter or the APIM `worker` tier.

## Global Constraints

- **Public repo — commit nothing private.** No gateway base URL, tenant/audience GUIDs, virtual keys, or OpenRouter key in the tree. All operator-supplied from env/keychain/`az`; fail loud if unset. The `tools/hooks/pre-push` leak scan backstops it.
- **Reuse the existing check contract.** Source `tests/checks-prelude.sh`; every assertion emits one `CHECK\t(pass|fail|skip)\t<verb args>` line. Exit codes: `0` all passed, `1` an assertion failed, `127` broken invocation (never grade a 127 as fail).
- **SKIP, never fail, on absence.** A missing CLI, unresolvable gateway, or not-yet-built manifest records `skip` and does not fail the run.
- **Sandbox every live run.** Codex `-s read-only`; Pi `--no-tools` (or an explicit `--tools` allowlist) + `--no-session`; Claude in a scratch working dir. Scratch fixtures only, under `$TMPDIR`.
- **Model = `deepseek-v4-flash`** (OpenRouter slug `deepseek/deepseek-v4-flash`; APIM tier alias `worker`). It is a **reasoning model** — responses carry a `thinking` block plus a `text` block; live assertions must budget `max_tokens` ≥ 256 and read the `text` block, never assert on empty text under a tiny budget.
- **Transport is credential-resolved.** Prefer `apim` when a `MeshService`/`NightRunner` Entra token or SPN creds are present; else `openrouter` (keychain `OPENROUTER_API_KEY`). Auth model: linear `context/knowledge-base/architecture/apim-litellm-gateway-auth-model.md` + runbook `.../runbooks/call-litellm-via-apim.md`.
- **Branch:** `feat/harness-wiring-tests` (off `main`). Commit after every task.
- Spec: `meta/proposals/harness-wiring-test-suite.md`.

---

## File Structure

```
tests/harness/
├── run-harness-tests.sh        # driver: <claude-code|codex|pi|all> [--live]; dispatches, aggregates, exits 0/1/127
├── README.md                   # how to run, credential setup (no secrets)
├── lib/
│   ├── assert.sh               # source checks-prelude.sh + add: skip(), cmd-succeeds(), output-contains()
│   ├── gateway.sh              # resolve_transport(); shim_start()/shim_stop() for openrouter+claude
│   └── fixture.sh              # make_template_fixture(); make_spoke_fixture()
├── lib/tests/
│   ├── test-gateway.sh         # resolver order + fail-loud (no network)
│   └── test-fixture.sh         # fixture structure
├── claude-code/
│   ├── wiring.sh               # Layer-1 deterministic checks
│   └── live.sh                 # Layer-2: setup-wiring + hub-spoke-deploy
├── codex/
│   ├── wiring.sh
│   └── live.sh
└── pi/
    ├── wiring.sh
    └── live.sh
```

CI: one added step in `.github/workflows/ci.yml` runs `run-harness-tests.sh all` (Layer 1 only, no `--live`).

---

## Task 1: Runner skeleton + assertion library

**Files:**
- Create: `tests/harness/lib/assert.sh`
- Create: `tests/harness/run-harness-tests.sh`
- Test: `tests/harness/lib/tests/test-runner.sh`

**Interfaces:**
- Produces: `assert.sh` sourced by every check file — exposes `checks-prelude.sh` verbs plus `skip <reason>`, `cmd-succeeds <cmd...>`, `output-contains <file> <regex>`. `run-harness-tests.sh <harness|all> [--live]` sources `assert.sh`, runs each selected harness's `wiring.sh` (always) and `live.sh` (only with `--live`) as sourced files defining `wiring()` / `live()`, tallies `_CHECK_FAILED`, prints a summary, exits `0|1|127`.

- [ ] **Step 1: Write the failing test**

```bash
# tests/harness/lib/tests/test-runner.sh — run directly: bash tests/harness/lib/tests/test-runner.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"          # repo root
RUNNER="$ROOT/tests/harness/run-harness-tests.sh"
fail=0

# bad usage → 127
bash "$RUNNER" 2>/dev/null; [ $? -eq 127 ] || { echo "FAIL: no-arg should be 127"; fail=1; }
# unknown harness → 127
bash "$RUNNER" bogus 2>/dev/null; [ $? -eq 127 ] || { echo "FAIL: bad harness should be 127"; fail=1; }
# assert.sh exposes skip() and records a skip line
out="$(bash -c 'source '"$ROOT"'/tests/harness/lib/assert.sh; skip "because"')"
echo "$out" | grep -q 'CHECK	skip	because' || { echo "FAIL: skip verb"; fail=1; }

[ $fail -eq 0 ] && echo "test-runner: PASS" || { echo "test-runner: FAIL"; exit 1; }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/harness/lib/tests/test-runner.sh`
Expected: FAIL — `run-harness-tests.sh` and `assert.sh` do not exist yet (`bash: ...: No such file or directory`).

- [ ] **Step 3: Write `assert.sh`**

```bash
# tests/harness/lib/assert.sh — sourced, never executed.
# Extends the shared check prelude with a skip verb and command/output verbs.
_ASSERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$_ASSERT_DIR/../../checks-prelude.sh"

# skip <reason...> — records a non-failing CHECK line (absence is not failure).
skip() { printf 'CHECK\tskip\t%s\n' "$*"; return 0; }

# cmd-succeeds <label> -- <cmd...> : run cmd, record pass iff exit 0.
cmd-succeeds() {
  local label="$1"; shift; [ "$1" = "--" ] && shift
  if "$@" >/dev/null 2>&1; then _record pass "cmd-succeeds $label"; else _record fail "cmd-succeeds $label"; fi
}

# output-contains <file> <extended-regex> : alias of file-contains with a clearer name for captured output.
output-contains() { file-contains "$1" "$2"; }
```

- [ ] **Step 4: Write `run-harness-tests.sh`**

```bash
#!/usr/bin/env bash
# Driver for the harness wiring suite.
#   tests/harness/run-harness-tests.sh <claude-code|codex|pi|all> [--live]
# Sources each selected harness's wiring.sh (always) and live.sh (with --live),
# each of which defines a wiring()/live() function that calls assert verbs.
# Exit: 0 all passed, 1 an assertion failed, 127 broken invocation.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
usage() { echo "usage: run-harness-tests.sh <claude-code|codex|pi|all> [--live]" >&2; exit 127; }

[ $# -ge 1 ] || usage
target="$1"; shift || true
live=0
[ "${1:-}" = "--live" ] && live=1
case "$target" in claude-code|codex|pi) harnesses="$target" ;; all) harnesses="claude-code codex pi" ;; *) usage ;; esac

# shellcheck source=/dev/null
source "$HERE/lib/assert.sh" || { echo "broken: assert.sh failed to source" >&2; exit 127; }

run_phase() {  # <harness> <phase: wiring|live>
  local h="$1" phase="$2" file="$HERE/$1/$2.sh"
  [ -f "$file" ] || { echo "broken: missing $file" >&2; return 127; }
  # shellcheck source=/dev/null
  source "$file" || { echo "broken: $file failed to source" >&2; return 127; }
  declare -F "$phase" >/dev/null || { echo "broken: $file defines no $phase()" >&2; return 127; }
  echo "── $h/$phase ──"
  "$phase"
}

for h in $harnesses; do
  run_phase "$h" wiring; rc=$?; [ "$rc" -eq 127 ] && exit 127
  if [ "$live" -eq 1 ]; then run_phase "$h" live; rc=$?; [ "$rc" -eq 127 ] && exit 127; fi
done

echo "────────"
[ "$_CHECK_FAILED" -eq 0 ] && { echo "all checks passed"; exit 0; } || { echo "checks failed"; exit 1; }
```

Then create placeholder phase files so the runner has something to source (real checks land in later tasks):

```bash
# tests/harness/claude-code/wiring.sh  (and codex/, pi/ — identical placeholder)
wiring() { skip "wiring checks not yet implemented"; }
# tests/harness/claude-code/live.sh    (and codex/, pi/ — identical placeholder)
live() { skip "live checks not yet implemented"; }
```

```bash
chmod +x tests/harness/run-harness-tests.sh
mkdir -p tests/harness/{claude-code,codex,pi} tests/harness/lib/tests
```

- [ ] **Step 5: Run test to verify it passes**

Run: `bash tests/harness/lib/tests/test-runner.sh && bash tests/harness/run-harness-tests.sh all`
Expected: `test-runner: PASS`, then the runner prints skip lines for all three harnesses and `all checks passed` (exit 0).

- [ ] **Step 6: Commit**

```bash
git add tests/harness/
git commit -m "test(harness): runner skeleton + assertion library"
```

---

## Task 2: Transport resolver (`gateway.sh`)

**Files:**
- Create: `tests/harness/lib/gateway.sh`
- Test: `tests/harness/lib/tests/test-gateway.sh`

**Interfaces:**
- Produces:
  - `resolve_transport()` — inspects env/keychain and sets, on success, `TP_MODE` (`apim|openrouter`), `TP_MODEL` (`worker` for apim, `deepseek/deepseek-v4-flash` for openrouter), and (apim only) `TP_OPENAI_BASE`+`TP_OPENAI_AUTH`. Returns `0` if a transport resolved, `1` if none (caller SKIPs). Resolution order: `apim` when `$AWOW_GATEWAY_BASE` **and** (`$AWOW_GATEWAY_TOKEN` or SPN triple `$AWOW_SP_CLIENT_ID`/`$AWOW_SP_CLIENT_SECRET`/`$AWOW_SP_TENANT`) are set; else `openrouter` when the keychain key or `$OPENROUTER_API_KEY` resolves; else return 1.
  - `openrouter_key()` — echoes the key from `$OPENROUTER_API_KEY` or `security find-generic-password -l OPENROUTER_API_KEY -w`; empty if neither.
  - `shim_start()` / `shim_stop()` — start/stop a box-local litellm Anthropic shim for `openrouter` mode; `shim_start` echoes the base URL (e.g. `http://127.0.0.1:$port`) and sets `SHIM_PID`. No-op error (return 1) if `litellm` is absent.

- [ ] **Step 1: Write the failing test** (no network — env-driven resolution + fail-loud only)

```bash
# tests/harness/lib/tests/test-gateway.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/tests/harness/lib/gateway.sh"
fail=0

# 1) apim wins when base + token present
( AWOW_GATEWAY_BASE="https://x/litellm" AWOW_GATEWAY_TOKEN="tok" OPENROUTER_API_KEY="k" \
  bash -c 'source '"$ROOT"'/tests/harness/lib/gateway.sh; resolve_transport && echo "$TP_MODE $TP_MODEL"' ) \
  | grep -q '^apim worker$' || { echo "FAIL: apim not preferred"; fail=1; }

# 2) openrouter when only the key is present
( env -u AWOW_GATEWAY_BASE -u AWOW_GATEWAY_TOKEN OPENROUTER_API_KEY="k" \
  bash -c 'source '"$ROOT"'/tests/harness/lib/gateway.sh; resolve_transport && echo "$TP_MODE $TP_MODEL"' ) \
  | grep -q '^openrouter deepseek/deepseek-v4-flash$' || { echo "FAIL: openrouter fallback"; fail=1; }

# 3) neither → return 1, no crash (simulate no keychain by forcing empty)
( env -u AWOW_GATEWAY_BASE -u AWOW_GATEWAY_TOKEN -u OPENROUTER_API_KEY AWOW_NO_KEYCHAIN=1 \
  bash -c 'source '"$ROOT"'/tests/harness/lib/gateway.sh; resolve_transport; echo "rc=$?"' ) \
  | grep -q 'rc=1' || { echo "FAIL: no-transport should return 1"; fail=1; }

[ $fail -eq 0 ] && echo "test-gateway: PASS" || { echo "test-gateway: FAIL"; exit 1; }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/harness/lib/tests/test-gateway.sh`
Expected: FAIL — `gateway.sh` does not exist.

- [ ] **Step 3: Write `gateway.sh`**

```bash
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/harness/lib/tests/test-gateway.sh`
Expected: `test-gateway: PASS`.

- [ ] **Step 5: Commit**

```bash
git add tests/harness/lib/gateway.sh tests/harness/lib/tests/test-gateway.sh
git commit -m "test(harness): credential-resolved transport + litellm shim helper"
```

---

## Task 3: Fixture builder (`fixture.sh`)

**Files:**
- Create: `tests/harness/lib/fixture.sh`
- Test: `tests/harness/lib/tests/test-fixture.sh`

**Interfaces:**
- Produces:
  - `make_template_fixture <dir>` — populates `<dir>` as a scratch git repo with awow vendored in: copies `.agents/`, `tools/`, `setup/`, `context/` from `$REPO_ROOT`, runs `python tools/gather.py` inside it, `git init`+commit. Echoes nothing; returns non-zero on failure.
  - `make_spoke_fixture <dir>` — populates `<dir>` as a thin spoke: a committed root `AGENTS.md` naming `hub: <hubdir> project: fixture`, `context/mission.md`, `context/board-scope.md`; plus a sibling `<dir>.hub` bare-ish hub clone with a minimal `context/tooling/board.md`. Echoes the spoke dir.
  - Both take `REPO_ROOT` from `${AWOW_REPO_ROOT:-$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)}`.

- [ ] **Step 1: Write the failing test**

```bash
# tests/harness/lib/tests/test-fixture.sh
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
# shellcheck source=/dev/null
source "$ROOT/tests/harness/lib/fixture.sh"
fail=0
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

make_template_fixture "$tmp/repo" || { echo "FAIL: template fixture build"; fail=1; }
[ -f "$tmp/repo/.claude/CLAUDE.md" ] || { echo "FAIL: gather did not run in fixture"; fail=1; }
[ -d "$tmp/repo/.git" ] || { echo "FAIL: fixture not a git repo"; fail=1; }

make_spoke_fixture "$tmp/spoke" >/dev/null || { echo "FAIL: spoke fixture build"; fail=1; }
grep -q 'hub:' "$tmp/spoke/AGENTS.md" 2>/dev/null || { echo "FAIL: spoke AGENTS.md missing hub"; fail=1; }

[ $fail -eq 0 ] && echo "test-fixture: PASS" || { echo "test-fixture: FAIL"; exit 1; }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/harness/lib/tests/test-fixture.sh`
Expected: FAIL — `fixture.sh` missing.

- [ ] **Step 3: Write `fixture.sh`**

```bash
# tests/harness/lib/fixture.sh — sourced. Builds scratch fixtures under $TMPDIR.
_fx_root() { printf '%s' "${AWOW_REPO_ROOT:-$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)}"; }

make_template_fixture() {  # <dir>
  local dir="$1" root; root="$(_fx_root)"; mkdir -p "$dir" || return 1
  local d; for d in .agents tools setup context .claude-plugin commands hooks; do
    [ -e "$root/$d" ] && cp -R "$root/$d" "$dir/" 2>/dev/null
  done
  ( cd "$dir" && AWOW_REPO_ROOT="$dir" python3 tools/gather.py >/dev/null 2>&1 ) || return 1
  ( cd "$dir" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm fixture ) || return 1
}

make_spoke_fixture() {  # <dir> ; echoes <dir>
  local dir="$1" hub="$1.hub"
  mkdir -p "$dir/context" "$hub/context/tooling" || return 1
  cat > "$dir/AGENTS.md" <<EOF
---
hub: $hub
project: fixture
---
This repo follows awow; hub is named above.
EOF
  printf 'fixture project\n' > "$dir/context/mission.md"
  printf 'team: fixture\nproject: fixture\n' > "$dir/context/board-scope.md"
  printf 'board: none (fixture)\n' > "$hub/context/tooling/board.md"
  ( cd "$dir" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm spoke ) || return 1
  ( cd "$hub" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm hub ) || return 1
  printf '%s' "$dir"
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/harness/lib/tests/test-fixture.sh`
Expected: `test-fixture: PASS`.

- [ ] **Step 5: Commit**

```bash
git add tests/harness/lib/fixture.sh tests/harness/lib/tests/test-fixture.sh
git commit -m "test(harness): scratch template + spoke fixture builders"
```

---

## Task 4: Claude Code Layer-1 wiring checks

**Files:**
- Modify: `tests/harness/claude-code/wiring.sh` (replace the placeholder)

**Interfaces:**
- Consumes: `assert.sh` verbs; `$HARNESS_REPO_ROOT` (set by the runner to the repo root — add it in this task).
- Produces: `wiring()` asserting the `.claude/` surface is generated and in sync.

- [ ] **Step 1: Add `HARNESS_REPO_ROOT` to the runner**

In `tests/harness/run-harness-tests.sh`, after the `source assert.sh` line, add:

```bash
HARNESS_REPO_ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
export HARNESS_REPO_ROOT
```

- [ ] **Step 2: Write `wiring()` for Claude Code**

```bash
# tests/harness/claude-code/wiring.sh
wiring() {
  local r="$HARNESS_REPO_ROOT"
  file-exists "$r/.claude/CLAUDE.md"
  file-contains "$r/.claude/CLAUDE.md" 'GENERATED by tools/gather.py'
  file-exists "$r/.claude/commands/setup-awow.md"
  dir-exists "$r/.claude/skills"
  # the .claude surface must be in sync with .agents (drift guard)
  if ( cd "$r" && python3 tools/gather.py --surface claude --check >/dev/null 2>&1 ); then
    _record pass "gather --surface claude --check"
  else
    _record fail "gather --surface claude --check"
  fi
}
```

- [ ] **Step 3: Run to verify it passes against the real repo**

Run: `bash tests/harness/run-harness-tests.sh claude-code`
Expected: `CHECK\tpass` lines for each verb, `all checks passed` (exit 0). (The `.claude/` surface exists and is in sync on this branch.)

- [ ] **Step 4: Commit**

```bash
git add tests/harness/run-harness-tests.sh tests/harness/claude-code/wiring.sh
git commit -m "test(harness): Claude Code Layer-1 wiring checks"
```

---

## Task 5: Codex Layer-1 wiring checks

**Files:**
- Modify: `tests/harness/codex/wiring.sh`

**Interfaces:**
- Produces: `wiring()` asserting root `AGENTS.md` steering (present + points at `.agents/AGENTS.md`), and the `.codex-plugin` manifest **iff present** (SKIP until hub-spoke WI-5 lands it).

- [ ] **Step 1: Write `wiring()` for Codex**

```bash
# tests/harness/codex/wiring.sh
wiring() {
  local r="$HARNESS_REPO_ROOT"
  # Root AGENTS.md is Codex's zero-install steering (pi-codex keystone).
  if [ -f "$r/AGENTS.md" ]; then
    file-contains "$r/AGENTS.md" 'GENERATED by tools/gather.py'
    file-contains "$r/AGENTS.md" '\.agents/AGENTS\.md'
  else
    skip "root AGENTS.md absent (pi-codex keystone not on this branch yet)"
  fi
  # Codex plugin manifest — only once hub-spoke WI-5 emits it.
  if [ -f "$r/.codex-plugin/plugin.json" ]; then
    cmd-succeeds "codex plugin.json is valid JSON" -- python3 -c "import json,sys; json.load(open('$r/.codex-plugin/plugin.json'))"
    file-contains "$r/.codex-plugin/plugin.json" '"hooks"[[:space:]]*:[[:space:]]*\{\}'
  else
    skip ".codex-plugin/plugin.json absent (hub-spoke WI-5 not landed)"
  fi
}
```

- [ ] **Step 2: Run to verify (expect a mix of pass + skip, exit 0)**

Run: `bash tests/harness/run-harness-tests.sh codex`
Expected: on `main` today — `skip` for root `AGENTS.md` (pi-codex #26 not merged to this branch) and `skip` for `.codex-plugin`; exit 0. After `git merge main` once #26 lands, the AGENTS.md checks turn to `pass`.

- [ ] **Step 3: Commit**

```bash
git add tests/harness/codex/wiring.sh
git commit -m "test(harness): Codex Layer-1 wiring checks (root AGENTS.md + plugin manifest, SKIP-gated)"
```

---

## Task 6: Pi Layer-1 wiring checks

**Files:**
- Modify: `tests/harness/pi/wiring.sh`

**Interfaces:**
- Produces: `wiring()` asserting root `AGENTS.md` steering (Pi reads it by default — spec §7) and the `.pi/extensions/awow.ts` extension **iff present** (SKIP until hub-spoke WI-5).

- [ ] **Step 1: Write `wiring()` for Pi**

```bash
# tests/harness/pi/wiring.sh
wiring() {
  local r="$HARNESS_REPO_ROOT"
  # Pi discovers root AGENTS.md/CLAUDE.md by default (spec §7); same keystone as Codex.
  if [ -f "$r/AGENTS.md" ]; then
    file-contains "$r/AGENTS.md" '\.agents/AGENTS\.md'
  else
    skip "root AGENTS.md absent (pi-codex keystone not on this branch yet)"
  fi
  if [ -f "$r/.pi/extensions/awow.ts" ]; then
    file-contains "$r/.pi/extensions/awow.ts" 'skillPaths'
  else
    skip ".pi/extensions/awow.ts absent (hub-spoke WI-5 not landed)"
  fi
}
```

- [ ] **Step 2: Run to verify (expect skips, exit 0)**

Run: `bash tests/harness/run-harness-tests.sh pi`
Expected: `skip` lines, exit 0.

- [ ] **Step 3: Commit**

```bash
git add tests/harness/pi/wiring.sh
git commit -m "test(harness): Pi Layer-1 wiring checks (root AGENTS.md + extension, SKIP-gated)"
```

---

## Task 7: Wire Layer-1 into CI

**Files:**
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `run-harness-tests.sh all` (no `--live`) — Layer-1 only, no gateway, no CLIs needed beyond `python3`.

- [ ] **Step 1: Add the CI step**

Append to the `gather-check` job's `steps:` in `.github/workflows/ci.yml`:

```yaml
      - name: Harness wiring checks (Layer 1, no model)
        run: bash tests/harness/run-harness-tests.sh all
```

- [ ] **Step 2: Verify locally the exact CI invocation is green**

Run: `bash tests/harness/run-harness-tests.sh all; echo "exit=$?"`
Expected: mix of pass/skip across the three harnesses, `all checks passed`, `exit=0`. (No `--live`, so no model or CLI is exercised.)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run harness Layer-1 wiring checks on every PR"
```

---

## Task 8: Claude Code Layer-2 — setup-wiring scenario

**Files:**
- Modify: `tests/harness/claude-code/live.sh` (replace placeholder)

**Interfaces:**
- Consumes: `gateway.sh` (`resolve_transport`, `shim_start`/`shim_stop`, `openrouter_key`); `fixture.sh` (`make_template_fixture`); `assert.sh`.
- Produces: `live()` that, when a transport resolves and `claude` is installed, builds a template fixture and drives `claude -p` on `deepseek-v4-flash` to confirm the harness loads awow and answers; SKIPs otherwise. Task 9 appends the deploy scenario to the same `live()`.

- [ ] **Step 1: Write `live()` — setup-wiring**

```bash
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
    base="$(shim_start)" || { skip "litellm shim unavailable"; return 0; }
    token="sk-local-noauth"; model="deepseek-flash"
  else
    base="$AWOW_GATEWAY_BASE"; token="$AWOW_GATEWAY_TOKEN"; model="$TP_MODEL"
  fi
  trap 'shim_stop' RETURN

  local fx; fx="$(mktemp -d)/repo"
  make_template_fixture "$fx" || { _record fail "template fixture build"; return 0; }
  _record pass "template fixture built"

  # Drive claude headless in the fixture; budget tokens for the reasoning model.
  local out; out="$(mktemp)"
  ( cd "$fx" && env -u ANTHROPIC_API_KEY \
      ANTHROPIC_BASE_URL="$base" ANTHROPIC_AUTH_TOKEN="$token" ANTHROPIC_MODEL="$model" \
      MAX_THINKING_TOKENS=1024 \
      claude -p "Reply with exactly one word: READY" --model "$model" >"$out" 2>/dev/null )
  if grep -qi 'READY' "$out"; then _record pass "claude -p ran awow fixture and answered"; else _record fail "claude -p produced no usable answer"; fi
  rm -f "$out"
}
```

- [ ] **Step 2: Run live (with a resolvable transport)**

Run: `OPENROUTER_API_KEY not needed if in keychain:` `bash tests/harness/run-harness-tests.sh claude-code --live`
Expected: `template fixture built` pass, `claude -p ran awow fixture and answered` pass; exit 0. If no key/CLI: clean `skip`, exit 0.

- [ ] **Step 3: Commit**

```bash
git add tests/harness/claude-code/live.sh
git commit -m "test(harness): Claude Code live setup-wiring scenario"
```

---

## Task 9: Claude Code Layer-2 — hub-spoke deploy scenario

**Files:**
- Modify: `tests/harness/claude-code/live.sh` (append to `live()`)

**Interfaces:**
- Consumes: `make_spoke_fixture`; the resolved `base/token/model` from Task 8.
- Produces: appends deploy assertions — install the `dist/` payload as a local plugin marketplace against a thin spoke, run a command that reads hub config, assert the spoke's scope is what the model reports (§8.1 T1); fail-loud on unset hub (T3).

- [ ] **Step 1: Append the deploy block** to `live()`, before the final `}`:

```bash
  # --- hub-spoke deploy (needs the built payload) ---
  if [ ! -d "$HARNESS_REPO_ROOT/dist/commands" ]; then skip "dist/ payload absent (hub-spoke not built on this branch)"; return 0; fi
  local spoke; spoke="$(make_spoke_fixture "$(mktemp -d)/spoke")" || { _record fail "spoke fixture build"; return 0; }
  _record pass "spoke fixture built"

  # T3 (fail-loud): with the hub identity unset, a hub-reading command must NOT invent context.
  local o2; o2="$(mktemp)"
  ( cd "$spoke" && env -u AWOW_HUB -u ANTHROPIC_API_KEY \
      ANTHROPIC_BASE_URL="$base" ANTHROPIC_AUTH_TOKEN="$token" ANTHROPIC_MODEL="$model" \
      claude -p "Read the board config named by this repo's AGENTS.md hub. If you cannot resolve the hub path, reply exactly: HUB_UNRESOLVED. Do not guess." --model "$model" >"$o2" 2>/dev/null )
  if grep -q 'HUB_UNRESOLVED' "$o2"; then _record pass "deploy: fail-loud on unset hub (T3)"; else _record fail "deploy: model guessed instead of failing loud (T3)"; fi
  rm -f "$o2"
```

- [ ] **Step 2: Run live**

Run: `bash tests/harness/run-harness-tests.sh claude-code --live`
Expected: if `dist/` present (it is on `main` after #25) — `spoke fixture built` + a `deploy: fail-loud` result; else `skip`. Exit 0 unless an assertion genuinely fails.

- [ ] **Step 3: Commit**

```bash
git add tests/harness/claude-code/live.sh
git commit -m "test(harness): Claude Code live hub-spoke deploy scenario"
```

---

## Task 10: Codex Layer-2 — setup-wiring scenario

**Files:**
- Modify: `tests/harness/codex/live.sh`

**Interfaces:**
- Consumes: `gateway.sh`, `fixture.sh`. Codex is OpenAI-compatible → no shim; point a custom provider at OpenRouter (or the APIM `/v1` in apim mode). Sandbox `-s read-only`, `--json`.
- Produces: `live()` — build a template fixture, run `codex exec` on `deepseek-v4-flash`, assert it completes and answers; deploy scenario SKIPs until hub-spoke WI-5 provides `.codex-plugin`.

- [ ] **Step 1: Write `live()` for Codex**

```bash
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

  local out; out="$(mktemp)"
  OPENROUTER_API_KEY="$key" codex exec \
    -C "$fx" -s read-only --skip-git-repo-check --ignore-user-config --json \
    -c model_providers.awow.name=awow \
    -c "model_providers.awow.base_url=$base" \
    -c model_providers.awow.env_key=OPENROUTER_API_KEY \
    -c model_provider=awow \
    -m "$TP_MODEL" \
    "Reply with exactly one word: READY" >"$out" 2>/dev/null
  if grep -qi 'READY' "$out"; then _record pass "codex exec ran awow fixture and answered"; else _record fail "codex exec produced no usable answer"; fi
  rm -f "$out"

  skip "codex hub-spoke deploy: awaits hub-spoke WI-5 (.codex-plugin manifest)"
}
```

- [ ] **Step 2: Run live**

Run: `bash tests/harness/run-harness-tests.sh codex --live`
Expected: `template fixture built` + `codex exec ... answered` pass, then a `skip` for deploy; exit 0. (In `apim` mode the `env_key`/base differ; the SPN token path is Task 12.)

- [ ] **Step 3: Commit**

```bash
git add tests/harness/codex/live.sh
git commit -m "test(harness): Codex live setup-wiring scenario (read-only sandbox)"
```

---

## Task 11: Pi Layer-2 — setup-wiring scenario

**Files:**
- Modify: `tests/harness/pi/live.sh`

**Interfaces:**
- Consumes: `gateway.sh`, `fixture.sh`. Pi: `-p --mode json --no-session`, tool-restricted; `--provider openrouter --model deepseek/deepseek-v4-flash --api-key <key>` in openrouter mode. (apim mode needs a `models.json` provider block — Task 12.) Also asserts the spec §7 finding: Pi reads root `AGENTS.md`.
- Produces: `live()` — run `pi -p` in a template fixture, assert it answers; deploy SKIPs until WI-5.

- [ ] **Step 1: Write `live()` for Pi**

```bash
# tests/harness/pi/live.sh
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/gateway.sh"
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/../lib/fixture.sh"

live() {
  command -v pi >/dev/null 2>&1 || { skip "pi CLI not installed"; return 0; }
  resolve_transport || { skip "no transport resolved"; return 0; }
  if [ "$TP_MODE" != "openrouter" ]; then skip "pi apim mode needs a models.json provider block (Task 12)"; return 0; fi

  local fx; fx="$(mktemp -d)/repo"
  make_template_fixture "$fx" || { _record fail "template fixture build"; return 0; }
  _record pass "template fixture built"

  local out; out="$(mktemp)"
  ( cd "$fx" && pi -p --mode json --no-session --no-tools \
      --provider openrouter --model "deepseek/deepseek-v4-flash" --api-key "$(openrouter_key)" \
      "Reply with exactly one word: READY" >"$out" 2>/dev/null )
  if grep -qi 'READY' "$out"; then _record pass "pi -p ran awow fixture and answered"; else _record fail "pi -p produced no usable answer"; fi
  rm -f "$out"

  skip "pi hub-spoke deploy: awaits hub-spoke WI-5 (.pi extension)"
}
```

- [ ] **Step 2: Run live**

Run: `bash tests/harness/run-harness-tests.sh pi --live`
Expected: `template fixture built` + `pi -p ... answered` pass, deploy `skip`; exit 0. If Pi's OpenRouter provider name differs, adjust `--provider` per `pi --list-models` (note it in README).

- [ ] **Step 3: Commit**

```bash
git add tests/harness/pi/live.sh
git commit -m "test(harness): Pi live setup-wiring scenario (tool-restricted)"
```

---

## Task 12: APIM token mint + README

**Files:**
- Modify: `tests/harness/lib/gateway.sh` (add `apim_mint_token`)
- Create: `tests/harness/README.md`

**Interfaces:**
- Produces: `apim_mint_token()` — if `$AWOW_GATEWAY_TOKEN` is set, echo it; else if the SPN triple is set, mint a client-credentials v2 token via `curl` to `login.microsoftonline.com/$AWOW_SP_TENANT/oauth2/v2.0/token` with `scope=api://$AWOW_GATEWAY_AUD/.default`; else empty. Called by `resolve_transport` to fill `TP_OPENAI_AUTH` in apim mode.

- [ ] **Step 1: Add `apim_mint_token` and call it from `resolve_transport`**

```bash
# append to tests/harness/lib/gateway.sh
apim_mint_token() {
  if [ -n "${AWOW_GATEWAY_TOKEN:-}" ]; then printf '%s' "$AWOW_GATEWAY_TOKEN"; return 0; fi
  [ -n "${AWOW_SP_CLIENT_ID:-}" ] && [ -n "${AWOW_SP_CLIENT_SECRET:-}" ] && [ -n "${AWOW_SP_TENANT:-}" ] && [ -n "${AWOW_GATEWAY_AUD:-}" ] || return 1
  curl -s -X POST "https://login.microsoftonline.com/$AWOW_SP_TENANT/oauth2/v2.0/token" \
    -d grant_type=client_credentials -d client_id="$AWOW_SP_CLIENT_ID" \
    -d client_secret="$AWOW_SP_CLIENT_SECRET" -d scope="api://$AWOW_GATEWAY_AUD/.default" \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))"
}
```

In `resolve_transport`, replace the apim `TP_OPENAI_AUTH="${AWOW_GATEWAY_TOKEN:-}"` line with:

```bash
    TP_OPENAI_AUTH="$(apim_mint_token)"; [ -n "$TP_OPENAI_AUTH" ] || return 1
```

- [ ] **Step 2: Write the README (no secrets — env var names only)**

```markdown
# tests/harness — per-harness wiring test suite

Two layers (see `meta/proposals/harness-wiring-test-suite.md`):
- **Layer 1 (wiring)** — deterministic, runs in CI: `bash tests/harness/run-harness-tests.sh all`
- **Layer 2 (live)** — opt-in, drives each CLI on `deepseek-v4-flash`: add `--live`.

## Credentials (nothing is committed)
- **openrouter mode:** `OPENROUTER_API_KEY` in env or macOS keychain (`security add-generic-password -l OPENROUTER_API_KEY -a $USER -w`).
- **apim mode:** `AWOW_GATEWAY_BASE` (operator-supplied) + either `AWOW_GATEWAY_TOKEN` (a v2 Entra token with a MeshService/NightRunner role) or the SPN triple `AWOW_SP_TENANT`/`AWOW_SP_CLIENT_ID`/`AWOW_SP_CLIENT_SECRET` + `AWOW_GATEWAY_AUD`. See linear `context/knowledge-base/runbooks/call-litellm-via-apim.md`.

Absent a CLI or credential, live checks SKIP (never fail).
```

- [ ] **Step 3: Run the full suite live to confirm end-to-end**

Run: `bash tests/harness/run-harness-tests.sh all --live; echo "exit=$?"`
Expected: for each installed harness with a resolvable transport, `... answered` passes; deploy scenarios pass or skip per branch state; `exit=0`.

- [ ] **Step 4: Commit**

```bash
git add tests/harness/lib/gateway.sh tests/harness/README.md
git commit -m "test(harness): apim SPN token mint + suite README"
```

---

## Self-Review Notes (for the implementer)

- **Spec coverage:** WI-1 → Tasks 2–3 (+1 assert lib); WI-2 → Tasks 1,4,5,6,7; WI-3 → Tasks 8–9; WI-4 → Task 10; WI-5 → Task 11; WI-6 → Task 12. All six covered.
- **SKIP discipline:** every live/manifest check that can be absent records `skip`, never `fail` (missing CLI, no transport, no `dist/`, no `.codex-plugin`/`.pi`).
- **Reasoning-model guard:** live prompts ask for a one-word sentinel (`READY`) and match case-insensitively; `MAX_THINKING_TOKENS`/token budget lets the `thinking` block complete before the `text` block.
- **Verify-at-build items** (flagged inline, not blockers): exact Pi OpenRouter `--provider` name (Task 11), Codex custom-provider `-c` keys against the installed 0.144.x (Task 10), and `/setup-awow` non-interactive scope (fixture uses installer+gather+discovery, not the wizard — matches spec §4).
```

