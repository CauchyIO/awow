# Proposal — The M365 Copilot harness

**Status:** Accepted — Phase-1 try-out slice in build (2026-07-28).
**Spec:** [`docs/superpowers/specs/2026-07-15-m365-copilot-harness-design.md`](../../docs/superpowers/specs/2026-07-15-m365-copilot-harness-design.md) — the full design: problem, architecture, the two primitive swaps, phase plan, decisions D1–D7.
**Scope:** add `m365` to awow's harness fan-out. `gather.py --surface m365` renders `.agents/` + `context/` into an M365 Copilot declarative-agent package; a `fetchAwowContext` action reads context live from git so git stays the sole SSOT; `commitAwowInbox` routes M365-originated KB captures into the existing `kb-inbox/` drain.

## Increment in build — the try-out slice

The smallest package that tests the load-bearing claim (fetch-then-follow-the-playbook fidelity) on a real tenant, before any board wiring:

1. `gather.py --surface m365` emitting `dist/m365/` (manifest, `declarativeAgent.json`, assembled instructions with the 8,000-char build gate).
2. `fetchAwowContext` as an OpenAPI action against the public repo's raw content — the spec's public-hub direct-fetch case; the §4.1a endpoint is deferred with the private-hub increment.
3. Advisory conversation starters only (context-grounded commands); ADO/Jira action bindings deferred.
4. Sideload into a pilot tenant; validate grounding against the §10 smoke-test set.

Deferred with the later increments: the fetch/write endpoint, `commitAwowInbox`, board action bindings (D3), Studio flows (Phase 2), Graph connector (D7 = out).
