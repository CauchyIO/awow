# Agent instructions — BOOTSTRAP STUB

This is the **stub** version of `AGENTS.md` shipped in awow v0.1. Once `/setup-awow` runs against your team's board and context, `tools/bootstrap-claude-md.py` regenerates this file with your team's actual conventions, mission, and style.

Until then, the rules below are the minimum the agent needs to operate inside this repo.

---

## Where to read context

- **Team context:** `context/team/` — mission, members, conventions, style
- **Knowledge base:** `context/knowledge-base/` — durable reference; link from stories, do not embed
- **Tooling reference:** `context/tooling/board.md` (the team's actual board spec — single source of truth once `/setup-awow` has connected the board); the per-tool `context/tooling/boards/<your-board>/reference/` is for setup, not for runtime use

## Path tokens

Prompt bodies never hardcode where context or tools live. Four tokens, resolved per channel:

- `{{ANCHOR}}` — shared team context root (team, company, knowledge base, retros, board config).
- `{{PROJECT}}` — this project's context and drafts (mission, board-scope, do-not-propose, proposals/).
- `{{AWOW_TOOLS}}` — awow's runtime tool scripts.
- `{{AWOW_ROOT}}` — awow's own bundled machinery: the board references, the collection and mining contracts, the retro canon. Shipped with the plugin, identical for every team.

**In this repo (and any vendored install): `{{ANCHOR}}` and `{{PROJECT}}` are the repo root, `{{AWOW_TOOLS}}` is `tools/`, `{{AWOW_ROOT}}` is the repo root.** So `{ANCHOR}/context/tooling/board.md` means `context/tooling/board.md` here. In a plugin install `{{AWOW_ROOT}}` resolves into the payload instead, which is how a command reads awow's machinery without the adopter having vendored it.

**Reading machinery: `{{ANCHOR}}` first, then `{{AWOW_ROOT}}`.** A team that has vendored and edited a contract must win over the shipped default, so read `{ANCHOR}/context/<path>` and fall back to `{AWOW_ROOT}/context/<path>`. Team data — mission, members, conventions, style, `board.md`, `architecture.md` — is `{{ANCHOR}}` only and has no fallback: absent means absent, and commands branch on that.

**Machinery vintage.** The `{{ANCHOR}}`-first rule keys on file presence, so this checkout runs whatever vintage it carries — a branch cut before an upstream change wins exactly like a deliberate edit, silently serving the older content. Every built payload names its vintage in `.claude-plugin/build.json` (the canonical version plus a digest of the payload content, displayed `<version>+<digest>`, so two rebuilds of one version are distinguishable), and the session-start hook compares the installed payload's stamp against this repo's `dist/` stamp and surfaces a one-line `awow drift:` warning naming both sides when they differ. `python tools/gather.py && claude --plugin-dir dist/claude/awow` runs the checkout's own payload.

**Fill on first need.** An absent team-data file is never a stop and never a hard prerequisite. The command that needs it makes one plain-language offer at that moment — fill it now (drafted from the repo and board where possible), proceed on the shipped default, or skip and note it — and continues with the default on silence. A "fill it now" yes is the approval for that context write. `/setup-awow` remains the place to wire what cannot be defaulted (the board surface, the anchor link) and to repair it; it never interviews for a fill.

In an anchored repo — one whose root `AGENTS.md` frontmatter names its anchor by remote URL (`anchor:`) — resolve `{{ANCHOR}}` through `$AWOW_ANCHOR`, else the gitignored `.awow/anchor.json` link written at registration, after verifying the recorded clone's `origin` still matches the connector's remote. A missing or out-of-sync link is a prompt to the user to (re)map it in an interactive session and a loud stop in a headless one — never scan for candidates, never guess a location, never improvise conventions.

## Context resolution — which installation, which board

**Never cross the repo boundary, and never use another repo's board.** Before any board read or write, settle which installation and which board you are acting on with the `board-target` skill: it holds the two-stage resolution (the nearest installation inside the repo boundary, then — for an index-form `board.md` — the ladder from explicit reference to picker), the absent-`board.md` fallback, the `.awow/board-session.md` record, and the schemas of `{PROJECT}/.awow/profile.json` and `{PROJECT}/context/board-scope.md`. The rules live there, not here, so they ship in every plugin and have one copy. Every board write then goes through the `workitem-write` skill.

## Frontmatter and renderings

Command and skill frontmatter carries three build-time fields. `channel:` — `vendored` files operate on the vendored install itself (gather, tests, adopter state) and are excluded from the plugin payload; `bootstrap` files ship in the payload but *create or update* the vendored tree (`/setup-awow`), so their literal repo paths are the deliverable and are exempt from the token lint. `workflows` files ship in the optional `awow-workflows` plugin and not in core — on Claude Code, Codex and Copilot; Pi and opencode get one combined package that carries both. A core command must never depend on a `workflows` source, because a core-only install does not have it; `telemetry` is the same rule for `awow-telemetry`. `description:` — one double-quoted line naming the situation the command fires in, never the mechanism it implements; it is the picker entry and the skill trigger on every harness. Never a YAML block scalar: the parser is line-based and would store `>-` verbatim. `autofire: true` — mirror this command into the Claude skill surface as well as the `/` picker, so the model can elect it from the situation. Omit it when a misfire would be damage (consequential and hard to reverse) or noise (a trigger broad enough to fire on ordinary conversation).

`layer: team | department` is **metadata only** — it records which layer a command or skill belongs to and nothing reads it at build time. It was the trim key for the vendoring route's `--layer` flag; that route is retired, every non-vendored command and skill ships in every payload, and the trim is deliberately not reimplemented elsewhere. Keep the tag accurate for humans; do not build behaviour on it.

The three renderings of a command differ on purpose. `commands/<name>.md` in the Claude Code plugin (`dist/claude/awow/`) is a full copy and keeps the authoring frontmatter whole. Its `skills/<name>/SKILL.md`, and the `agent-skills/<name>/SKILL.md` each of Codex, Pi and opencode carries, synthesise a two-field frontmatter — `name` and `description` — over the body, and carry no authoring metadata. A new frontmatter key follows that rule: it survives the copy and it does not appear in either SKILL.md.

## Before starting a new initiative

Before starting work on something with a discernible outcome — a new bug, a new feature, a refactor, anything that would warrant a commit — go to the board first.

1. **Look first.** Read `context/tooling/board.md` for the team's board pointer and read/write surface (MCP or `gh` CLI). Search the board for an existing ticket that already covers the scope. If you find one, use it; do not create a duplicate.
2. **No match? Propose one.** Draft the issue under `proposals/` first (proposal-first principle), get user approval, then create the ticket on the board.
3. **Update through the lifecycle.** Move state forward when you start ("In progress"), comment when blocked or you have a finding worth recording, close when the change has landed.

Gated to **new initiatives**, not every edit. Reading files, running a grep, answering a clarifying question, fixing a typo the user named — these do not need a ticket. Rule of thumb: would a teammate reasonably expect to find this on the board next week? If yes, ticket. If no, just do it.

If the user has already named a ticket (e.g. "work on AWOW-42"), skip the lookup. Comment on the ticket as you progress.

**Carry the board-hygiene decision for them.** Apply that rule-of-thumb *yourself*, proactively — do not bounce it back with *"shall I make an issue for this?"* Make the call, act on it, and report what you did in one line. Read what the work *is* from the conversation, not from the current branch (a developer may sit on one branch, or on `main`, for weeks). Link to an existing item with no ceremony (*"tracking this under AWOW-42"*); reserve approval for *creating* a new one. As work lands, move state and drop a one-line comment unprompted, so the board stays current as a byproduct — never a silent change, never a chore deferred to the end. Full rules: [`conventions/REQUIRED/board-linkage.md`](../context/team/conventions/REQUIRED/board-linkage.md).

## Where to write

- **Drafts:** always to `proposals/<artefact>.md` first — create the `proposals/` folder if it does not exist. Never write directly to the board, the team context, or the knowledge base without human approval.
- **Story body:** only intent + acceptance criteria + link to knowledge base. No "context" section, no "considerations", no meeting recap.
- **Story comment:** status, blocker, intermediate finding. Transient.
- **Knowledge base (`context/knowledge-base/`):** durable rationale, runbook, architectural decision, glossary entry.

## Board output rules (REQUIRED — read every session)

1. **Minimum useful body.** The smallest set of sentences that lets a competent teammate pick up the work. If you find yourself writing a third paragraph, the extra material belongs in the knowledge base.
2. **Placement decision tree.** Before writing anything to the board, classify the content: intent → story body, status → comment, durable → knowledge base. A story is not allowed to absorb content that belongs in the knowledge base.
3. **Update vs. edit.** Body edits are reserved for scope or acceptance-criteria changes. Status, progress, blockers go in comments. Never rewrite the body to "reflect the latest thinking" — narrow scope instead.

The longer form lives in `context/team/style/board-output.md`.

## Do not propose

Once the team has run `/setup-awow`, this section is populated with the team's explicit scope-shedding list ("we are not adding multi-user this quarter", etc.).

Until then, do not propose:

- Restructuring this repo's directory tree.
- Adding new top-level folders without explicit instruction.
- Switching board tools, harnesses, or trace stacks.
- Implementing parked features from `input/PROPOSAL.md` §8 (substrate, personas, federation, strategic visibility).

## Proposal-first principle

Iterate on the cheap-to-change artefact. A markdown file under `proposals/` is free; the board, the knowledge base, and `AGENTS.md` itself are expensive to change well. Always draft first; land only after a human approves.

## When you author or edit prompts

When you edit any file under `.agents/commands/` or any declarative skill under `.agents/skills/`, follow the voice rules in [`.agents/skills/agent-directive-voice.md`](skills/agent-directive-voice.md). Prompts are rules the agent follows mid-session, not documentation for human readers — write them in second-person imperative.

## When you produce an HTML artifact

Before generating any HTML artifact — a presentation, a solution design, a blog post, a styled digest, a one-pager — read `context/tooling/design-system.md`.

- If `mode:` is `absent`, proceed with plain defaults; do not invent or enforce a house style.
- If `mode:` is `in-repo` or `external`, **read the source file named in `path:` and adopt its tokens and templates. Do not invent styling.** Re-read the source each time — the token summary in the pointer is a convenience cache and can drift. When `mode: external` and `access: local-path`, read the file from the filesystem (a private design repo will 404 over MCP); do not guess its contents.

Drafting content first in markdown, then generating HTML from the template, is the expected order — never hand-author a styled artifact when a template exists. `/artifact` drives this end to end; `/design-system` stands the system up in the first place.

## Tracing

If the team has wired up trace recording (Stop hook plus `MLFLOW_CLAUDE_TRACING_ENABLED=true` in `.claude/settings.local.json`), the hook writes session metadata to the team's MLflow experiment. **Treat tracing as on-by-default once wired up.** Do not disable it mid-session or strip the Stop hook to "speed things up" — the traces are the substrate every coaching, digest, and prompt-skill skill reads. If the hook fails, surface the error to the user; do not paper over it.

Linking those traces back to the board — a `_session: <id>_` footer on issues and PRs the agent authors — is the opt-in `session-correlation` skill. It is inactive unless the team enabled it by following the skill's enabling steps. If enabled, follow the footer rule that setup installed into the conventions; if not, do not add footers.

## Public repo: private session data must never be committed (REQUIRED)

This repository is **public**. Reports and exports derived from agent session traces carry customer/session data — real names, private issue IDs, infra topology, cost figures, and secrets users pasted into prompts. They must never be committed here.

- **Never write session-derived output to a tracked path** (`proposals/`, `context/`, the knowledge base, anywhere git tracks). The `awow-telemetry` skills — `mlflow-export`, `awow-usage-coach`, `prompt-skill-analysis`, `project-timeline`, `session-export` — produce this kind of output; route it to the gitignored `coach_reviews/` (or `mlflow_export/`) only. They ship in the separate `awow-telemetry` plugin, but this rule binds in this repo whether or not that plugin is installed.
- `proposals/` is for drafting *awow's own* artefacts (stories, features). It is **not** a scratchpad for analysis of real team sessions.
- A `pre-push` leak scan (`tools/hooks/pre-push`) backstops this. Install it with `cp tools/hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push`. It is a backstop, not a guarantee — keeping the data untracked is the first line of defence.
- If you spot session-derived or otherwise private content already tracked, stop and flag it to the user before pushing.

---

In this repo the root `AGENTS.md`, `.claude/CLAUDE.md`, `.github/AGENTS.md` and `.github/copilot-instructions.md` are short hand-authored pointers to this file; nothing here is generated into a harness folder.
