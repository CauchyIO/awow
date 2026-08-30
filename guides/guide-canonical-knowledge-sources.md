# Canonical knowledge sources

Route from shared team context to authoritative knowledge without copying that knowledge into
the anchor (this repo, which holds your team's shared context).

> **TL;DR** The anchor keeps a small catalog of source records (OKF — open knowledge-source
> format): source descriptions, routing signals, canonical URIs, and access capabilities. The
> agent picks the source that matches the question, works out how to reach it for this session,
> and reads it where it lives. External knowledge stays read-only and is referenced, never
> copied into the anchor.

## The boundary

| Location | Owns | Never owns |
|---|---|---|
| Anchor `context/` | Team policy, local durable knowledge, canonical-source catalog | Copies of content from anchored repos, SharePoint, or search indexes |
| External source | Its own documents and history | Anchor-specific team context |
| Agent session | What it fetched this session, plus any local clone it happened to find | A saved list of paths, or a synced copy |

The catalog just points at sources; it doesn't merge or serve their content. A repository
remote URL, SharePoint URI, or retrieval endpoint stays stable even though every engineer's
filesystem is different.

## One record per source

Each file under `context/knowledge-sources/` describes one source, using OKF v0.2. It records
what the source is, the words that suggest it's relevant, when it applies and when it doesn't,
its canonical `resource` URI, which tool or connector can read it, and where to start reading
when it has one.

The record does not claim that access is installed. It gives the agent enough information to
look for a matching local checkout or native connector and to explain what is missing when
neither exists.

## Resolution behavior

| Situation | What the agent does |
|---|---|
| No catalog, empty catalog, or no credible match | Falls back to anchor context only. |
| One credible match | Resolves and reads the canonical source for this session. |
| Several credible matches | Lists the candidates and asks rather than guessing. |
| Matching local checkout | Checks the clone's git remote matches the record before searching it. Uses it for this session only; doesn't remember the path. |
| No local checkout | Uses the declared native read capability when available. |
| No usable capability | Names the source and URI, explains the missing access, and continues anchor-only where possible. |
| OKF source | Starts at the source's declared index and opens further documents only as needed. |
| SharePoint source | Searches and reads through the SharePoint capability. |
| Vector-backed source | Retrieves through the named capability and preserves underlying document provenance. |

Routing never writes to an external source, clones it into the anchor, or caches it locally.

## Reference before capture

Before durable knowledge enters the anchor, decide where it is authoritative. Material whose
authoritative home is the anchor goes through the usual propose-then-approve step (see the
[core delivery loop](guide-core-delivery-loop.md)). External-canonical material produces a
concise reference to the catalog record and canonical URI. When it's unclear who owns the
material, the agent asks before writing rather than keeping two copies.

## Setup

`/setup-awow` Step 6 offers to catalog external sources. It drafts the records for you to
review, then writes the approved ones to `context/knowledge-sources/`. Teams can add or retire
records later through the same review-then-write process.

## Sources of truth

- `context/tooling/knowledge-sources.md` — record profile and resolver contract.
- `context/knowledge-sources/index.md` — this team's registered sources.
- `.agents/skills/knowledge-source-routing/SKILL.md` — agent routing and capture behavior.
- `.agents/skills/adopting-okf/SKILL.md` — opt-in OKF adoption for an explicitly writable repo.
- `proposals/canonical-knowledge-source-routing-design.md` — accepted design and boundaries.

Companion guides: [setup & the plugin model](guide-setup-and-two-harnesses.md) — setup and
distribution; [the core delivery loop](guide-core-delivery-loop.md) — governed writes.
