---
name: handover
description: "Use when a session's work must survive it — the user asks for a handover, a resume prompt or a brief for another agent, says they are signing off, switching sessions, running out of context, or wants to pick this up tomorrow."
---

# /handover — carry a session across a boundary

You write the artifact that lets someone resume this work without you.

**A handover is not a summary of what happened. It is the shortest thing that unblocks a named reader.** Different readers are blocked on different things, so you do not know what to write until you know who reads it.

---

## Step 1 — Ask who it is for. This is your first action.

**Ask before you read the repo, before you draft, and before you raise any other question.** The session will be full of louder questions — an unresolved ruling, a broken build, a decision the user owes you. Those wait. You cannot write a single correct line until you know the reader, so the reader question goes first, alone.

Ask with `AskUserQuestion`, one question, headed `Reader`. Offer these four; the harness adds its own free-text option for anything else:

| Option | Label | Description to show |
|---|---|---|
| A | Me, reading it later | You reorient after a break and decide what happens next. Optimised for answering, not executing. |
| B | A fresh session on this same work | An agent with zero context continues this thread from where it stopped. |
| C | Another agent, to challenge or review | A second opinion attacks this work. Carries the claim and the evidence, not the conclusion. |
| D | An agent that will build from it | An implementer executes a defined change. Carries acceptance criteria and commands. |

Take the argument as the answer when the user already supplied one (`/handover for Fable to review` → C). Never guess from context alone: a wrong guess costs the reader the whole document.

Ask a second question **only** when the answer is B, C or D and you cannot tell from the session whether the reader shares this filesystem. That single fact decides the form.

When you cannot ask interactively, still put the reader first: name the reader you assumed in your opening line and in the header, mark it `assumed — confirm`, and carry on. Silently picking one is the failure; assuming out loud is not.

| The thought | The reality |
|---|---|
| "It's obviously for a fresh session" | Four readers need four different documents. One question costs a line. |
| "There's a bigger question to ask first" | Every other question is about the work. This one is about who the work is for. It goes first. |
| "The session makes the audience clear" | It made it clear to you, and you are not the one who has to read the result. |

### Derive the form from the answer, then state it

| Reader | Form | Why |
|---|---|---|
| A — you, later | File. Plus a 3–5 line paste block naming the file and the first decision. | You read it, then hand it onward. Both uses, one artifact. |
| B — fresh session, same work | File. Plus a paste block: read-order, mode, first move. | The file carries the load; the paste block only points. |
| C — challenge or review | Self-contained prompt in chat **and** a file. | The reader may be on another machine, another model, another repo. |
| D — implementer | File on the branch it applies to. Paste block names the file and the branch. | Execution needs the repo anyway. |

Say which form you chose in one line before you write. Do not write a paste block that restates the document — that duplication is the most common way these documents become unreadable.

---

## Step 2 — Fill every slot. A missing slot is the defect.

Write these in this order. Each is required; write `None` where a slot is genuinely empty rather than dropping it.

1. **Header.** Date · which session wrote it · **who it is for, named** · **the mode the reader enters** · the document that outranks this one.
   - The mode line is a rule, not a hint: `Mode: reach a written ruling. Do not write code.` or `Mode: execute the plan as written. Do not redesign.` or `Mode: attack this. Disagree freely.`
2. **State, verified.** What is true right now, with how you checked it. Head the section so the qualifier is unmissable — `## State (verified, live)`.
3. **Read first, in order.** A numbered list separate from the action list, each entry saying what to notice in it and when to stop reading.
4. **Decisions needed from the reader.** State each one; never point at where it lives. Per decision: the question in plain words · your recommendation · what it blocks · what a complete answer looks like. Leave a blank `RULING:` line under each so it can be answered in place.
5. **Traps, ordered by how much time each costs.** Numbered, each opening with a bolded imperative. Refuted designs, documents that look authoritative but are stale, tool quirks, rulings that look like drift and are deliberate.
6. **Next actions, split by owner, as checkboxes.** `## On <the human> — in this order` · `## On the agent — in this order, each on their go` · `## Parallel / not blocking`.
7. **Out of scope.** What another session or thread owns. Name it so the reader does not grab it.
8. **Provenance on every ruling.** Mark each as decided by the human directly, or recommended by an agent and not yet confirmed. Unmarked recommendations get read as settled and stop being reopened.
9. **Expiry.** One line naming the condition under which this document stops being true, so a later reader can tell it has gone stale.

