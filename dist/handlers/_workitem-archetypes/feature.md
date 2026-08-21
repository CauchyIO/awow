# feature — archetype handler

A net-new capability the system does not have yet. The durable artefact is the thinnest slice that satisfies the acceptance criteria and nothing more.

This is a **starter archetype** shipped with awow v0.1. Edit it to match how your team actually ships features.

---

## When this archetype applies

The story names a capability to add or a behaviour to introduce: new endpoint, new screen, new command, new option, new integration. The system is not broken — it simply does not do this yet.

Trigger words in the title or body: *add*, *implement*, *introduce*, *support*, *enable*, *create*, *new*.

If the story names broken behaviour, route to `bugfix`. If it restructures existing code without changing behaviour, route to `refactor`. If it only asks a question or evaluates options, route to `spike`.

---

## Validation requirements

Before drafting a plan, confirm three things. If any are missing, stop and ask.

1. **Testable acceptance criteria.** Each criterion describes observable behaviour, not implementation. "Returns 404 for unknown IDs" — not "adds a guard clause."
2. **Scope boundary.** What is explicitly *out* of this story. A feature with no out-of-scope line invites gold-plating.
3. **Preconditions and dependencies.** What must already exist (data, an upstream service, a decision). If the story implies an unmade architectural decision, surface it before planning — do not decide it silently.

**Do not start coding from a story whose "done" is undefined.** Vague acceptance criteria produce scope drift.

---

## Planning rules

- **Ship the thinnest vertical slice that satisfies the acceptance criteria.** One working path end-to-end beats a half-built general solution.
- **Name the interface/contract before the implementation** — the function signature, the endpoint shape, the config key. Iterate on that with the user; it is the cheap thing to change.
- **Defer the trimmings.** Observability, refactors, extra config surfaces, and docs are follow-up stories unless an acceptance criterion demands them.
- **Do not build for an imagined future.** Generality the story does not ask for is scope you cannot verify.

---

## Common pitfalls

| Pitfall | Symptom | What to do instead |
|---|---|---|
| Gold-plating | The PR does far more than the AC asked | Deliver exactly the AC; open follow-ups for the rest |
| Kitchen-sink story | "Implement X, add tests, refactor Y, update docs" in one item | Split before planning; one shippable slice per story |
| AC written as implementation | "Add a cache layer" with no observable outcome | Rewrite AC as behaviour the user can see |
| Architectural decision left to the agent | The agent silently picks a pattern the team never agreed | Surface the decision as an open question first |

---

## Verification checklist (additions for this archetype)

In addition to the generic verification from `process-workitem` step 6:

- [ ] Each acceptance criterion has explicit evidence (test, demo, or check).
- [ ] New behaviour is covered by a test at the appropriate level.
- [ ] The diff contains nothing beyond what the AC required; tangential work is a separate proposal.
- [ ] Deferred trimmings (observability, docs, refactors) are captured as follow-up stories, not silently dropped.
