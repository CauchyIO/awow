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
- **apim mode** (a box with a service identity): `AWOW_GATEWAY_BASE` (operator-supplied) plus either
  `AWOW_GATEWAY_TOKEN` (a v2 Entra token carrying a `MeshService`/`NightRunner` role) or the SPN triple
  `AWOW_SP_TENANT` / `AWOW_SP_CLIENT_ID` / `AWOW_SP_CLIENT_SECRET` + `AWOW_GATEWAY_AUD`. Auth model:
  linear `context/knowledge-base/runbooks/call-litellm-via-apim.md`.

## Known limitations (verified 2026-07-13)

- **Codex + deepseek-v4-flash via OpenRouter**: codex 0.144 requires the Responses API and advertises
  `namespace`-format tools that deepseek-v4-flash's OpenRouter endpoints reject — the codex live turn
  SKIPs with that reason. It needs a tool-capable model or the APIM `worker` tier.
- **Hub-spoke deploy**: the Claude Code deploy scenario checks the payload + connector deterministically;
  the behavioural hub-resolution run and the codex/pi deploy paths SKIP until the hub-spoke work items
  (WI-4 `resolve_hub`, WI-5 Codex/Pi manifests) land.
- **Pi apim mode** needs a `models.json` provider block (Pi ignores `OPENAI_BASE_URL`); openrouter mode
  uses Pi's built-in `openrouter` provider.
