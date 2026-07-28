# awow on Microsoft 365 Copilot — harness design

- **Date:** 2026-07-15 · revised 2026-07-16 after review
- **Status:** Draft (design spec — pre-board). Promote to a `meta/proposals/` entry before any build begins, per AGENTS.md's proposal-first reflex.
- **Related:** `meta/proposals/hub-and-spoke-adoption.md`, `meta/proposals/pi-codex-harness-support.md`, `context/tooling/harnesses/README.md`, `tools/gather.py`

## 1. Problem

awow's commands and skills work because an agent reads a small pointer file, then **deterministically opens the exact `context/` markdown file it links to on demand** ("re-read the source each time — the cache can drift"). Microsoft 365 Copilot has no equivalent primitive: its extensibility surfaces are declarative agents (inline `instructions` + *knowledge sources* + *actions*), Copilot Studio, and Graph/API connectors. Grounding there is RAG retrieval, and a declarative agent cannot run scripts, touch git, or execute the board mechanics many awow commands assume.

We want awow to work for a specific population that today's harnesses don't reach.

## 2. Target user & scope (decided)

- **Users:** non-technical, **no repo**. M365 Copilot is their only surface onto awow. Relative markdown links are meaningless to them.
- **Goal:** **execute the workflows** — a work item actually appears on the board, a KB entry actually lands — not merely advisory Q&A.
- **State substrate:** **Azure DevOps / Jira** for board state. **KB entries and proposals stay in git**: the agent writes them into the hub's `kb-inbox/` through a write action (§4.2), so there is exactly one KB — the same one repo-side agents ground on. SharePoint holds no authoritative awow content.
- **Build appetite:** whatever a faithful port needs.

### Non-goals

- Porting repo-hygiene / telemetry machinery (git commits by users, MLflow/session export, hook scans, public-repo leak guard). These have no meaning in a Copilot chat agent and are **excluded**.
- Making SharePoint (or any indexed store) a source of truth. **Git remains the sole SSOT** (§4).
- A 1:1 mirror of every command. This is a **port of the board / KB / proposal subset** (inventory in §5).

## 3. Architecture — phased 1 → 2

A new **`m365` harness** in awow's existing fan-out model. `.agents/` + `context/` stay the single source of truth; `gather.py --surface m365` renders them into an M365 Copilot **declarative agent** package. Non-technical users are *assigned* the agent (they don't self-install); it grounds on awow's conventions and executes board/KB workflows by calling ADO/Jira APIs and the git inbox action.

- **Phase 1 — declarative agent** (gather-emitted): grounding + conversation starters + single-call actions. Covers the advisory + simple-mutation commands, which is most of the daily value.
- **Phase 2 — Copilot Studio escalation** (later): the genuinely branchy pipelines move to Studio/Power Automate flows invoked as actions.

## 4. The two primitive swaps — and how git stays SSOT

### 4.1 `context/` access — runtime fetch, zero copy

awow commands already name **exact files** ("read `context/knowledge-base/mining.md`"), which maps onto an on-demand fetch far better than fuzzy RAG.

- **Primary mechanism — a `fetchAwowContext(path)` API action.** The declarative agent reads the exact markdown **live from git** each time it needs it. This reproduces link-following **1:1** and keeps the "re-read the exact source each time" contract. **There is no copy anywhere** — git is unambiguously the only source.
- **The file-index manifest replaces the links.** `gather.py --surface m365` emits, into the agent instructions, a generated index of fetchable paths (path + one-line description). That manifest is what tells the agent *what exists and when to fetch it* — the structural replacement for markdown links.
- **Fidelity caveats (mitigated, not ignored).** Action responses are size-capped, and a truncated file the model silently summarizes would break the contract. `fetchAwowContext` therefore supports an optional heading-scoped read (`path` + section anchor) so large files return in faithful chunks. Fetch latency and git-host rate limits are absorbed by short-TTL caching in the endpoint (§4.1a) — a transient cache, never a store.
- **Optional augmentation — a git-fed Graph connector** for fuzzy "what does awow say about X?" discovery only. It is a **derived, one-way index in the same category as the `.claude/`/`.github/` stubs**: regenerated from git on every merge, never human-edited, no browsable SharePoint library. It is a cache of git, not a peer to it. It can be dropped entirely — the fetch action alone is complete (D7).

