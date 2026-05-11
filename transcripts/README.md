# Transcripts

**Ephemeral input.** Drop meeting transcripts here; `/process-transcript` reads them and produces structured proposals. The contents of this folder are **gitignored** — transcripts are not committed.

## Naming

`<YYYY-MM-DD>-<meeting-name>.vtt` (or `.txt`, `.md`)

Use ISO dates so chronological sort works. Meeting name should be terse and recognisable: `refinement`, `retrospective`, `architecture-review`, `1on1-with-X`.

## Lifecycle

1. Drop the transcript file.
2. Run `/process-transcript transcripts/<file>`.
3. The agent produces a proposal at `proposals/transcripts/<date>-<meeting>.md`.
4. Review and selectively land items on the board / knowledge base.
5. The raw transcript can be deleted; the structured output is what persists.

## Why ephemeral

Per the blog (§9 in `input/PROPOSAL.md`'s anchor), meeting transcripts often contain personal data (under GDPR Article 4). The trace pipeline records *file references*, not transcript content. Keeping transcripts gitignored avoids accidentally committing personal data.

Teams that want longer-term transcript retention should configure a dedicated retention surface outside this repo (e.g. an enterprise meeting platform's transcript archive).

## What's tracked

- `README.md` (this file)
- `.gitkeep`
- `.gitignore` (ignores everything except the three files above)
