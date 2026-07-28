# Knowledge base — paths & wiring

Where the durable knowledge base and its staging inbox live. The KB contracts and
commands resolve these two locations **from here**, so a team can relocate them without
editing every contract. This file is at a fixed path (like `board.md`); its *contents*
are what a team edits.

## Paths

| Logical name | Default | What lives there |
|---|---|---|
| `kb_root` | `context/knowledge-base/` | The durable layer — `architecture/`, `patterns/`, `runbooks/`, `decisions/`, `glossary.md` — plus the KB contracts that operate on it (`README.md`, `mining.md`, `mining-policy.md`, `synthesis.md`). |
| `inbox` | `context/kb-inbox/` | Committed staging for durable-knowledge candidates awaiting promotion (`README.md`, `_synthesis-log.md`, and the candidate files). |

To relocate either, change its path in the table above **and move the folder to match**.
`/setup-awow` Step 6 offers to set these. Everything that reads or writes the KB resolves
the location from this file.

## Resolution rule (for agents)

Read this file before acting on the KB. The KB contracts and commands write the default
paths (`context/knowledge-base/…`, `context/kb-inbox/…`) inline for readability; **if the
table above declares a different `kb_root` or `inbox`, those override the inline
literals.** Cross-references *within* `kb_root` (e.g. `mining.md` → `mining-policy.md`)
are relative and move with the folder, so they need no resolution.

## Constraints

- Both are **committed** folders (unlike the gitignored `activity/` snapshots), so
  relocating them does not touch `.gitignore`.
- Keep `kb_root` and `inbox` as **distinct** folders — the drain (`synthesis.md`) moves
  files out of `inbox` into `kb_root`; nesting one inside the other breaks that hand-off.
- These are the only two KB locations that are configurable. The ephemeral `activity/`
  snapshots and `digests/` output are fixed by design.
