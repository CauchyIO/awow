# doc — archetype handler

A change to documentation or a small chore — a README, a guide, a runbook, a config tidy — that changes no behaviour. The durable artefact is text a reader can act on, in the place they will look for it.

This is a **starter archetype** shipped with awow. Edit it to match how your team actually writes and places documentation.

---

## When this archetype applies

The story asks to add, update, move or remove documentation, or to do a small chore that no caller would notice — with no change to what the system does.

Trigger words in the title or body: *README*, *doc*, *docs*, *document*, *guide*, *runbook*, *write up*, *chore*, *tidy*, *typo*.

If behaviour should change, route to `feature`. If the text documents a defect that needs fixing, route the fix to `bugfix`. If the story is really a question to answer, route to `spike`.

---

## Validation requirements

Before drafting a plan, confirm three things. If any are missing, stop and ask.

1. **The target and the reader are named.** Which file or page changes, and who reads it. "Improve the docs" names neither.
2. **What exists today has been read.** Search for the document or section already covering this, so the change edits it rather than writing a second copy.
3. **The facts have a source.** Every command, path, flag or number the text will state comes from the code, the story, or the user — never from memory.

---

## Planning rules

- **Edit before you add.** Extend the existing page or section; create a new file only when nothing covers the topic.
- **Place it where the reader looks.** Durable rationale goes to the knowledge base, reader-facing how-to next to what it describes, never into the story body.
- **State only what you verified.** Run the command, open the path, or read the code before you write it down.
- **Keep the diff to the text.** A doc story that also changes code is two stories.

---

## Common pitfalls

| Pitfall | Symptom | What to do instead |
|---|---|---|
| Duplicate page | Two documents now disagree | Edit the existing one; link rather than copy |
| Invented specifics | A command or path in the text does not exist | Verify each against the repo before writing it |
| Wrong place | The reader never finds it | Put it next to what it describes, or link it from there |
| Hidden code change | A "docs" PR also changes behaviour | Split the code change into its own story |

---

## Verification checklist (additions for this archetype)

In addition to the generic verification from `process-workitem` step 6:

- [ ] Each acceptance criterion maps to a check on the text: the file exists, the key sentence is there.
- [ ] Every command, path and link in the new text resolves.
- [ ] No second copy of the same content was created.
- [ ] The diff changes no behaviour.
