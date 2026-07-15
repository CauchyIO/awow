# awow on Microsoft 365 Copilot — harness design

- **Date:** 2026-07-15
- **Status:** Draft (design spec — pre-board). Promote to a `meta/proposals/` entry before any build begins, per AGENTS.md's proposal-first reflex.
- **Related:** `meta/proposals/hub-and-spoke-adoption.md`, `meta/proposals/pi-codex-harness-support.md`, `context/tooling/harnesses/README.md`, `tools/gather.py`

## 1. Problem

awow's commands and skills work because an agent reads a small pointer file, then **deterministically opens the exact `context/` markdown file it links to on demand** ("re-read the source each time — the cache can drift"). Microsoft 365 Copilot has no equivalent primitive: its extensibility surfaces are declarative agents (inline `instructions` + *knowledge sources* + *actions*), Copilot Studio, and Graph/API connectors. Grounding there is RAG retrieval, and a declarative agent cannot run scripts, touch git, or execute the board mechanics many awow commands assume.

We want awow to work for a specific population that today's harnesses don't reach.

## 2. Target user & scope (decided)

- **Users:** non-technical, **no repo**. M365 Copilot is their only surface onto awow. Relative markdown links are meaningless to them.
- **Goal:** **execute the workflows** — a work item actually appears on the board, a KB entry actually lands — not merely advisory Q&A.
- **State substrate:** **Azure DevOps / Jira** for the board; SharePoint or a wiki for KB entries and proposals. (`context/` itself stays in git — see §4.)
- **Build appetite:** whatever a faithful port needs.

### Non-goals

- Porting repo-hygiene / telemetry machinery (git commits, MLflow/session export, hook scans, public-repo leak guard). These have no meaning in a Copilot chat agent and are **excluded**.
- Making SharePoint (or any indexed store) a source of truth. **Git remains the sole SSOT** (§4).
- A 1:1 mirror of every command. This is a **port of the board / KB / proposal subset**.

## 3. Architecture — phased 1 → 3

A new **`m365` harness** in awow's existing fan-out model. `.agents/` + `context/` stay the single source of truth; `gather.py --surface m365` renders them into an M365 Copilot **declarative agent** package. Non-technical users are *assigned* the agent (they don't self-install); it grounds on awow's conventions and executes board/KB workflows by calling ADO/Jira/SharePoint APIs.

- **Phase 1 — declarative agent** (gather-emitted): grounding + conversation starters + single-call actions. Covers the advisory + simple-mutation commands, which is most of the daily value.
- **Phase 3 — Copilot Studio escalation** (later): the genuinely branchy pipelines move to Studio/Power Automate flows invoked as actions.

## 4. The two primitive swaps — and how git stays SSOT

### 4.1 `context/` access — runtime fetch, zero copy

awow commands already name **exact files** ("read `context/knowledge-base/mining.md`"), which maps onto an on-demand fetch far better than fuzzy RAG.

- **Primary mechanism — a `fetchAwowContext(path)` API action.** The declarative agent reads the exact markdown **live from git** (GitHub API, or a thin auth proxy for a private repo) each time it needs it. This reproduces link-following **1:1** and keeps the "re-read the exact source each time" contract. **There is no copy anywhere** — git is unambiguously the only source.
- **The file-index manifest replaces the links.** `gather.py --surface m365` emits, into the agent instructions, a generated index of fetchable paths (path + one-line description). That manifest is what tells the agent *what exists and when to fetch it* — the structural replacement for markdown links.
- **Optional augmentation — a git-fed Graph connector** for fuzzy "what does awow say about X?" discovery only. It is a **derived, one-way index in the same category as the `.claude/`/`.github/` stubs**: regenerated from git on every merge, never human-edited, no browsable SharePoint library. It is a cache of git, not a peer to it. It can be dropped entirely — the fetch action alone is complete.

**Result:** git is the sole SSOT. No SharePoint document library that humans edit; no second authoritative store.

### 4.2 commands/skills → instructions + conversation starters + actions

- The "slash command" surface becomes **conversation starters** — one per ported command.
- Each command's procedure becomes an **instruction playbook block**. Load-bearing `REQUIRED` conventions are **inlined** into instructions (not left to retrieval); everything else is fetched on demand via §4.1.
- Each command's mutating steps become **OpenAPI actions** against ADO/Jira (board) and SharePoint/wiki (KB, proposals): create work item, query board, comment, transition, add KB entry, draft proposal.

