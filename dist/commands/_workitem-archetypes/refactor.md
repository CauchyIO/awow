# refactor — archetype handler

A change to structure that leaves observable behaviour identical. The durable artefact is a green test suite proving nothing changed for the caller.

This is a **starter archetype** shipped with awow v0.1. Edit it to match how your team actually restructures code.

---

## When this archetype applies

The story asks to restructure, simplify, extract, rename, or de-duplicate — with no change to what the system does from the outside.

Trigger words in the title or body: *refactor*, *restructure*, *clean up*, *extract*, *rename*, *simplify*, *de-duplicate*, *modularise*, *tidy*.

If behaviour should change, route to `feature`. If the change fixes a defect, route to `bugfix`. The moment a "refactor" alters observable behaviour, it is no longer a refactor — re-classify it.

---

## Validation requirements

Before drafting a plan, confirm three things. If any are missing, stop and ask.

1. **A behaviour safety net exists.** Tests pin the current behaviour you intend to preserve. If they do not exist, the first step is adding characterisation tests — not restructuring.
2. **The equivalence claim is explicit.** State plainly what stays the same (the public interface, the outputs, the side effects). That claim is what verification checks.
3. **A reason.** Refactors compete with feature work; the story should say what the restructure unlocks or unblocks. "Cleaner" is not a reason on its own.

**Do not restructure code with no test coverage and no characterisation tests first.** You cannot prove equivalence you never captured.

---

## Planning rules

- **Change structure, not behaviour.** If you find a bug mid-refactor, stop and raise it as a separate `bugfix` — do not fix it in the same diff.
- **Keep the diff mechanical and reviewable.** A reviewer should be able to see at a glance that nothing observable moved.
- **Land in small green steps.** Each step keeps the suite passing; avoid one giant irreversible diff.
- **Do not bundle opportunistic feature work.** "While I was in here…" is how refactors hide behaviour changes.

---

## Common pitfalls

| Pitfall | Symptom | What to do instead |
|---|---|---|
| Behaviour drift hidden in a refactor | A test changes meaning, not just shape | Revert the behaviour change; raise it as its own story |
| No safety net | "Tests pass" but the tests never covered this path | Add characterisation tests before touching structure |
| Giant diff | Reviewer cannot tell what is equivalent | Break into small steps, each independently green |
| Bundled fix or feature | The refactor PR also "fixes a thing" | Separate the change; one intent per story |

---

## Verification checklist (additions for this archetype)

In addition to the generic verification from `process-workitem` step 6:

- [ ] The full test suite is green both before and after, with no test assertions changed in meaning.
- [ ] Public interfaces / outputs / side effects are unchanged (or the story explicitly scoped the change).
- [ ] The diff contains no behaviour change; anything behavioural was split into its own story.
- [ ] The reason the refactor unlocks is recorded, so the cost is justified.
