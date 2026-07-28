# incident — archetype handler

Something already broke in a running system. The deliverable is an evidence-backed account of *what happened and why* — the fix and the hardening are separate stories.

This is a **starter archetype** shipped with awow v0.1. Edit it to match how your team actually runs post-mortems.

---

## When this archetype applies

A live system misbehaved: an outage, data loss, a destructive change, a corrupted state, an unexpected production behaviour. The story asks you to reconstruct the sequence and name the root cause.

Trigger words in the title or body: *incident*, *post-mortem*, *postmortem*, *RCA*, *root cause*, *forensic*, *what happened*, *outage*, *data loss*, *broke in production*.

This archetype produces the **analysis**. The remediation belongs to a `bugfix`; durable prevention belongs to an `infra-change` or `feature`. If nothing has actually broken yet and you are assessing risk forward, route to `spike`.

---

## Validation requirements

Before starting, confirm three things. If any are missing, stop and ask.

1. **The symptom and blast radius are known.** What broke, for whom, and how widely. "Something is wrong" is not enough to start a forensic timeline.
2. **There is evidence to reconstruct from.** Logs, state history, deploy/commit timeline, audit trail. If the evidence is gone, say so — an honest "we cannot reconstruct this" beats a fabricated timeline.
3. **The timeframe is bounded.** A start and end for the window under investigation.

---

## Planning rules

- **Build a factual timeline first.** Timestamps, actors, and the exact commands / deploys / state changes — before any interpretation. The timeline is the spine of the analysis.
- **Name the root cause, distinct from the trigger and the symptom.** The trigger is what set it off; the root cause is the system gap that let the trigger do damage. Fixing only the trigger invites a repeat.
- **Separate analysis from remediation.** This story lands the writeup; spawn the fix and the hardening as their own tickets, linked back.
- **Do not mutate the broken system to "test theories"** without a deliberate, reversible plan — a forensic investigation must not become a second incident.

---

## Common pitfalls

| Pitfall | Symptom | What to do instead |
|---|---|---|
| Blaming the trigger | "Someone ran the wrong command" closes the case | Ask why the system *allowed* the command to do harm |
| Fix bundled into the investigation | The post-mortem PR also changes code | Land the analysis; spawn remediation as separate tickets |
| No durable writeup | The findings live in chat and evaporate | Record the timeline + root cause in the knowledge base |
| Blaming people, not systems | The conclusion is "be more careful" | Name the missing guardrail, the absent gate, the silent failure |

---

## Verification checklist (additions for this archetype)

In addition to the generic verification from `process-workitem` step 6:

- [ ] The timeline is reconstructed from evidence, with timestamps and actors — not from memory.
- [ ] The root cause is named and distinguished from the trigger and the symptom.
- [ ] Remediation and prevention are captured as separate, linked tickets.
- [ ] The writeup is landed in the knowledge base so the next on-call can learn from it.
