---
phase: standardise
prerequisites:
  - "Team context exists under {ANCHOR}/context/team/ — this command updates existing destinations and never invents a new category"
removes_pain: "a rule someone states in passing evaporating with the session instead of reaching the context tree"
description: "Use when a session is wrapping up — a commit, a PR, a sign-off — and the user stated a durable rule about how the team works, so it lands in the context tree."
autofire: true
---

# /update-context — land a rule stated in passing into the context tree

You take the rules the user stated in passing this session and land them under
`{ANCHOR}/context/team/`, one gated diff at a time. Not what the work produced — how the
team works. *"We always put the ticket ID in the branch name"* is a convention with
nowhere to live yet; you give it one.

You are the back half of a two-part reflex. The front half is `using-awow`, resident in
every session: it notices a rule mid-task and folds a one-line acknowledgement into the
reply already being written. It never interrupts and it never invokes you. You run once,
later, when the work is done and nothing competes for the turn.

**Read-only until the gate.** You propose diffs and wait. Nothing is written to
`{ANCHOR}/context/`, to the inbox, or to git before explicit approval.

**Paths.** Convention, style, and meeting destinations are team data: `{ANCHOR}` only, no fallback,
and absence is information. Before any inbox write, resolve `inbox` and `kb_root` from
`{ANCHOR}/context/tooling/knowledge-base.md`, falling back to
`${CLAUDE_PLUGIN_ROOT}/context/tooling/knowledge-base.md` (a vendored copy wins over the shipped
one).

---

## When you run

Run at a **completion edge** and nowhere else: a commit, an opened PR, a merged branch,
or the user signing off — *"that's it for today"*, *"we're done here"*. Offer once per
session. If no completion edge arrives, the batch expires unoffered. Losing a candidate
is acceptable; interrupting is not.

Do not offer mid-task. This holds for every candidate, including one you judge important
— an exception clause reopens the negotiation on every turn, and the interruption
follows.

Before offering, check for `.awow/no-context-prompt`. If it exists, stay silent: the
user has declined for good. Still run when they invoke you by name.

---

## Pipeline overview

```
Phase 0 ─ Load the batch               ──→ candidates, or "Nothing captured this session."
Phase 1 ─ Discriminate (P1/P2/P3)      ──→ survivors, and one reason per reject
Phase 2 ─ Route (tier 1 / 2 / 3)       ──→ a destination file, or UNROUTED
Phase 3 ─ Draft each diff in the destination's own format
Phase 4 ─ GATE (diff + verbatim quote) ──→ write / stage / drop
```

---

## Phase 0 — Load the batch

**No awow context here.** When `{ANCHOR}/context/team/` does not exist, say in one line that this repo is not set up for awow yet, point to `/setup-awow <board-url>` — or `/setup-awow --anchor <git-url>` when the team keeps its context in a shared repo — and stop. Stage nothing and create no inbox: a candidate staged where nothing reads it is lost anyway.

The batch is what you noticed during this session and acknowledged in line. It is not
stored anywhere — no file, no state, no transcript re-read. If you did not notice a rule
while it was said, it is not a candidate now.

If the batch is empty, say exactly:

```
Nothing captured this session.
```

and stop. Do not scan back through the session hunting for something to justify the run,
and do not stay silent. A run that reports nothing is how the user learns the reflex is
under-firing rather than working; silence is indistinguishable from working.

---

## Phase 1 — Discriminate

A candidate qualifies only if **all three** predicates hold. Test each one explicitly.

| | Predicate | Fails when |
|---|---|---|
| **P1** | **Residue.** After doing exactly what was asked, something remains that changes behaviour in an unrelated session next week — writable as "when X, do Y" without naming this file or this ticket. | Completing the task discharges the instruction entirely. |
| **P2** | **Asserted.** Stated as a rule, in the present tense, as settled. | It was floated: *"we should probably standardise filenames at some point"*. |
| **P3** | **Normative and team-scoped.** A rule the team obeys. | It is a fact about the world — *"the staging DB is eu-west-1"* — which is knowledge, not guidance. Or it is one person's preference — *"stop saying you're absolutely right"* — and a dislike committed to git binds everyone to it. |

