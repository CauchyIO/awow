# Agent instructions — Cauchy / awow (dogfood workspace)

This is the dogfood workspace's `CLAUDE.md`, hand-written as the worked example of what `tools/bootstrap-claude-md.py` should produce. The tool itself is a v0.1 skeleton — see issue tracking its implementation on the Dogfood project (#3) on CauchyIO.

Read this at session start when operating against `dogfood/`.

---

## Mission

Cauchy helps engineering teams make their plan as trustworthy as their code, by maintaining the agentic way of working as a living starter pack that adopters can actually read, run, and customise.

(`dogfood/context/team/mission.md`)

## Members

Solo team. Casper (`@hetspookjee` on GitHub, `casper@cauchy.io`) maintains all of awow. See `dogfood/context/team/members.md` for the Growth process when contributors join.

## Where to read context

- **Team context (this workspace):** `dogfood/context/team/` — mission, members, conventions, style.
- **Tooling reference:** `dogfood/context/tooling/board.md` (GitHub Projects / `Dogfood` project #3 on CauchyIO; `gh` CLI is the read/write surface — no MCP).
- **Knowledge base (when populated):** `dogfood/context/knowledge-base/` — durable rationale, ADRs, runbooks.
- **Awow template surface (parent repo):** `.agents/`, `tools/`, `context/tooling/boards/` — the awow product itself; modify with the agent-directive-voice rules when authoring or editing prompts.
- **Setup state:** `dogfood/setup-progress.md` — what the wizard has completed in this workspace.

## Before starting a new initiative

Before starting work on something with a discernible outcome — a new bug, a new feature, a refactor, anything that would warrant a commit — go to the board first.

1. **Look first.** Use the `gh` CLI to search `CauchyIO/awow` issues and the `Dogfood` project (project #3 on `CauchyIO`) for an existing ticket that already covers the scope. `dogfood/context/tooling/board.md` is the source of truth for state, labels, and hierarchy. If you find a matching ticket, use it; do not create a duplicate.
2. **No match? Propose one.** Draft the issue under `dogfood/proposals/` first (proposal-first principle), get Casper's approval, then create it on the board with the required labels (`dogfood`, `type:*`, `area:*`).
3. **Update through the lifecycle.** Move state forward when you start ("In progress"), comment when blocked or you have a finding worth recording, close when the change has landed.

Gated to **new initiatives**, not every edit. Reading files, running a grep, answering a clarifying question, fixing a typo Casper named — these do not need a ticket. Rule of thumb: would a future-Casper reasonably expect to find this on the board next week? If yes, ticket. If no, just do it.

If Casper has already named a ticket (e.g. "work on #42"), skip the lookup. Comment on the ticket as you progress.

## Where to write

- **Drafts:** always to `dogfood/proposals/<artefact>.md` first. Never write directly to the board, team context, or knowledge base without human approval.
- **Story body (board issues on `CauchyIO/awow`):** one-sentence intent + acceptance criteria + link to knowledge base. No "context" / "considerations" / meeting recap. See `dogfood/context/team/conventions/REQUIRED/output-discipline.md`.
- **Story comment:** status, blocker, intermediate finding. One paragraph max. Transient.
- **Knowledge base:** durable rationale, runbook, architectural decision, glossary entry.

## Board output rules (REQUIRED — read every session)

1. **Minimum useful body.** The smallest set of sentences that lets a competent teammate pick up the work. Third paragraph → knowledge base.
2. **Placement decision tree.** Intent → story body; status → comment; durable → knowledge base. A story is not allowed to absorb content that belongs in the knowledge base.
3. **Update vs. edit.** Body edits only for scope or acceptance-criteria changes. Status/progress/blockers go in comments. Never rewrite the body to "reflect the latest thinking" — narrow scope instead.

(Full text in `dogfood/context/team/conventions/REQUIRED/output-discipline.md`.)

## Required conventions

All four live under `dogfood/context/team/conventions/REQUIRED/`:

- `issue-titles.md` — verb-first; awow-specific patterns; scope-discipline rule (split if issue crosses `.agents/commands/`, `.agents/skills/`, `tools/`, `context/tooling/boards/`).
- `labels.md` — `type:`, `area:`, `status:` prefixes; **`dogfood` label** mandatory on every walkthrough-generated issue; bulk-closed by `/awow-reset`.
- `branches.md` — `{user}/issue-{number}-{slug}` for board-linked work; `prompt/{slug}` for maintainer prompt iteration without a board issue; `feature/{slug}` for long-lived.
- `output-discipline.md` — the non-negotiable. Read every session.

## Do not propose

Once awow has been pushed against in a way that produces specific scope-shedding, add items here. Until then, do not propose:

- Restructuring this repo's directory tree.
- Adding new top-level folders without explicit instruction.
- Switching board tools, harnesses, or trace stacks.
- Implementing parked features from `input/PROPOSAL.md` §8 (substrate, personas, federation, strategic visibility).

## Proposal-first principle

Iterate on the cheap-to-change artefact. A markdown file under `proposals/` is free; the board, the knowledge base, and `CLAUDE.md` itself are expensive to change well. Always draft first; land only after a human approves.

## When you author or edit prompts

When you edit any file under `.agents/commands/` or any declarative skill under `.agents/skills/`, follow the voice rules in `.agents/skills/agent-directive-voice.md`. Prompts are rules the agent follows mid-session, not documentation for human readers — write them in second-person imperative.

## Tracing

Tracing is on by default: `MLFLOW_CLAUDE_TRACING_ENABLED=true` in `.claude/settings.local.json` (gitignored — Casper's Databricks credentials). The Stop hook writes session metadata to the Databricks MLflow experiment `/Workspace/Shared/awow`. **Do not disable tracing mid-session or strip the Stop hook** — the traces are what `awow-usage-coach`, `daily-digest`, `weekly-digest`, and `prompt-skill-analysis` all read. If the hook fails, surface the error to Casper; do not paper over it.

## Commit messages

Two sentences maximum (user's global guideline). The "why" lives in the issue/PR; the commit captures what changed.

---

This file is the dogfood worked example of what `tools/bootstrap-claude-md.py` should produce. The tool's implementation is captured in `dogfood/backlog.md` (current preference: drop the script and have the wizard aggregate in-prompt). The wizard itself now supports `/setup-awow --root dogfood` to operate against this workspace without leaking into the template.
