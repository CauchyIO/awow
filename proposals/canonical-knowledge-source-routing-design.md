# Design — canonical knowledge-source routing: reference before capture

**Status:** Accepted — Markdown-first MVP implemented on 2026-08-06.
**Scope:** Make awow sessions discover and read relevant canonical knowledge outside the hub without copying it into the hub. Repository spokes are one source kind; SharePoint, vector-backed retrieval, and other native knowledge systems follow the same routing contract.
**Inputs:** [`hub-and-spoke-design.md`](hub-and-spoke-design.md), the existing `overnight` OKF project-map implementation, the unmerged `adopting-okf` v0.1 skill on `linear`'s `casper/okf-adoption-skill` branch, and the [Open Knowledge Format v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md).

---

## 1. Outcome

An awow session reads a compact catalog from `{HUB}`, recognizes when the conversation or current command relates to one or more external canonical sources, and follows the appropriate read-only access capability. The session progressively loads only relevant material and retains source provenance.

The hub remains the canonical home for this team's own context. It stores routing metadata and references to other canonical systems; it never mirrors their content.

This is **canonical-source routing**, not repository federation. It does not synchronize sources, own their lifecycle, or write back to them.

## 2. Ratified principles

### 2.1 Reference before capture

Before any flow proposes durable knowledge under `{HUB}`, it checks the source catalog. When the material already has another canonical home, the hub records a reference and the team-specific reason it matters; it does not reproduce the source material.

Hub content is allowed when the knowledge is genuinely hub-specific: team conventions, local decisions, local rationale, ownership, or synthesis that does not already have a canonical external home.

### 2.2 No external content custody

The routing capability never:

- copies or mirrors external source content into `{HUB}`;
- clones a repository to obtain knowledge;
- persists a user's local repository path;
- builds a synchronized cache that becomes a second knowledge store; or
- writes to a repository spoke, SharePoint, vector index, or any other external source.

Retrieved content is session input only. A source-specific connector may maintain its own implementation cache, but awow does not create, govern, or treat that cache as canonical.

### 2.3 Native access, common routing

The catalog uses one source-neutral routing profile. Each source is read through its native capability:

- a repository through the current matching workspace or a repository read API;
- an OKF-enabled repository through its declared bundle entry point;
- SharePoint through a SharePoint connector or skill;
- a vector-backed knowledge service through its query capability; and
- another system through the capability named by its catalog record.

The catalog declares what is needed; it does not embed harness-specific tool names or credentials.

### 2.4 Provenance reaches the authority

A retrieved claim carries its canonical resource, ref/version when available, and path or object identifier. A vector database is normally an access index rather than an authority: results must preserve links to their underlying canonical documents when the service exposes them. If it cannot, the session labels that limitation rather than presenting the index as primary evidence.

## 3. Three independent resolvers

The design separates three questions that should not be collapsed into one helper:

```text
Canonical-source resolver
  Which source is relevant to this conversation or command?
                |
                v
Access resolver
  Which available read capability can reach that source?
                |
                v
Knowledge resolver
  Which material inside that source answers the current need?
```

### 3.1 Canonical-source resolver

`{HUB}/context/knowledge-sources/index.md` is a compact OKF index. The shared `using-awow` reflex reads it at the first HUB-context use in a task. Its entries expose the title, one-line description, aliases, and routing signals for each source without loading the source records or their contents.

As the session evolves, the agent maintains zero or more active sources:

- an explicit source or project name is strong evidence;
- one uniquely strong implied match activates and is disclosed;
- ambiguous matches are surfaced at the next natural command gate, or through one blocking clarification when no gate exists; and
- multiple clear matches may be active without merging their provenance.

The source resolver is semantic agent judgment. A deterministic script may validate and render the catalog, but it does not decide what a conversation means.

### 3.2 Access resolver

The agent inspects the current repository and harness-exposed workspace roots for a matching normalized remote identity. It does not scan the wider filesystem without permission and it does not remember discovered paths.

If no matching exposed workspace is present, the agent invokes the catalogued native read capability. For a repository this is an authenticated contents/code-search API where available, not a clone. For SharePoint or a knowledge service it is the relevant connector or skill.

If the capability is absent or access fails, the session keeps the catalog summary, names the unavailable source and capability, and continues at reduced confidence. It may explain how the user can make the capability available, but it does not create local or external state.

### 3.3 Knowledge resolver