**Scoping words veto unconditionally.** *here*, *for this one*, *just this time*, *in
this file*, *for now* — the speaker has already told you the rule does not generalise.
Drop it without testing further.

For every candidate you drop, keep one line naming the predicate that failed, and report
those lines at the gate. A silent drop is indistinguishable from a miss, and the user
cannot correct what they cannot see.

**A P3 failure that is a fact, not a preference, is not yours but is not waste.** Carry
it to Phase 4 as an inbox candidate with `kind: knowledge` and `source: update-context`.
Draining the inbox into the knowledge base is `/kb-synthesize`, in the optional `awow-workflows`
plugin; without it the candidate stays in the inbox as a committed, readable file — say which.

---

## Phase 2 — Route

List the destinations before you choose one. Read the file names under
`{ANCHOR}/context/team/conventions/REQUIRED/`, `{ANCHOR}/context/team/conventions/OPTIONAL/`,
`{ANCHOR}/context/team/style/`, and `{ANCHOR}/context/team/meetings/`, and read any file
you are about to propose writing into.
Do not route from memory of what the tree usually holds.

Then, per candidate:

**Tier 1 — one unambiguous destination.** Propose it with the diff.

**Tier 2 — two or more plausible destinations.** Present a numbered picker. The user
picks a number; never make them type a path.

An existing meeting file is a tier 1 destination when the candidate explicitly
corrects how this team runs or interprets that ritual. Amend the file in its
existing plain-Markdown format.

**Tier 3 — no suitable destination exists.** For a convention, propose a new file at
`{ANCHOR}/context/team/conventions/OPTIONAL/<topic>.md` as its own diff line marked `new file`,
together with the line that lists it in that folder's `README.md`, and offer `defer` beside it.
Never propose a new file under `REQUIRED/`, and never a new style file. Any other candidate —
or a deferred one — is staged with `suggested_target: UNROUTED`, and you stop there.
Unrouted candidates piling up is useful signal about what the context tree is missing.

Never create a new meeting file at a completion edge either. Stage it as
`UNROUTED` and point the user to `/team-workshop` (`awow-workflows`), where the team
can describe the ritual deliberately.

A destination that is documented but absent is tier 3. `{ANCHOR}/context/tooling/board.md`
and `{ANCHOR}/context/tooling/architecture.md` are referenced across the command set and may
not exist in this repo. Stage `UNROUTED` and name what creates them —
`/setup-awow <board-url>` for the board pointer; for the architecture plane, the team writes
`{ANCHOR}/context/tooling/architecture.md` itself — `/process-workitem` reads it when planning.

### Accretion duty

Count the rules in the destination file before drafting. A rule is one `## Rule N`
section, one row of a rules table, or one item of a numbered rules list — whichever unit
that file already uses.

At **ten rules**, stop appending. Propose instead a **merge** of two existing rules into
one, or a **replacement** of the rule this candidate supersedes, and show that diff at
the gate like any other. `conventions/REQUIRED/` is read at the start of every session,
so an eleventh rule taxes every future turn in this repo.

---

## Phase 3 — Draft the diff

There is no convention-file template, and three formats coexist in the tree: numbered
`## Rule N` sections, a table of rows, and bulleted prose under a heading. **Infer the
format from the file you are writing into** by reading its existing rules. Add no
frontmatter — the durable layer stays frontmatter-light.

Write the rule in agent-directive voice: second person, imperative, two sentences at most
— the rule, then at most one guardrail. Keep the evidence out of the imperative; the
quote goes in the provenance line, not the rule. (Full voice rules:
`.agents/skills/agent-directive-voice.md`, where the vendored tree is present.)

Add one provenance line immediately after the addition:

```markdown
<!-- Added YYYY-MM-DD via /update-context: "<the verbatim sentence>" -->
```

