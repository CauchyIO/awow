# Retrospective Anti-Pattern Library

The named pathologies `/process-retro` actively probes for. Two sections — keep them separate.

The first is grounded in 20+ years of retro literature. The second is **net-new for agentic-AI workflows**: there is no prior canon to draw from, and these patterns are the AWOW community's contribution back.

Maintained file. Add patterns as your team discovers them. Keep names hyphenated, descriptions ≤ 3 lines, and put new agentic patterns in the second section unless they map cleanly to a published general anti-pattern.

See [`canon.md`](canon.md) for the philosophical grounding and the references behind the general patterns.

---

## Section A — General retro anti-patterns (documented)

These are patterns retro practitioners have catalogued in books, blogs, and tool docs over the last two decades. Where a canonical source exists, it's linked.

### venting-ritual
Retros surface complaints about things outside the team's locus of control, with no commitment to action. Catharsis without change. Trains the team to expect performance rather than improvement.
*Source: [Retrium anti-patterns](https://www.retrium.com/ultimate-guide-to-agile-retrospectives/retrospective-anti-patterns); [Wolpers, 21 Anti-Patterns](https://dzone.com/articles/21-sprint-retrospective-anti-patterns).*

### conversational-dominance
One speaker holds the floor disproportionately, controls topic transitions, interrupts more than is interrupted. Documented in Project Aristotle as a negative predictor of team effectiveness.
*Source: [Project Aristotle](https://psychsafety.com/googles-project-aristotle/).*

### action-list-inflation
Retro produces a long list of action items, no owners, no dates. The canon explicitly warns against this — "small number" is load-bearing in Derby & Larsen's Decide phase.
*Source: Derby & Larsen, *Agile Retrospectives* (2006).*

### action-orphan
Action items from prior retros that no-one can locate. The clinical signal of a venting ritual. Drives down action-item closure rate, which is the field's standard effectiveness measure.

### hijacked-agenda
In Lean Coffee or any participant-led format: dominant voices propose all the topics, so the agenda reflects who's loud rather than what's broken.
*Source: Lean Coffee community practice notes.*

### premature-solutioning
Team jumps from Gather Data straight to Decide What to Do, skipping Generate Insights entirely. Solutions land before the problem has been understood. The most common phase-discipline failure.
*Source: Derby & Larsen, *Agile Retrospectives*.*

### blameless-violation
Someone in the retro names an individual as the cause of a problem rather than the system. Direct violation of the Prime Directive.
*Source: Kerth, *Project Retrospectives* (2001).*

### template-stagnation
Same activity used retro after retro until the signal is gone. Note the distinction: consistency is fine when the signal still arrives; stagnation is when participants have memorised the responses.

### feedback-asymmetry
Junior members give feedback up; senior members don't reciprocate. Or vice versa. Edmondson's psychological-safety markers fail.
*Source: [Edmondson on psychological safety](https://psychsafety.com/the-history-of-psychological-safety/).*

---

## Section B — Agentic-AI retro anti-patterns (AWOW originals)

These are patterns specific to teams running agentic workflows. The retrospective literature does not address them — agentic AI is recent enough that retros-on-agents are themselves a green-field practice. This section is the AWOW community's contribution.

### duplicate-creation
Agent creates a new board item that overlaps an existing one because the duplicate-check was insufficient or skipped. Often a context-window artefact — the agent didn't see the prior issue in its working set.

### attribution-gap
Work shows up on the board under a human's name with no marker that an agent performed it on the human's behalf. The human stays accountable but loses visibility into what they themselves did vs. what the agent did.

### ghost-edit
Agent modifies a board item without flagging itself as the actor. A sibling of attribution-gap, scoped to edits rather than creation.

### prompt-drift
The instructions in the repo (`CLAUDE.md`, `copilot-instructions.md`, slash-command prompts) no longer match what the agent is actually doing in practice. Usually because the agent's behaviour evolved through use without the prompt being updated.

### instruction-bypass
Agent skips a stated rule (duplicate check, repo-first edit, gate confirmation). Worth distinguishing from prompt-drift: the rule is still in the prompt, the agent just didn't follow it this time.

### manual-override
Human intervenes to fix agent output and the fix doesn't get fed back into the prompt or any maintained library. The agent makes the same mistake next time.

### blame-the-agent
Recurring framing of issues as *"the agent did X"* when the prompt is the actual root cause. The cousin of the general `blameless-violation`, scoped to human/agent relationships — and worth catching because the agent can't defend itself.

### context-bleed
Old session context leaks into a new conversation, producing stale references, wrong file paths, or actions on outdated assumptions.

### board-zombie
Items that haven't moved in N retros and no-one owns. Created by an agent on someone's behalf, then forgotten by both. The agentic-AI variant of `action-orphan`.

### silent-fail
A task is reported done by the agent but no artefact landed in the board or the work tree. The agent's self-report and the verifiable state of the world have diverged.

### acoustic-prioritisation
Loudest voice gets the agent's next slot instead of severity-driven priority. Strictly a process-AI hybrid: the canonical `conversational-dominance` patten extends to "whoever is most insistent gets the most agent-hours."

---

## Adding patterns

When your team discovers a new failure mode worth naming:

1. Decide which section it belongs in (general → Section A; agentic-AI → Section B). If it's general but missing a canonical source, that's fine — leave the citation line out.
2. Keep names hyphenated, lowercase, no leading articles.
3. Description ≤ 3 lines. The slug is what does the work; the description is just for the next maintainer.
4. If it has a canonical source, add it — that's what makes Section A trustworthy.

`/process-retro` reads this file every run, so additions take effect on the next retro without redeployment.
