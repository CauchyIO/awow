---
name: knowledge-source-routing
description: "Use when a task reads shared ANCHOR context, mentions another repository or external knowledge system, or may capture durable knowledge whose canonical source could be elsewhere."
---

# Route canonical knowledge

Treat `{ANCHOR}/context/knowledge-sources/index.md` as a semantic routing catalog, not a content
store. Read `{ANCHOR}/context/tooling/knowledge-sources.md`, falling back to
`${CLAUDE_PLUGIN_ROOT}/context/tooling/knowledge-sources.md`, for the record profile and full contract.

## Route

1. Read the catalog once per task. Match the task's nouns, systems, projects, and intent against
   source titles, descriptions, aliases, signals, and use boundaries.
2. With no credible match, remain ANCHOR-only. With one match, use it. With several plausible
   matches, surface the ambiguity; do not choose by filename or catalog order.
3. Resolve access only for this session. A local checkout is valid only after its normalized git
   remote matches the record's canonical `resource`. Otherwise use the named native connector or
   provider capability. Never persist a local path and never clone, mirror, or cache the source.
4. Navigate with the source's declared knowledge format: OKF entrypoint and indexes, SharePoint
   native search, or vector retrieval that preserves underlying canonical provenance. Retain the
   canonical URI, ref/version, and path or object identifier when available.

External sources are read-only. Never write back to an anchored repo, SharePoint, vector store,
or other canonical system while acting from the ANCHOR.

## Capture

Before any durable ANCHOR write, decide where the fact is canonical. Write ANCHOR-canonical knowledge
through the normal gate. For external-canonical knowledge, store only a concise reference to the
catalog record and canonical URI. If authority is unclear, ask before proposing the write.

## Stop conditions

- Missing or empty catalog: proceed ANCHOR-only.
- Missing access capability: report the source, URI, and missing capability; continue with ANCHOR
  context where useful.
- Broken OKF entrypoint: report it and use only navigation the canonical provider exposes.
- Unsupported OKF version: use ordinary Markdown when possible without claiming conformant
  traversal.
- Stale, deprecated, unverified, or contradictory results: label the limitation and keep each
  source's provenance separate.
- Any access path that would require copying content into the ANCHOR or writing externally: stop.
