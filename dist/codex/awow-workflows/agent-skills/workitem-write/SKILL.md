---
name: workitem-write
description: "Use for any board item create or update — an ad-hoc make-a-ticket request or a flow's write step. The one convention-wired path: resolve the target, look first, cite conventions, shape, gate, write, report."
---

# workitem-write — the one path for board creates and updates

Every board item create or update routes through these steps, in this plugin and from any other: a flow delegating its write step (in `awow-workflows`: `/daily-checkin`, `/project-plan`, `/refinement-prep`, `/process-transcript`) or an ad-hoc "make a ticket for X" mid-session. A delegating flow keeps its own discovery, templates, and flow-specific rules; this skill owns the generic write discipline. It is deliberately type-agnostic — work-type rules live in the `_workitem-archetypes/` handlers at execution time, never here at creation time.

## 1. Resolve the target, then look first

Settle which installation and which board you are writing to with the `board-target` skill — it owns the resolution ladder, the absent-`board.md` fallback, and the session record. Do not restate or improvise those rules here.

Then search the board (surface per `{ANCHOR}/context/tooling/board.md`) before drafting anything new, along four axes: keywords from the request, named owners' assigned items, project / area scope, and recency (items updated in the last two cycles). Note match confidence: exact / likely related / weak signal. When `board.md` declares a board-team filter for a shared board, scope reads to the filter but run the duplicate search board-wide — a duplicate across teams is still a duplicate.

Found coverage → link or comment with no ceremony. **Smallest board footprint wins:** comment > move > create. Creating a new item is the exception that must justify itself against the search you just ran, never the reflex.

**Record the pre-image.** For every item you may change, record what you just read — current state, title, and the body section a change would touch. This snapshot is the board plan's "before"; step 5 re-verifies it line by line.

## 2. Convention inventory

Before shaping a draft, read and apply:

- `{ANCHOR}/context/team/conventions/REQUIRED/issue-titles.md` — title verbs and patterns
- `{ANCHOR}/context/team/conventions/REQUIRED/labels.md` — the label taxonomy
- The board's existing projects / containers and their naming

The draft **cites** which conventions shaped it — title pattern, labels chosen, container — so the user approves against the team's rules, not your taste. Placing an item in a new container requires stating why no existing one fits.

## 3. Shape the body

- Story shape per `story-shape.md`, beside this skill; voice per `{ANCHOR}/context/team/style/board-output.md`.
- Placement per `{ANCHOR}/context/team/conventions/REQUIRED/output-discipline.md` Rule 2: intent + acceptance criteria → body; status, blockers, execution decisions → comment; durable rationale → `{ANCHOR}/context/knowledge-base/`, through the `knowledge-source-routing` skill's Capture rule whenever `{ANCHOR}/context/knowledge-sources/index.md` exists. Label every section by placement before the gate — the user approves placement, not just words.
- **No invented specifics.** A draft may not name a technology, path, endpoint, count, limit, or time window the source material or `{ANCHOR}/context/` did not state — those are design decisions; surface them as open questions. Never fill in Owner or Cycle unless the user named them.
- **Source every action.** Record where each proposed action comes from — the transcript segment, user statement, board item, or convention that motivates it. Step 4 refuses a line with no source.

## 4. Gate — reuse the authorisation you have, then the board plan

Ask only for authorisation you do not already hold. Three kinds of action never reach the gate:

- **Links and comments.** Linking an existing item and commenting need no approval.
- **Agent-owned transitions.** A state move that `{ANCHOR}/context/tooling/board.md` assigns to the agent in its state machine — typically In Progress on pick-up, In Review on PR open, Done on merge — is already authorised by the team. Make it, and report it in one line. A move `board.md` does not name as agent-owned, or names as human-confirmed, is gated.
- **A concrete change already approved in this conversation.** The user stated the exact change ("close PROJ-42 as duplicate of PROJ-40"), or approved it in a calling flow's plan. Execute it; do not ask again.

