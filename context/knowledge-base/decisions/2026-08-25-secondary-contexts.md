# Secondary contexts: explicit reference, board-only writes

**Date:** 2026-08-25
**Status:** Accepted
**Board:** CAU-1410 (ported from awowio/AWO-260); locked in a `/solution-design-flow` session.

## Context
The need behind the mutual-hub sketches: a session in one team's repo sometimes must reach another
team's context or board — a cross-team ticket, a shared board. Until now the only designed
mechanism was read-only knowledge-source routing; board interaction across a repo boundary had no
design. Any answer must preserve the invariant that exactly one context governs a session and a
repo boundary is never crossed silently.

## Decision
One **primary anchor** governs `{ANCHOR}` and receives all context writes. Any other anchor is a
**secondary context**: reachable only by explicit reference in the invocation — a ticket id whose
prefix belongs to its board, or the board/anchor named outright. Resolution is per-invocation and
never re-pins the session. Allowed against a secondary: reads, and board writes on the explicitly
referenced items. Forbidden: context writes, silent fallback, scanning for candidates. Secondary
anchors are declared as knowledge-source records (canonical URI plus routing signals) — no new
registry.

## Consequences
Cross-team work becomes speakable without weakening governance: comments and state moves can land
on another team's board when the user names it, while each team's context stays writable only by
its own sessions. The knowledge-source catalog gains a second job — board reachability — which its
records must carry, and the resolution ladder's explicit-reference rung extends across anchors.
Implementation is a separate work item; nothing is built until it is picked up.
