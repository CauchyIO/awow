# tests/harness — per-harness wiring test suite

Two layers (design: [`meta/proposals/harness-wiring-test-suite.md`](../../meta/proposals/harness-wiring-test-suite.md)):

- **Layer 1 (wiring)** — deterministic, no model, runs in CI:
  ```bash
  bash tests/harness/run-harness-tests.sh all
  ```
- **Layer 2 (live)** — opt-in, drives each installed CLI on `deepseek-v4-flash`:
  ```bash
  bash tests/harness/run-harness-tests.sh all --live
  ```

Target one harness with `claude-code` / `codex` / `pi` instead of `all`. Exit codes: `0` all passed, `1` an assertion failed, `127` broken invocation. A missing CLI, credential, or not-yet-built manifest records `skip` (never fail).

## Credentials (nothing is committed)

The transport is resolved by available credential (`tests/harness/lib/gateway.sh`):

- **openrouter mode** (default on a laptop): `OPENROUTER_API_KEY` in env, or in the macOS keychain:
  ```bash
  security add-generic-password -l OPENROUTER_API_KEY -a "$USER" -w <key>
  ```
  Claude Code is driven through a box-local `litellm` Anthropic shim; codex/pi point straight at OpenRouter.
- **gateway mode** (a box with a service identity): `AWOW_GATEWAY_BASE` (operator-supplied, an
  OpenAI-compatible endpoint) plus either `AWOW_GATEWAY_TOKEN` (a pre-minted OIDC bearer token) or the
  client-credentials triple `AWOW_SP_TENANT` / `AWOW_SP_CLIENT_ID` / `AWOW_SP_CLIENT_SECRET` +
  `AWOW_GATEWAY_AUD`. See your team's private gateway auth runbook.

## Known limitations (verified 2026-07-13)

- **Codex + deepseek-v4-flash via OpenRouter**: codex 0.144 requires the Responses API and, with its
  tool/app/plugin features on, advertises a `namespace` tool type that deepseek-v4-flash's OpenRouter
  endpoints reject. The suite runs codex with those features **disabled** (`--disable browser_use …`),
  which a wiring smoke does not need — the codex turn then completes. If the format changes and the
  request is still rejected, the turn SKIPs with that reason rather than failing. (Note: a gateway
  tier that proxies to the same downstream model would hit the same wall — the fix is disabling the
  tools, not the transport.)
- **Hub-spoke deploy**: the Claude Code deploy scenario checks the payload + connector deterministically.
  The codex/pi `live` paths now install the real awow plugin/package from the built `dist/` (staged as a
  git repo, mirroring `tools/sync-dist.sh` → `CauchyIO/awow-dist`) and assert a flow is discoverable —
  no model needed. The Claude Code behavioural hub-resolution run still SKIPs until WI-4 `resolve_hub` lands.
- **Pi apim mode** needs a `models.json` provider block (Pi ignores `OPENAI_BASE_URL`); openrouter mode
  uses Pi's built-in `openrouter` provider.
