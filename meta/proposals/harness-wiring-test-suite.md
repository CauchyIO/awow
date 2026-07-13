# Proposal — harness wiring test suite (Claude Code / Codex / Pi)

**Status:** Draft — awaiting review. Design validated by a live transport spike (2026-07-13, §6); the claude↔deepseek path is proven working, so the build is mechanical.
**Inputs:** Maintainer request (Casper, 2026-07-13) for a simple test per harness (Claude Code, Codex, Pi) that drives each headlessly against a cheap model and validates that the awow wiring is *set up right* — not prompt-quality regression (explicitly later). References named by the maintainer: `../superpowers` for test structure (its `tests/<harness>/` split + `docs/testing.md`), and `../linear` for the already-working APIM+OpenRouter inference config (`docs/inference-mesh/LITELLM-GATEWAY-AND-AUTH.md`, `internal_projects/local_llm/mesh/claude-code-settings.reference.json`). Builds on the deferred headless driver in `hub-and-spoke-design.md` §8/WI-8, `eval-baseline-and-prompt-cleanup.md`, and the non-headless `setup-awow-regression-tests.md` (Landed).
**Scope:** a per-harness integration suite that (1) checks the generated surfaces/manifests each harness needs are wired correctly (deterministic, CI-safe) and (2) drives the real CLI headless on `deepseek-v4-flash` to prove `/setup-awow` bootstrap and the hub-spoke deployment actually work. **Out of scope:** prompt/behavioural regression (the later eval suite), multi-turn wizard branches, real board writes.

---

## 1. Why now, and what unlocks it

The Landed `setup-awow-regression-tests.md` framework was built under an explicit constraint: *"the maintainer does not have an Anthropic API key… no `claude -p`, no programmatic invocation."* That ruled out a headless driver and pushed it toward "human drives, machine grades." `hub-and-spoke-design.md` §8/WI-8 wanted the opposite — a headless matrix across Claude Code / Codex / Pi — but deferred it behind the same key gap (its §8.1 MVP hand-ran one `claude -p` flow).

A cheap model over OpenRouter (`deepseek-v4-flash`, ~$0.08/$0.15 per Mtok) removes the gap. This proposal is the **headless wiring driver all three prior specs deferred** — scoped tightly to "is it set up right," leaving prompt quality to the eval suite.

## 2. Two layers (mirrors superpowers' `tests/` vs `evals/` split)

superpowers separates *"does the non-LLM wiring work?"* (`tests/`, deterministic, CI) from *"do agents behave right?"* (`evals/`, live, slow, not in CI). This suite lives mostly in the first bucket with a thin live touch, and deliberately not in the second.

- **Layer 1 — wiring (deterministic, no model, CI-safe).** Per harness, assert the surfaces/manifests it discovers are correctly generated: root `AGENTS.md` present and points at `.agents/AGENTS.md` (Codex, Pi); `.codex-plugin/plugin.json` valid with the load-bearing empty `"hooks": {}` (once hub-spoke WI-5 lands); `.pi` extension loads; `gather.py --surface <h>` in sync. Fast; localises failures; runs on every PR.
- **Layer 2 — live smoke (opt-in `--live`, needs a gateway).** Per harness, drive the real CLI headless on `deepseek-v4-flash` in a scratch fixture. Two scenarios (§4). Asserts wiring *outcomes* (files created, command discovered, output shape, spoke resolves hub) — never prompt quality.

## 3. Layout

```
tests/harness/
├── lib/
│   ├── gateway.sh     # resolve base_url + auth + model; pluggable mode; fail loud; NOTHING committed
│   ├── fixture.sh     # build scratch template-repo + thin-spoke + local marketplace (§8.1's setup-fixture.sh)
│   └── assert.sh      # reuse tests/checks-prelude.sh verb style
├── claude-code/       # per-harness driver + scenarios
├── codex/
├── pi/
└── run-harness-tests.sh <claude-code|codex|pi|all> [--live]
```

Follows superpowers' `tests/<harness>/` shape and awow's existing `tests/run-checks.sh` / `checks-prelude.sh` conventions.

## 4. Layer-2 scenarios (per harness)

1. **Setup wiring.** Bootstrap awow into a scratch repo (installer + `gather.py`, i.e. `/setup-awow` Step 0 mechanics — not the interactive wizard; drive `--quickstart`/non-interactive), then a real headless invocation of one **read-only** awow command-as-skill. Assert the harness discovered it and the end state is right. Answers *"is awow set up right in this harness?"*
2. **Hub-spoke deploy.** Install the built `dist/` payload as a plugin + a thin spoke, `resolve_hub` maps identity→path, live-run a command that reads hub config + spoke scope. Assert it names the spoke's items, fails loud on unset hub, and provenance/collision hold — i.e. the §8.1 MVP **T1–T5**, generalised from one harness to three.

