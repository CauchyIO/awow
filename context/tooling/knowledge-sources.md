# Canonical knowledge sources — routing contract

`{HUB}/context/knowledge-sources/index.md` is the team-owned catalog of knowledge that is
canonical somewhere else: another repository, SharePoint, a vector-backed retrieval system,
or another provider with a native read capability. The HUB records how to find it, not its
contents.

## Source record

Store one OKF v0.2 concept document per source under `context/knowledge-sources/` and link it
from `index.md`. Use this profile:

```yaml
---
type: Project Repository
title: Payments platform
description: Engineering documentation for payment processing and settlement.
resource: https://github.com/example/payments-platform
tags:
  - payments
  - settlement
status: active
routing:
  aliases:
    - payments
    - pay platform
  signals:
    - payment processing
    - settlement jobs
  when_to_use:
    - Work concerns the payments platform or its operating procedures.
  when_not_to_use:
    - Work concerns team policy that is already canonical in this HUB.
source:
  kind: repository
  provider: github
access:
  capability: repository-read
  mode: read-only
knowledge:
  format: okf
  entrypoint: knowledge/index.md
---
```

`resource` is always the stable canonical URI. Never put a clone path, home-directory path,
workspace path, token, or credential in a record. `access.capability` names the kind of native
access an agent should look for; it is not a guarantee that every harness has it installed.
For vector-backed sources, the retrieval result must retain the URI of the underlying canonical
document. A vector index is a route to knowledge, not authority in its own right.

Require `type`, `title`, `description`, `resource`, `routing`, `source`, and `access`. `knowledge`
is optional; omit it when the provider's native navigation is the only entrypoint. Preserve any
other OKF lifecycle, trust, and provenance fields.

Keep the root index compact. Each linked entry has this shape:

```markdown
- [Payments platform](payments-platform.md) — Payment processing and settlement. Aliases:
  payments, pay platform. Signals: refunds, settlement jobs.
```

Use source-specific types and abstract capabilities. Typical pairs are `Project Repository` /
`repository-read`, `SharePoint Library` / `sharepoint-read`, and `Knowledge Index` /
`semantic-knowledge-search`. Provider names belong under `source.provider`; harness-specific tool
names do not belong in the catalog.

## Spoke records

When the resource is a repository this team governs as a spoke — the repo commits a connector
naming this HUB by remote URL and its sessions read team context from here — add one block:

```yaml
spoke:
  board:
    team: Payments            # board team the spoke's items land on
    project: Payments platform  # optional board project/container
  subpath: services/payments  # optional, monorepo scoping
  capabilities: [team]        # e.g. solo | team
```

`spoke:` adds governance metadata only; the rest of the record keeps its routing meaning, so a
spoke is also an ordinary routable read-only source. Records without `spoke:` are plain external
sources. Never put a clone path in a spoke record — the machine-local link lives in the spoke's
gitignored `.awow/hub.json`, written at registration by `/setup-awow`.

## Resolution

When a task consumes HUB context or may create durable HUB knowledge:

1. **Select semantically.** Read the catalog once. Compare the request, transcript, board item,
   and project vocabulary with each source's title, description, aliases, signals, and use
   boundaries. Zero credible matches means HUB-only behavior. One match activates that source.
   Several plausible matches are ambiguity: say which ones and do not guess.
2. **Resolve access for this session.** Prefer a matching local checkout only when its normalized
   git remote equals `resource`; discover it from the current workspace or other accessible
   workspace roots and never persist the path. Otherwise use the named provider capability or
   connector. If neither is available, report the canonical URI and missing capability. Do not
   clone, mirror, cache, or invent a path.
3. **Navigate in the source's own way.** For OKF, start at `knowledge.entrypoint`, follow indexes,
   then use `rg` when a verified local checkout is available. For SharePoint or vector-backed
   sources, use native search/read operations and preserve the canonical URI, ref/version, and
   path or object identifier the provider returns.

Retrieval is read-only and session-local. Never write to a source repo or external system while
acting from the HUB.

For repository identity, normalize away transport and syntax differences: compare host plus
owner/repository, ignoring credentials, an optional `.git` suffix, and a trailing slash. Search
only workspace roots the harness exposes; do not crawl an engineer's home directory. Several
matching checkouts are ambiguity, not permission to choose one silently.

## Reference before capture

Before proposing any durable HUB write, classify the material:

- **HUB-canonical** — write through the normal proposal and approval gate.
- **External-canonical** — write only a concise pointer to the source record and canonical URI;
  do not reproduce the source body.
- **Authority unclear** — ask which location is canonical before proposing a write.

Catalog changes are themselves governed team-context writes: draft the new or changed record,
show it to the user, and land it only after approval.

## Degraded behavior

- Missing catalog: retain current HUB-only behavior.
- Empty catalog or no match: retain current HUB-only behavior.
- Missing provider capability: name the source and URI, explain what access is unavailable, and
  continue with HUB context where possible.
- Broken entrypoint: use the canonical URI and native provider navigation; report the broken
  pointer rather than silently substituting another source.
- Unsupported OKF version: read ordinary Markdown where possible, but do not claim conformant
  traversal.
- Stale, deprecated, unverified, or conflicting material: retain the lifecycle signal, label the
  confidence limitation, and keep competing provenance separate.