For an OKF-enabled repository, `knowledge.entrypoint` identifies the bundle root `index.md`. The agent follows its descriptions and links progressively, fetching raw Markdown by exact path when the source is remote. When the repository is the current workspace, normal local tools such as `rg` remain available. Provider-native code search may support a broader remote query; the router never clones merely to gain grep.

Other source kinds keep their native knowledge resolver. SharePoint search and vector similarity are valid retrieval mechanisms even though the underlying corpus is not converted to OKF.

OKF is therefore the resolver *inside participating repositories* and the metadata envelope for hub catalog records. It is not the filesystem, network, authentication, or universal query protocol.

## 4. Hub catalog profile

The catalog is team data and has no `{AWOW_ROOT}` fallback. It lives at:

```text
{HUB}/context/knowledge-sources/
  index.md
  <source-slug>.md
```

Each source record is an OKF v0.2 concept. OKF's standard fields retain their standard meaning; `routing`, `source`, `access`, and `knowledge` are awow profile extensions.

```yaml
---
type: Project Repository
title: Payments Platform
description: Payment authorization, settlement, refunds, and ledger integration.
resource: https://github.example/acme/payments
tags: [payments, checkout, settlement, ledger]
status: stable
routing:
  aliases: [paycore, transaction service]
  signals: [refund orchestration, payment authorization, settlement]
  when_to_use: Work concerns the payments platform or one of its owned domains.
  when_not_to_use: Work only concerns generic finance policy owned in SharePoint.
source:
  kind: repository
  provider: github
access:
  capability: repository-read
knowledge:
  format: okf
  entrypoint: knowledge/index.md
---
```

Profile requirements:

- `type`, `title`, `description`, `resource`, `routing`, `source`, and `access` are required.
- `resource` is the canonical URL or URI. For repositories it is the remote URL, never a local path.
- `routing` contains only discovery signals, not copied source knowledge.
- `access.capability` is a stable abstract capability, resolved to the tools available in the current harness.
- `knowledge` is optional. Repository sources use it when they expose a structured entry point such as OKF.
- OKF lifecycle, provenance, and trust fields remain available and are honored by consumers.
- The generated `index.md` is the session-start surface; source records are loaded only after a plausible match.

Example non-repository records use the same envelope:

- `type: SharePoint Library`, `source.kind: document-system`, `access.capability: sharepoint-read`;
- `type: Knowledge Index`, `source.kind: retrieval-index`, `access.capability: semantic-knowledge-search`.

The record for a retrieval index states whether results provide underlying canonical-resource links.

## 5. Components and lifecycle

### 5.1 OKF adoption capability

Update and land the existing `adopting-okf` prior art against OKF v0.2. It formats existing repository documentation as a bundle, preserves tool-consumed frontmatter and document bodies, requires a conformance and freshness review, and exposes a stable root index.

Adoption does not invent missing documentation. A documentation-poor repository first gets a separately approved enrichment pass, one concept per subsystem or bounded context rather than a file-tree mirror.

### 5.2 Catalog management capability

Setup creates the empty catalog skeleton. Adding or changing a source is a governed `{HUB}` context write: draft the source record, show its routing metadata and placement, obtain approval, then update the compact index. The flow reviews the canonical URI and declared capability without copying any source material.

### 5.3 Shared routing reflex

`using-awow` owns the session-wide contract, so individual commands do not implement private routing algorithms. Claude Code, Codex, and Pi receive the same canonical reflex through their existing delivery surfaces.

Commands still read their explicit `{HUB}` files. Routed sources supplement those reads; they do not replace team context or command contracts.

### 5.4 Reference-before-capture seam

Every flow that proposes or performs a durable hub knowledge write consults the relevant active sources and catalog candidates before its approval gate. It classifies the result as one of:

- **hub-canonical** — write the team-specific knowledge to the proposed hub location;
- **external-canonical** — record or present the canonical reference plus local relevance, without copying content; or
- **uncertain authority** — surface the competing candidates and defer capture until a human decides.

This applies to transcript processing, solution design, knowledge mining/synthesis, context updates, and future hub-writing flows through one shared rule rather than repeated prose.

## 6. Precedence and trust

- Hub conventions and governance are authoritative for how the team works.
- A routed source is authoritative for facts within its declared domain.
- A catalog record is authoritative only for routing metadata, not for the source's substantive content.
- A matching current workspace is a session view; branch and dirty-state differences are disclosed when they affect authority.
- External lifecycle and trust signals are retained. Deprecated, stale, or unverified material receives an explicit confidence label rather than silent rejection.
- Contradictions are shown with both sources and their provenance. The router never silently blends them.