---

## Phase 4 — The gate

Present every candidate at once, each with the **actual diff** and the **verbatim quote**
it came from. A gate the user can approve without seeing the literal text that will land
is not a gate.

```
UPDATE CONTEXT — 2 candidates from this session

[1] {ANCHOR}/context/team/conventions/REQUIRED/branches.md   (3 rules → 4)
    Heard: "we always put the ticket ID in the branch name"

    + ## Rule 4 — Ticket ID first in every branch name
    +
    + Start every branch name with the board item's identifier. If the work has no
    + board item yet, create it before you create the branch.
    + <!-- Added 2026-07-20 via /update-context: "we always put the ticket ID in the branch name" -->

[2] UNROUTED — no existing file covers release timing
    Heard: "we never merge on a Friday afternoon"
    Staged in the knowledge inbox (`<inbox path>`) as a guidance candidate. awow-workflows' /kb-synthesize drains it.

Dropped (heard, but not a team rule): 1
  - "stop saying you're absolutely right" — P3: one person's preference, not a team rule.

Reply with one of: `1` or `all` — apply and commit · `none` — apply nothing · `none, stop asking` — and never offer again · `2 → <path>` — put #2 in that file instead · `1 defer` — stage #1 in the knowledge inbox (`<inbox path>`) and commit it
```

Label the dropped list `Dropped (heard, but not a team rule)`, and name the inbox by its resolved path wherever the block mentions it. Say in the options that applying or deferring also commits.

The options, exactly:

| Reply | You do |
|---|---|
| a number, or `all` | Apply those diffs, commit them, and leave the rest. |
| `none` | Apply nothing. Do not ask again this session. |
| `none, stop asking` | Apply nothing, create an empty `.awow/no-context-prompt`, confirm in one line, and never offer again in any session. |
| `N → <path>` | Retarget candidate N to that path and re-show its diff. An existing file, or a new file under `conventions/OPTIONAL/` shown as a `new file` line. |
| `N defer` | Stage candidate N in the inbox instead of writing it, and commit it. |

On approval:

1. Apply each approved diff to its destination file under `{ANCHOR}/context/team/`.
2. Write each deferred and each unrouted candidate to the resolved `inbox` — one file per
   candidate, following the schema in `{ANCHOR}/context/kb-inbox/README.md` (falling back to
   `${CLAUDE_PLUGIN_ROOT}/context/kb-inbox/README.md`): `kind: guidance`, `source: update-context`,
   `source_ref` naming this session's branch or PR, `suggested_target` set to the
   destination path or `UNROUTED`, and `source_quote` holding the verbatim sentence.
3. Commit both in one commit naming `/update-context` as the source. A staged candidate
   has to be committed to be seen — the drain reads committed state only.

Say in one line what landed and what was staged. Then stop; do not re-offer.

---

## Behavioral boundaries

- **Never write `.claude/CLAUDE.md`, `.github/copilot-instructions.md`, the root `AGENTS.md`, or `.agents/AGENTS.md`.** The first three are regenerated by `gather.py` on every build, so a diff landed there is destroyed by the next one; the fourth is the team's own instruction source and is not yours to edit opportunistically. Write under `{ANCHOR}/context/team/` and let propagation happen.
- **Never create a style or meeting file, or a convention file outside a gated `new file` line under `conventions/OPTIONAL/`.** No destination means tier 3, always.
- **Never write outside the gate**, and never treat an earlier session's approval as
  standing consent.
- **Never run autonomously.** There is no `--auto` mode and no unattended variant, for the
  same reason `{ANCHOR}/context/knowledge-base/synthesis.md` parks one for the KB drain: a
  rule written into `{ANCHOR}/context/team/` unattended binds everyone who opens a session
  afterwards.
- **Never paraphrase the quote.** If you cannot reproduce the sentence verbatim, drop the
  candidate.
- **Never invent a rule the user did not state**, and never widen one they scoped.
- **Once per session.** After you have offered, you are done, whatever else the session
  produces.