## 5. Phase 1 — declarative agent (gather-emitted)

`gather.py --surface m365` emits a Teams app package under `dist/m365/`:

- `appPackage/manifest.json` + `appPackage/declarativeAgent.json` — name, description, **instructions** (assembled: trimmed AGENTS.md rules + inlined `REQUIRED` conventions + the file-index manifest + triaged command playbooks, fit to the instruction size cap — **D1**), `conversation_starters` (one per ported command), and capability / knowledge / action references.
- `actions/*.json` — OpenAPI plugin specs: `fetchAwowContext` plus the ADO/Jira/SharePoint board ops.
- (Optional) Graph-connector ingestion config for the derived discovery index (§4.1).

### DRY mechanism — one source, many surfaces

A new optional per-command frontmatter block, `m365:`, tells gather how to render each command onto the M365 surface:

```yaml
m365:
  include: true            # default false — repo-only commands drop out automatically
  conversation_starter: "Run my daily routine"
  action_bindings: [ado.createWorkItem, sharepoint.addKbEntry]
```

Default `include: false`, so repo-only commands (mlflow-export, session-export, coach, hooks, leak-scan) are excluded without per-command edits. This keeps `.agents/` canonical and consistent with the existing stub philosophy.

## 6. Phase 3 — Copilot Studio escalation (later)

The branchy pipelines — `daily-routine` (gather → mine → route → synthesize) and `kb-synthesize` (plan → approve → promote) — get reimplemented as **Copilot Studio / Power Automate flows** invoked by the declarative agent as actions. The human approval gate becomes an **adaptive-card confirmation** (**D4**) instead of a proposal-in-PR. Everything else stays in the Phase-1 declarative agent.

## 7. Known fidelity losses (accepted)

1. Retrieval/discovery is weaker than link-following for *broad* questions (mitigated: exact-file fetch for named files; optional Graph connector for fuzzy discovery).
2. No git versioning of *state* — ADO/Jira + SharePoint versioning instead. (`context/` itself stays git-versioned.)
3. Only board/KB/proposal commands port; repo-hygiene/telemetry machinery does not.
4. Instructions are size-capped, forcing an inline-vs-fetch triage.
5. Approval gates render as adaptive cards, not markdown proposals.

## 8. Open decisions

- **D1 — Instruction size cap.** Confirm the current M365 declarative-agent instruction limit and set the inline-triage budget (what must be inline vs. fetched on demand).
- **D2 — Action identity.** Delegated OAuth (attributes tickets to the signed-in user) vs. a service principal.
- **D3 — ADO or Jira first.** Build the action layer against one; abstract later.
- **D4 — Approval-gate UX.** Adaptive-card confirmation shape for the Phase-3 gates.
- **D5 — Fetch endpoint.** GitHub API directly vs. a thin auth proxy for a private repo; and that endpoint's auth/credential model.
- **D6 — Distribution.** Teams admin assignment vs. Copilot Studio publish; users don't self-install.
- **D7 — Graph connector: in or out** for v1 (the fetch action is sufficient without it).

## 9. Validation

- `gather --check` extended with an **m365 drift guard** (same as today's stub guard).
- A **grounding smoke test**: canonical question → expected-answer set that measures fetch/retrieval fidelity.
- **Action contract tests** against an ADO/Jira sandbox.

## 10. New / changed artifacts

- `tools/gather.py` — add the `--surface m365` render target.
- `context/tooling/harnesses/m365-copilot.md` — harness doc (join the supported-harness table).
- Optional per-command `m365:` frontmatter (§5).
- `context/tooling/m365/` — M365 config: fetch-action + OpenAPI templates, instruction-triage policy, conversation-starter/manifest generation rules.
- A knowledge/connector-sync CI workflow (only if D7 = in).
- This spec (promote to `meta/proposals/` before build — §1 status).

## 11. Source-of-truth invariant

`.agents/` + `context/` in git are the **only** authoritative source. Every M365 artifact — instructions, conversation starters, file-index manifest, and any Graph-connector index — is a **generated, one-way derivation** regenerated by `gather.py` and CI on merge. Nothing on the M365 side is ever hand-edited, and nothing on it is authoritative. This is the same "generated stubs, never drift" contract awow already enforces for `.claude/` and `.github/`, extended to a new surface.
