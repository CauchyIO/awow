---
selectivity: 2            # 0 strict … 5 generous — how low the keep bar sits. awow defaults strict.
categories:               # which insight types the mining lens may capture
  - patterns
  - decisions
  - architecture
  - runbooks
  - glossary
max_candidates_per_run: 5 # hard cap on candidates emitted in one mining run
max_candidates_per_item: 2 # cap per source item (one issue/PR rarely yields more)
---

# Mining policy — the tunable keep bar

The one lever over **what the mining lens keeps**. `context/knowledge-base/mining.md`
reads this file and applies the dials above plus the rubric below; it does not hardcode
the bar. Tune here, in one place — the mining contract is unchanged.

> **Paths.** The `inbox` and `kb_root` locations referenced below resolve via
> `context/tooling/knowledge-base.md`; the literals are the defaults.

The dials live in the frontmatter so they are cheap to read and edit:

| Dial | Meaning |
|---|---|
| `selectivity` | The main knob. `0` = only the most unmistakable durable insight; `5` = generous, keep anything plausibly reusable. awow ships at `2`: **a low yield of high-signal candidates beats a pile of noise.** |
| `categories` | Which insight types may be captured. Each maps to a `context/knowledge-base/` destination (see mining.md's routing table). Remove one to stop mining it. |
| `max_candidates_per_run` | Hard ceiling per run. If more seem to qualify, the bar is too low — raise `selectivity`'s strictness and keep the strongest. |
| `max_candidates_per_item` | Ceiling per source issue/PR. Guards against one noisy thread flooding the inbox. |

---

## The rubric — durable-only

Mine for what belongs in a **reference layer**, not a changelog. The test: *would a
teammate six months from now, hitting this problem cold, be glad this was written
down?*

**Qualifies:**
- A **reusable pattern** — "how we do X" that recurred or was deliberately chosen.
- A **decision + rationale** — a choice with trade-offs worth an ADR (why A over B).
- An **architecture / integration** note — system shape, a contract between parts.
- A **runbook-worthy** sequence — an ops/incident procedure someone will repeat.
- A **new domain term** — vocabulary used as if known but not yet in the glossary.

**Does not qualify** (drop these):
- Story status, blockers, or intermediate findings → those live in story comments.
- A one-off fix already legible from the code + git history.
- Scope or acceptance criteria → those live in the story body.
- Anything already covered by an existing KB entry (dedup — see mining.md).

**Examples**

- KEEP → `decisions/`: "We chose per-tenant schemas over row-level security because the
  compliance audit needs a hard data boundary, accepting the migration cost."
- KEEP → `patterns/`: "We wrap every board write in the idempotency helper so a retried
  MCP call can't double-post a comment."
- DROP: "Moved <TEAM>-123 to In Review." / "Fixed the typo in the config loader."

---

## Tuning signal (optional)

The synthesis drain records each candidate's fate in `context/kb-inbox/_synthesis-log.md`
(`promoted` / `annotated` / `no-op` / `dropped`). Read against it over time: a high
**drop / no-op** rate means the bar is too low (raise strictness); a **trickle** of
candidates on active days means it is too high (lower it). An automated tuning loop over
this signal is deferred — see `meta/proposals/kb-capture-synthesize-spine.md`.