#### 4.1a The fetch/write endpoint is critical-path, not plumbing

For the actual adopter population the hub repo is **private**, so a **thin auth endpoint in front of git is the default deployment**, not the fallback — and it is the only new *hosted* component in the entire design, so it gets first-class treatment:

- **Per-tenant artifact.** Each adopter runs one; `gather --surface m365` stamps its base URL into the emitted action specs.
- **Credential:** a read-scoped (plus inbox-write-scoped, §4.2) git-host credential — a GitHub App installation or equivalent — held by the endpoint, never by the agent.
- **Path allow-list:** serves `context/`, `.agents/`, and `kb-inbox/` writes only; everything else 403s.
- **Caching:** short-TTL read cache for latency and rate-limit absorption.
- Direct, unproxied git-host API calls are the special case for **public** hubs only (D5 covers the hosting/credential shape).

### 4.2 KB & proposal writes — the git inbox action

The write half of the KB contract mirrors the read half. A **`commitAwowInbox(path, content)` action** (same endpoint as §4.1a) writes a markdown capture into the hub's **`kb-inbox/`** — KB candidates and proposal drafts alike — as a commit or PR. Attribution: the signed-in user's identity where the git host supports delegated authoring, else the endpoint's credential commits with the user's UPN stamped in the entry frontmatter.

This is the load-bearing move that keeps **one KB**: M365-originated captures land in the *same inbox* `/kb-synthesize` already drains, so the existing human gate reviews them before anything is promoted to `context/knowledge-base/`. Nothing KB-shaped is ever written to SharePoint. Board mutations, by contrast, go straight to ADO/Jira (§4.3) — board state was never git's to hold.

### 4.3 commands/skills → instructions + conversation starters + actions

- The "slash command" surface becomes **conversation starters** — one per ported command (≤ 12; the schema cap *is* the port budget).
- The instruction block does **not** inline command procedures — it can't (§5 size math). It carries the agent's identity, the small set of load-bearing `REQUIRED` convention lines, and a **routing manifest**: starter → playbook path. On invocation the agent **fetches the playbook via §4.1 and follows it** — which is exactly the pointer-file-then-open pattern awow already runs on every other harness. If the fetch fails, the command **stops loudly**; it never improvises the procedure from model memory.
- Each command's mutating steps become **OpenAPI actions** against ADO/Jira (board) and the git inbox (§4.2). Copilot renders its **built-in confirmation card before any write operation** (per-operation, declared in the plugin manifest) — that card is the Phase-1 approval gate.

## 5. Phase 1 — declarative agent (gather-emitted)

**Hard limits (declarative agent manifest schema v1.7 — this resolves D1):** `instructions` ≤ **8,000 characters**; `conversation_starters` ≤ **12**; `actions` = 1–10 plugin manifests (each plugin may carry many operations). Consequences: playbooks are always fetched, never inlined (§4.3); the inline budget is identity + `REQUIRED` lines + routing/file-index manifest, and gather **fails the build** if the assembled instructions exceed the cap rather than silently truncating.

`gather.py --surface m365` emits a Teams app package under `dist/m365/`:

- `appPackage/manifest.json` + `appPackage/declarativeAgent.json` — name, description, **instructions** (assembled per the budget above), `conversation_starters` (one per ported command), and capability / knowledge / action references.
- `actions/*.json` — OpenAPI plugin specs: `fetchAwowContext` + `commitAwowInbox` (§4.1–4.2) plus the ADO/Jira board operations, write operations flagged for confirmation cards.
- (Optional) Graph-connector ingestion config for the derived discovery index (§4.1, D7).