**Budget: 60–140 lines.** Under that, link to the proposal, plan or board item that carries the design. Over 180 lines, the open-items section stops being a queue and becomes an inventory, and the reader cannot find where to start.

**Short handovers work when they link; long handovers fail when they inline.** When the design already exists in an approved document, carry only live state, scope, ground rules and out-of-scope — thirty lines is complete.

---

## Step 3 — Verify before you assert, and say how

Every state claim carries how it was checked, in the sentence or in an evidence index at the end.

- Run the check rather than recalling it. Verify against the actual source — the upstream repo, the live resource, the merged branch — not against a local cache or your memory of earlier in the session.
- Pin commits, never branches. `at 9c1cc6c` survives; `on casper/thing` does not.
- When a claim is load-bearing for something irreversible, state what you actually checked and what you did not. A partial check reported as complete is worse than no check.
- When you did not verify something, mark it `unverified` and move it into the decisions or traps slot.

---

## Step 4 — Sweep for what only exists in this context

Before writing, list what would be lost if this session ended right now, and check each against the draft:

- Findings from subagents or parallel workflows that were never written to a file.
- Things the user said in passing that changed the work.
- Approaches you tried and rejected, and why — otherwise the next reader retries them.
- Constraints from the user's own rules that the next session's context will not carry.
- Open threads you noticed and did not pursue.

Ask yourself the question the user will otherwise ask: *what is still open that we have not captured anywhere?* Answer it in the document.

**Do not let your own recommendation ride in as the plan.** When the next-move slot carries the approach this session took, say so and name the alternative you set aside, so the reader can reopen it cheaply.

---

## Step 5 — Land it durably, then report

A handover that lives in chat has not been written. Neither has one sitting uncommitted, or on a worktree branch invisible from the main checkout.

1. Write to the repo's handover path — follow the existing convention, else `docs/handovers/HANDOVER-YYYY-MM-DD-slug.md`.
2. Commit it.
3. Push it, per the repo's push rules. On a public repo, ask first.
4. Report the path, the commit SHA, and the branch. When it is not on the branch the reader will check out, say which branch it is on.

**No exceptions:**
- Not "I'll show it here and you can save it."
- Not "committed locally, tell me if you want it pushed" when the reader is another machine or another person.
- Not left beside unrelated work-in-progress that blocks the commit — commit the handover on its own.

---

## Anti-patterns

| What you are about to do | What it costs | Instead |
|---|---|---|
| Point at a decision queue or proposal for the open questions | The reader cannot tell what is being asked and has to have it re-derived | State each question in the document, in plain words |
| List the top five blockers | The reader believes the work is nearly done when forty decisions remain | State the count and link the full inventory |
| Say what to produce, not how to behave | The reader writes the whole plan when you needed one decision at a time | Put the mode in the header as a rule |
| Restate the document inside a paste block | The reader stops trusting either copy | Paste block points; document carries |
| Name repos as the remote names them | The reader cannot map it to their own checkout | Use the paths the reader actually has |
| Carry framing from a reference implementation as if it were ownership | The reader inherits a relationship that does not exist | Say `reference, not relationship` |
| Deliver a table the reader must retype | Work that has to be executed by hand does not survive the format | Shape anything hand-executed for copy-paste |
| Write one brief when two agents will work in parallel | Neither knows which half is theirs | Split into one self-contained prompt per agent |

---

## Red flags — stop and fix before you report done

- You raised a question about the work before you asked who reads this.
- The header's `To:` is a guess you never surfaced.
- The document exists only in this conversation.
- You wrote "verified" for something you remember rather than checked.
- The decisions slot says where to look instead of what to answer.
- You cannot name the reader.
- There is no mode line.
- Subagent or workflow findings from this session are not in it.
- It is over 180 lines and you have not tried linking instead of inlining.
- Nothing states when it goes stale.

---

## When not to use this

- The work is already fully captured in a board item, plan or PR the reader will open anyway — link it and say so.
- The session produced nothing that would be lost. Say that instead of writing a document nobody needs.
- The user is staying in this session. Handovers cross boundaries; inside one, just answer.
