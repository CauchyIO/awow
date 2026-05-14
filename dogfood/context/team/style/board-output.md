# Board output style

Brevity is non-negotiable. See `context/team/conventions/REQUIRED/output-discipline.md` for the canonical rules.

This file covers the *voice* and *shape* of board output beyond the brevity rules.

## Voice

- Terse, declarative. Active voice.
- No hedging ("we think", "perhaps", "might"). Either we know or we ask.
- No marketing language. No "ensures", "enables", "leverages", "robust".
- No em-dashes in board output. Em-dashes belong in prose, not in story bodies or comments. (The maintainer's prose elsewhere uses them; the board does not.)

## Shape

- Story title: verb-first, per `conventions/REQUIRED/issue-titles.md`.
- Story body: one-sentence intent + acceptance criteria checklist + link to knowledge base (if applicable). Nothing else.
- Comments: status, blocker, intermediate finding. One paragraph max.

## awow-specific

- The `dogfood` label appears on every walkthrough-generated issue (see `conventions/REQUIRED/labels.md`). Without it, the issue is treated as durable backlog.
- Pull request titles follow the same pattern as story titles. No "WIP" prefix — use draft PRs instead.