## 7. Failure behavior and safety

- **No catalog:** preserve today's awow behavior.
- **No source match:** stay hub-only without catalog noise.
- **Ambiguous match:** do not guess; use the next natural gate or one blocking clarification.
- **Missing capability or authentication:** keep the source pointer, name what is unavailable, and continue at reduced confidence.
- **Missing repository OKF entry point:** report that the repository is registered but the declared knowledge bundle is unavailable.
- **Unsupported OKF version:** read ordinary Markdown where possible, but do not claim conformant traversal.
- **Broken OKF link:** tolerate, skip, and report it as permitted by the specification.
- **Retrieval result without underlying provenance:** label the retrieval service as the available source and state that primary provenance was not supplied.
- **Conflicting material:** apply the precedence rules and surface the conflict.

All routed access is read-only. No error path authorizes a clone, mirror, external edit, or fallback copy into the hub.

## 8. MVP scope

The MVP proves the shared routing seam without creating a new content platform:

1. Define the awow OKF v0.2 source-record profile in the shared routing contract.
2. Provide a compact, human-maintained catalog index whose entries expose only routing metadata.
3. Update the `using-awow` reflex with source discovery, confidence, provenance, and degradation rules.
4. Land the updated `adopting-okf` capability for participating repositories.
5. Define repository/OKF traversal through available local or remote read capabilities.
6. Allow SharePoint and vector-backed records to route to installed native capabilities without embedding their content or provider logic into the catalog.
7. Centralize the reference-before-capture seam in the injected reflex so current and future HUB-writing flows inherit it.
8. Render and verify the same behavior across Claude Code, Codex, and Pi.

The MVP does not:

- host, index, embed, copy, mirror, clone, or synchronize external content;
- edit or write back to any external canonical source;
- replace provider authentication or guarantee every declared capability is installed;
- make all external systems conform to OKF;
- implement a universal query language; or
- expand into version-pinned, multi-upstream repository federation.

## 9. Verification

### 9.1 Deterministic checks

- Validate both skill manifests.
- Classify the routing contract as payload and the source catalog as HUB team data.
- Regenerate and drift-check Claude Code, Codex, Pi, opencode, and Copilot surfaces.
- Run the existing path-token, context-write, packaging, and harness-wiring suites.

The MVP deliberately adds no parser, generator, daemon, local registry, or retrieval code. Those
would automate Markdown that agents can already read and write, while adding a second behavior
surface to keep consistent. Add deterministic catalog tooling only after real usage demonstrates
a recurring structural failure it would prevent.

### 9.2 Behavioral acceptance

Exercise these cases during real usage and add synthetic fixtures when repeated failures justify
the extra surface:

1. First HUB-context use loads only compact catalog descriptions.
2. Explicit and implied terms activate the intended source.
3. Ambiguity is surfaced rather than guessed.
4. Multiple sources remain provenance-separated.
5. Repository knowledge is traversed through OKF without copying it.
6. SharePoint-like and vector-like records dispatch to their declared capability.
7. Vector results retain underlying canonical references when supplied.
8. Missing access degrades to a pointer and precise explanation.
9. A proposed hub capture becomes a reference when another source is canonical.
10. Representative transcript, solution-design, work-item, and knowledge flows use the shared routing contract without command-specific matching code.
11. Claude Code, Codex, and Pi behave consistently.
12. A final diff and filesystem assertion finds no retrieved source body, discovered local path, clone, or external write artifact in the hub fixture.

### 9.3 Success criterion

An engineer can begin in the hub, imply a domain or project in ordinary conversation, and receive relevant, provenance-bearing knowledge from the appropriate canonical source. The hub gains only the routing metadata and local context it legitimately owns.

## 10. Relationship to existing awow work

- This extends the hub-and-spoke identity model from one spoke-to-hub link into read-only hub-to-canonical-source discovery; it does not revive the parked federation scope.
- The current transcript router is a useful acceptance case, not the implementation home.
- `using-awow` is the cross-command implementation home for session discovery.
- The `overnight` OKF bundle and navigation script are implementation prior art, not content to vendor.
- The landed `adopting-okf` skill is the OKF v0.2 reconciliation of that prior art.
