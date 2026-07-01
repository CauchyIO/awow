# Synthesis log

Append-only provenance of the synthesis drain (`context/knowledge-base/synthesis.md`).
One line per drained candidate — never edited, never a candidate itself. The git
history of `context/knowledge-base/` is the audit trail; this log is the human-readable
index into it.

Format, one line per disposition:

```
YYYY-MM-DD  <inbox-file>  →  <disposition>  <target-or-note>   # optional note
```

Dispositions: `promoted` (new note written) · `annotated` (existing note strengthened) ·
`no-op` (already covered) · `dropped` (too thin / noise).

<!-- entries below, newest last -->
