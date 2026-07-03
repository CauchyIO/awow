---
name: agent-directive-voice
description: "Agent-directive voice"
---

# Agent-directive voice

A skill the agent reads when authoring or editing prompts in `.agents/commands/` or `.agents/skills/`. Defines the voice rules every awow rule must follow.

The rule of thumb: **a prompt is a rule the agent reads at session start and follows during the session.** It is not documentation for a human teammate. The voice should match.

---

## Core principle

Prompts are addressed to the agent, not to the human reader. The agent is the recipient. The voice is imperative, second-person, terse.

A descriptive sentence ("A right-sized story is one an agent or engineer can produce a working PR for in a single session") is documentation. The agent-directive equivalent ("Right-size each story so a single session can ship a working PR; split anything larger") is a rule. They convey the same content; only one is actionable mid-session.

---

## Voice rules

- **Second person, addressed to the agent.** "When you have…", "Before you write…", "After you apply…", "Do not chain…". Never "the user should" or "ask Claude to".
- **Imperative, terse.** Match the existing CLAUDE.md sentences: *"Drafts: always to `proposals/<artefact>.md` first."* *"Body edits are reserved for scope or acceptance-criteria changes."*
- **Two sentences max per rule.** First sentence: the rule. Optional second sentence: the guardrail or exception.
- **No exclamation marks, no emojis, no "always remember to".**
- **No restating evidence inside the rule itself.** Stats, quotes, and rationale go beside the rule (in a separate `Why:` line, an Anti-patterns table, or a callout), not inside the imperative.

---

## Worked rewrites

**Verbose, human-aimed advice:**
> "After Claude executes a `propose`d change, ask for a one-line readback before moving on. 'Show the diff you applied and confirm the brevity rule still holds.' Don't stack a second `propose` on top of an unverified first one."

**Tight, agent-directive:**
> "After you apply a proposed change, summarise the diff in one line and stop. Do not chain a second proposal on the unverified first."

---

**Human-aimed:**
> "If the question has a likely follow-up — 'and then I'll need a conclusion,' 'and we'll have to update the diagrams' — open the session with the goal, not the first sub-task."

**Agent-directive:**
> "When a session's first prompt is a single-line action without surrounding goal, ask: 'what's the larger goal this fits into?' before acting. Skip the question only if the prompt explicitly marks itself as one-off."

---

**Human-aimed (descriptive prose):**
> "A right-sized story is one an agent or engineer can produce a working PR for in a single session. Sizing checks: 1–5 files touched, 2–3 sentences to describe without hand-waving, ≤5 acceptance criteria."

**Agent-directive:**
> "Right-size each story so a single session can ship a working PR: touch 1–5 files, describe the change in 2–3 sentences, and keep acceptance criteria at five or fewer. Split anything larger."

---

## When a rewrite cannot be made agent-actionable

If the only honest rewrite still reads as advice to a human ("the team should decide…", "discuss with the product owner"), the content does not belong in a prompt. Move it to:

- The CLAUDE.md "Don't propose" / scope-shedding block, if it is a posture.
- `context/team/style/*.md`, if it is a writing convention reviewed by humans.
- An archetype handler, if it is work-type-specific guidance.
- The skill's "When NOT to" section, if it is delineating scope.

Prompts hold rules the agent follows; everything else lives elsewhere.

---

## Where this skill applies

- Every file under `.agents/commands/` (slash command prompts).
- Every file under `.agents/skills/` whose body is meant to shape agent output (declarative skills) — including this one.
- The CLAUDE.md instructions block.

It does **not** apply to README.md files. Those are documentation for human readers about how the system is organised; descriptive voice is correct there.

---

## How this fits the workflow

When the agent edits a prompt, it should:

1. **Read this skill** before writing the new content.
2. **Identify the addressee** of each sentence. If a sentence talks *about* the agent or *to* the human, rewrite it.
3. **Check the length.** Two sentences per rule; longer means the rule is doing two jobs.
4. **Strip evidence from the imperative.** Move stats and quotes to a separate block beside the rule.

When in doubt, mirror the cadence of existing awow rules in `.agents/AGENTS.md` — that file is the calibration sample.