### Phase-1 command inventory (the port list)

| Command | Conversation starter | Action bindings | Notes |
|---|---|---|---|
| `my-work` | "What does the board need from me?" | `board.query` | read-only |
| `daily-checkin` | "Check in my day" | `board.query`, `board.update`, `board.comment` | plan first, then confirmation-carded writes |
| `refinement-prep` | "Draft a feature for the next refinement" | `board.createWorkItem` | gated write |
| `kb-mine` | "Capture today's durable knowledge" | `commitAwowInbox` | lands in the hub `kb-inbox/` (§4.2) |
| `daily-digest` | "What happened across the team today?" | `board.query` | advisory |
| `weekly-digest` | "How did this week trend?" | `board.query` | advisory |
| `cross-team-view` | "Where do the teams intersect?" | `board.query` | advisory |
| `solution-design-flow` (capture mode) | "Capture this design discussion" | `commitAwowInbox` | proposal draft → inbox |
| `project-plan` | "Publish the project plan" | `board.createWorkItem` (batch) | gated write |

9 starters of the 12-cap — headroom for two or three additions before the budget forces a cut.

**Phase 2 (Studio):** `daily-routine`, `kb-synthesize`, `process-transcript`, `process-retro`, `project-manager` — the branchy, multi-gate pipelines (§6).

**Excluded** (default `include: false`): `setup-awow`, `update-awow`, `test-setup-awow`, `awow-add`/`awow-reset`/`awow-status`, `board-skill`, `design-system`, `artifact`, `coaching-review`, `process-workitem` (produces a PR — repo work), and all telemetry/export skills.

### DRY mechanism — one source, many surfaces

A new optional per-command frontmatter block, `m365:`, tells gather how to render each command onto the M365 surface:

```yaml
m365:
  include: true            # default false — repo-only commands drop out automatically
  conversation_starter: "Run my daily routine"
  action_bindings: [ado.createWorkItem, git.commitAwowInbox]
```

Default `include: false`, so repo-only commands are excluded without per-command edits. This keeps `.agents/` canonical and consistent with the existing stub philosophy. The §5 inventory table is the initial `include: true` set.

## 6. Phase 2 — Copilot Studio escalation (later)

The branchy pipelines — `daily-routine` (gather → mine → route → synthesize), `kb-synthesize` (plan → approve → promote), and the transcript/retro processors — get reimplemented as **Copilot Studio / Power Automate flows** invoked by the declarative agent as actions. Their multi-step approval gates become **adaptive-card confirmations**, the same interaction shape users already know from Phase 1's built-in write-confirmation cards. Everything else stays in the Phase-1 declarative agent.

## 7. Prerequisites (adoption gates, stated honestly)

- **Licensing:** every target user needs an M365 Copilot seat (or the tenant allows metered usage) — declarative agents with capabilities beyond web search require it. For this population that is the single largest adoption gate.
- **Tenant admin:** the app package is deployed and *assigned* centrally (D6); users never self-install.
- **First-use consent:** each action prompts a per-user consent card on first invocation. Onboarding material must walk through this — for non-technical users an unexplained consent prompt is where the funnel dies.
- **Identity plumbing:** an app registration for the delegated OAuth to ADO/Jira (§9 D2), and the fetch/write endpoint deployment (§4.1a) for private hubs.

## 8. Known fidelity losses (accepted)

1. Retrieval/discovery is weaker than link-following for *broad* questions (mitigated: exact-file fetch for named files; optional Graph connector for fuzzy discovery).
2. No git versioning of **board** state — ADO/Jira versioning instead. (`context/` *and the KB* stay git-versioned; §4.2 keeps KB writes in git.)
3. Only board/KB/proposal commands port; repo-hygiene/telemetry machinery does not.
4. Every command invocation costs one playbook fetch (latency), and a fetch failure blocks the command — by design: fail loud, never run a half-remembered procedure.
5. Approval gates render as confirmation/adaptive cards, not proposals-in-PR.
6. Large-file reads are chunked by section (§4.1) rather than delivered whole.