Everything else — creating an item, editing a body, any other state move — requires explicit approval in this conversation. **Show the concrete change before you ask.** Never request approval in the abstract ("shall I make a ticket for this?"): the question is always a board plan the user can read. Present every batch of gated actions as one **board plan**: a fenced `diff` block, one numbered line per action, a counts footer.

```diff
BOARD PLAN · board: <name> [<tool>]

+ 1  <Type> "<Title>"   → <initial state>
~ 2  <ID>  body: <what changes>
~ 3  <ID>  <from> → <to>
- 4  <ID>  close — <reason>

Plan: <n> add · <n> change · <n> close
```

- Symbols: `+` create, `~` any change to an existing item, `-` close or cancel. Use no other symbols.
- Change phrase by action — create: `→ <initial state>`, plus `↳ under <line|ID>` when parented; body edit: `body: <what changes>`, naming the section touched, ten words or fewer; state move: `<from> → <to>`; field or label: `<field>: <old> → <new>`; close: `close — <reason>`.
- One line per item: join multiple facets with ` · `; keep a line under ~100 characters and truncate with `…` — the remainder belongs to `details`.
- A plan spanning boards suffixes each line with `[<board>]` and breaks the footer down per board; a single-board plan omits both.
- Comments, links, and agent-owned transitions are not plan lines; they appear only in the step-5 report.
- KB writes and escalations proposed alongside board actions: list them under the diff block as `KB <n>  <path> — <one-line>` and `ESCALATE <n>  <edge> → <action>`, numbering continuing the plan, and extend the footer (`· <n> kb · <n> escalate`).

Offer the standard options and wait; execute only what was explicitly approved:

```
"go"        — execute all
"skip 2,3"  — execute all except listed
"details 3" — show one line's full draft, then re-offer these options
"review"    — walk through each
"cancel"    — no changes
```

**`details N`** prints, by action type — create: the full draft body as it would land plus the conventions that shaped it; body edit: an old/new diff of only the touched sections; move or field: current value, target value, rationale; close: the reason and what supersedes it. End every details view with `because: <source>` — the provenance line — and never execute anything from inside `details`.

**Provenance.** Every plan line must trace to a source (transcript segment, user statement, board item, convention); do not propose a line you cannot source. `details` and `review` surface each line's `because:`.

The plan is ephemeral: never write it to a file and never keep it after execution — the board is the only truth.

## 5. Write + report

Execute via the board surface, one action at a time, confirming each briefly. Re-verify each line's pre-image before touching its item — a move re-reads the current state, a body edit re-reads the touched section. On mismatch, do not apply the line: report `stale — board changed since plan` with the fresh value and move on; never force, never merge silently. Apply parented creates parent-first; a failed parent skips its children, reported as skipped. Execute exactly what was approved — if ambiguity surfaces mid-execution, stop and ask; no silent changes. If an action fails, report the error and continue.

**Resume, never restart.** When a plan was interrupted — a failed call, a lost connection, a turn that ended mid-batch — the board is the record of what landed. Re-read it, skip every line it already reflects (link the item a create already produced; never create it twice), and continue from the first unexecuted line. The approval still stands for lines whose pre-image is unchanged; re-gate only a line the board has moved under. Encode dependency edges when given: the board's native blocked-by relation, or a `Blocked by:` body line when the board has none.

Then report:

```
DONE
Executed: [one line each]
Skipped: [list or "none"]
Failed: [list or "none"]
Manual follow-up: [list or "none"]
```

## 6. Hygiene hooks

- **One layer at a time.** Decomposing into more than ~5 children → create the first layer only; deeper layers wait until the work reaches them.
- **Update vs. edit** (output-discipline Rule 3): body edits are reserved for scope and acceptance-criteria changes; status, progress, and findings go in comments. Never rewrite a body to "reflect the latest thinking."