**Buildable-now gating.** Claude Code runs both scenarios today (payload exists; §8.1 already proved the flow). **Codex** runs scenario 1 via the root `AGENTS.md` path now; its `.codex-plugin` deploy path **SKIPs (clear message) until hub-spoke WI-5**. **Pi** likewise — see §7 for the live finding that Pi already reads root `AGENTS.md`. SKIP, never fail, when a CLI/gateway/manifest is absent (superpowers' evals-not-in-CI posture).

## 5. Transport — pluggable, direct-OpenRouter default (spike-driven, §6)

`gateway.sh` resolves `(base_url, auth, model)` from environment/config, **committing nothing** (awow is public — no gateway URLs, tenant/client IDs, or keys in the tree). Two modes:

- **`openrouter` (default, proven today).** Model `deepseek/deepseek-v4-flash`, key from keychain (`security find-generic-password -l OPENROUTER_API_KEY -w`) or `$OPENROUTER_API_KEY`. codex/pi are OpenAI-compatible → point straight at `openrouter.ai`. **Claude Code needs an Anthropic `/v1/messages` endpoint**, so the suite stands up a **box-local litellm shim** (`litellm` is installed) mapping a model alias → `openrouter/deepseek/deepseek-v4-flash`, and points `claude -p` at it via `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`.
- **`apim` (opt-in; config owned elsewhere).** The Cauchy APIM+LiteLLM gateway. Auth is an Entra token (`az account get-access-token --resource api://<client-id>`), OpenAI-compatible at `/litellm/v1`, and Claude Code uses the `apiKeyHelper` pattern from linear's `claude-code-settings.reference.json`. Gateway URL/resource/model-alias come from env/config sourced from the linear mesh docs — never committed here. **Current-state caveat (from §6): the maintainer's virtual key is allow-listed to `gemma-worker` only, and that model 500s on the Anthropic `/v1/messages` shape — so APIM cannot serve `deepseek-v4-flash` to Claude Code (or codex/pi) until the key's allow-list + the model's Anthropic-messages provider are reconciled.** That reconciliation is delegated to a separate agent/effort; this suite treats `apim` as a ready slot, not a blocker.

**Model note:** `deepseek-v4-flash` is a *reasoning* model — responses carry a `thinking` block plus a `text` block. Drivers must budget enough `max_tokens` and assert on the `text` block, not choke on empty text under a tiny budget.

## 6. Transport spike (run 2026-07-13, claude 2.1.207, litellm local)

| # | Check | Result |
|---|---|---|
| S1 | APIM reachable + Entra auth (`az` token) accepted | **PASS** — gateway responds, token valid |
| S2 | APIM serves `deepseek-v4-flash` | **FAIL** — key allow-listed to `gemma-worker` only; `worker`/`deepseek-*` → `401 key not allowed` |
| S3 | APIM `gemma-worker` on Anthropic `/v1/messages` | **FAIL** — `500 Anthropic messages provider config not found` (MLX/openai-backed model, no anthropic bridge) |
| S4 | Direct OpenRouter → local litellm Anthropic shim → `/v1/messages` | **PASS** — `200`, valid Anthropic-shape body |
| S5 | Real `claude -p` through the shim on `deepseek-v4-flash` | **PASS** — exit 0; litellm logged `POST /v1/messages?beta=true 200`; content `"2+2 equals 4."` |

**Conclusion:** direct-OpenRouter is the path that delivers `deepseek-v4-flash` to all three harnesses today; APIM is a documented, currently-gemma-only secondary.

## 7. Live finding — Pi reads root `AGENTS.md` (resolves pi-codex open item 2)

`pi --help` carries `--no-context-files: Disable AGENTS.md and CLAUDE.md discovery` — i.e. Pi **discovers root `AGENTS.md`/`CLAUDE.md` by default.** So the PR #26 keystone steers Pi zero-install too, and `context/tooling/harnesses/pi.md`'s "Pi has no zero-install in-repo story" is wrong and should be corrected in a follow-up. The Pi setup-wiring scenario asserts this directly.

## 8. Test-safety guards

Every live run is sandboxed (Codex `-s read-only`; Pi tool-restricted via `--no-tools`/`--tools`; Claude in a scratch dir), against scratch fixtures only, on the cheap model, opt-in behind `--live` + a resolvable gateway. Absent CLI/gateway/manifest → **SKIP**, never fail. No secrets or internal endpoints ever land in the repo; the pre-push leak scan backstops it.

## 9. Work items

- **WI-1** — `tests/harness/lib/gateway.sh` (pluggable, openrouter default, fail-loud) + `fixture.sh` (scratch template-repo + thin-spoke + local marketplace) + `assert.sh`.
- **WI-2** — `run-harness-tests.sh` driver + Layer-1 deterministic wiring checks for all three harnesses (CI-wired via `.github/workflows/ci.yml`, no `--live`).
- **WI-3** — Claude Code Layer-2: box-local litellm shim + both scenarios (setup wiring, hub-spoke deploy).
- **WI-4** — Codex Layer-2: `codex exec` driver (OpenRouter provider, `-s read-only`, `--json`); scenario 1 now, deploy SKIP until hub-spoke WI-5.
- **WI-5** — Pi Layer-2: `pi -p` driver (`--mode json`, `--no-session`, tool restriction); scenario 1 (incl. the §7 root-`AGENTS.md` assertion), deploy SKIP until hub-spoke WI-5.
- **WI-6** — `apim` transport mode wired to the ready slot once the key/config reconciliation (§5/§6) lands; docs page for running the suite.

## 10. Open items

1. **APIM config reconciliation** — the maintainer's key allow-list + a deepseek Anthropic-messages provider on the gateway (§6 S2/S3). Owned by a separate effort; `apim` mode is built against it but not blocked on it.
2. **Claude auth in `apim` mode** — static Entra token vs the `apiKeyHelper` refresh pattern (token TTL ~50 min per the reference config).
3. **Pi provider wiring** — confirm Pi's OpenRouter provider vs a custom OpenAI base_url at build time (`--provider`/`--model`/`--api-key`).
4. **`/setup-awow` non-interactive** — confirm `--quickstart` is headless-drivable end-to-end, or scope scenario 1 to the installer+gather+discovery+one-command slice.

## 11. Suggested sequencing

1. Review and accept this proposal; land on a new branch off `main` (`feat/harness-wiring-tests`).
2. WI-1..2 first (deterministic floor + runner, CI-green with no gateway).
3. WI-3 (Claude Code live — the proven path) as the reference scenario; WI-4..5 (Codex/Pi) follow the same shape.
4. WI-6 once the APIM details land from the separate effort.