## 9. Decisions

**Decided:**

- **D1 — Instruction size cap: resolved.** 8,000 chars / 12 starters / 10 action plugins (schema v1.7); the inline-vs-fetch triage in §4.3–§5 is designed to those numbers, and gather enforces the cap at build time.
- **D2 — Action identity: delegated OAuth.** The goal sentence ("a work item actually appears") implies *attributed* board writes; a service principal writing as everyone is a governance non-starter for board admins. A service credential exists only inside the §4.1a endpoint, for git.
- **D4 — Approval-gate UX: resolved.** Phase 1 uses Copilot's built-in per-operation write-confirmation cards; Phase-2 Studio flows use adaptive cards of the same shape.

**Open:**

- **D3 — ADO or Jira first.** Build the action layer against one; abstract later. (Leaning ADO: the target population is by definition an M365 shop.)
- **D5 — Endpoint hosting & credential shape.** The endpoint itself is decided (§4.1a, default-on for private hubs); open is where it runs (Azure Functions vs. container vs. adopter-managed) and the exact git-host credential (GitHub App vs. fine-grained PAT vs. ADO-repos equivalent).
- **D6 — Distribution.** Teams admin assignment vs. Copilot Studio publish; users don't self-install.
- **D7 — Graph connector: in or out for v1.** Default **out** — the fetch action is complete without it.

## 10. Validation

- `gather --check` extended with an **m365 drift guard** (same as today's stub guard), including the instruction-size cap check.
- A **grounding smoke test**: canonical question → expected-answer set that measures fetch/retrieval fidelity.
- **Action contract tests** against an ADO/Jira sandbox.
- An **end-to-end scenario suite** — the regression floor, mirroring `tests/harness/`: a scripted conversation per Phase-1 command (M365 Agents Toolkit test harness) asserting the *terminal side effect*, not the transcript — the work item exists in the sandbox board with the expected fields; the KB capture landed in a fixture hub's `kb-inbox/`. Contract tests prove the API works; only this suite proves the *agent invokes it correctly*, which is where declarative agents actually fail.
- A **pilot before broad assignment**: a small group of real target users. Technical validation cannot falsify the core claim ("non-technical users execute the workflows") — only a pilot can.

## 11. New / changed artifacts

- `tools/gather.py` — add the `--surface m365` render target + instruction-size build gate.
- `context/tooling/harnesses/m365-copilot.md` — harness doc (join the supported-harness table).
- Per-command `m365:` frontmatter for the §5 inventory set.
- `context/tooling/m365/` — M365 config: fetch/write action + OpenAPI templates, instruction-triage policy, conversation-starter/manifest generation rules.
- **The fetch/write endpoint** (§4.1a): deploy template + operator doc — the one hosted component.
- `tests/harness/m365/` — the §10 end-to-end scenario suite, joining the existing harness matrix.
- A knowledge/connector-sync CI workflow (only if D7 = in).
- This spec (promote to `meta/proposals/` before build — §2 status).

## 12. Source-of-truth invariant

`.agents/` + `context/` in git are the **only** authoritative source. Every M365 artifact — instructions, conversation starters, file-index manifest, and any Graph-connector index — is a **generated, one-way derivation** regenerated by `gather.py` and CI on merge. Nothing on the M365 side is ever hand-edited, and nothing on it is authoritative. This is the same "generated stubs, never drift" contract awow already enforces for `.claude/` and `.github/`, extended to a new surface.

The single deliberate flow in the *other* direction is the §4.2 inbox write (M365 → git) — and it lands in `kb-inbox/` precisely so the existing human synthesis gate reviews it before anything becomes durable knowledge.
