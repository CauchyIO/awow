# Canonical knowledge sources

Route from shared team context to authoritative knowledge without turning the HUB into a mirror.

> **TL;DR** The HUB keeps a small OKF catalog of source descriptions, routing signals, canonical
> URIs, and access capabilities. An agent selects a source semantically, resolves access for the
> current session, and reads it in place. External knowledge stays read-only and is referenced,
> never copied into the HUB.

## The boundary

| Location | Owns | Never owns |
|---|---|---|
| HUB `context/` | Team policy, local durable knowledge, canonical-source catalog | Copies of spoke, SharePoint, or vector-retrieved content |
| External source | Its own documents and history | HUB-specific team context |
| Agent session | Temporary retrieval and a discovered local checkout path | A persistent path registry or synchronized cache |

The catalog is an index, not a federation layer. A repository remote URL, SharePoint URI, or
retrieval endpoint stays stable even though every engineer's filesystem is different.

## One record per source

Records under `context/knowledge-sources/` are OKF v0.2 concepts. They describe what a source is,
the language that implies it, when it is and is not relevant, its canonical `resource` URI, the
native capability needed to read it, and its knowledge entrypoint when it has one.

The record does not claim that access is installed. It gives the agent enough information to
look for a matching local checkout or native connector and to explain what is missing when
neither exists.

## Resolution behavior

| Situation | Behavior |
|---|---|
| No catalog, empty catalog, or no credible match | Use HUB context only. |
| One credible match | Resolve and read the canonical source for this session. |
| Several credible matches | Surface the candidates; do not guess. |
| Matching local checkout | Verify its normalized git remote before using `rg`. Do not retain the path. |
| No local checkout | Use the declared native read capability when available. |
| No usable capability | Name the source and URI, explain the missing access, continue HUB-only where possible. |
| OKF source | Start at its declared index and progressively disclose documents. |
| SharePoint source | Search and read through the SharePoint capability. |
| Vector-backed source | Retrieve through the named capability and preserve underlying document provenance. |

Routing never authorizes writes to an external source, a clone into the HUB, or a local cache.

## Reference before capture

Before durable knowledge enters the HUB, decide where it is authoritative. HUB-canonical material
follows the normal proposal and approval gate. External-canonical material produces a concise
reference to the catalog record and canonical URI. Unclear authority becomes a question before a
write, not duplicated prose in two places.

## Setup

`/setup-awow` Step 6 offers to catalog external sources. It drafts records proposal-first, then
lands approved records in `context/knowledge-sources/`. Teams can add or retire records later
through the same governed context-write path.

## Sources of truth

- `context/tooling/knowledge-sources.md` — record profile and resolver contract.
- `context/knowledge-sources/index.md` — this team's registered sources.
- `.agents/skills/knowledge-source-routing/SKILL.md` — agent routing and capture behavior.
- `.agents/skills/adopting-okf/SKILL.md` — opt-in OKF adoption for an explicitly writable repo.
- `proposals/canonical-knowledge-source-routing-design.md` — accepted design and boundaries.

Companion guides: [setup & the plugin model](guide-setup-and-two-harnesses.md) — setup and
distribution; [the core delivery loop](guide-core-delivery-loop.md) — governed writes.
