# spike — archetype handler

A time-boxed investigation. The deliverable is a decision backed by evidence, not shippable code.

This is a **starter archetype** shipped with awow v0.1. Edit it to match how your team actually runs investigations.

---

## When this archetype applies

The story asks a question, evaluates options, or assesses feasibility — and no production code is expected to come out of it directly.

Trigger words in the title or body: *investigate*, *spike*, *research*, *evaluate*, *assess*, *explore*, *prototype*, *feasibility*, *compare*, *proof of concept*.

Once the spike produces a decision, the work it implies is a *separate* `feature` or `bugfix` story. If the story already knows what to build, it is not a spike.

---

## Validation requirements

Before starting, confirm three things. If any are missing, stop and ask.

1. **The question is explicit and answerable.** "Look into caching" is not a question. "Will a read-through cache cut p95 below 200ms for endpoint X?" is.
2. **A time-box is set.** A spike without a limit becomes unbounded building. Agree the budget before starting.
3. **"Done" is a decision, not code.** Confirm the output is a recommendation the team can act on — not a half-built implementation.

---

## Planning rules

- **Respect the time-box.** When it runs out, stop and report what you found, even if the answer is "inconclusive, needs more time" — then re-scope deliberately.
- **Capture findings in a durable artefact**, not just chat: a knowledge-base entry or a proposal. Chat scrolls away; the decision must outlive the session.
- **End with a recommendation and the follow-up stories it implies.** A spike that ends without a "therefore, do X" has not finished.
- **Throwaway prototype code stays throwaway.** Do not smuggle exploration code into production; if it is worth keeping, that is a new `feature` story with its own bar.

---

## Common pitfalls

| Pitfall | Symptom | What to do instead |
|---|---|---|
| Spike becomes a build | The time-box passed and you are still coding | Stop at the box; spin the build out as its own story |
| Findings lost in chat | The decision lives only in the transcript | Write it to the knowledge base or a proposal |
| Prototype shipped | Exploration code lands in production | Keep it throwaway; re-build under a `feature` story |
| No decision at the end | "Here is what I found" with no recommendation | Force a "therefore, do X" before closing |

---

## Verification checklist (additions for this archetype)

In addition to the generic verification from `process-workitem` step 6:

- [ ] The original question is answered, with evidence for the answer.
- [ ] A recommendation is recorded in a durable location (knowledge base / proposal), not just chat.
- [ ] Follow-up stories implied by the decision are created.
- [ ] The time-box was respected, or the overrun was made explicit and re-scoped.
