# Rename hub → anchor

**Date:** 2026-08-25
**Status:** Accepted
**Board:** CAU-1410 (ported from awowio/AWO-260); locked in a `/solution-design-flow` session.

## Context
"Hub" names the topology, not the function the word actually carries in awow: the single
governing context a session resolves to and routes from. Every standalone repo "is its own hub",
so the word invites graph-thinking — mutual hubs, secondary hubs — which relitigates the core
invariant: exactly one context governs a session, and a session never crosses a repo boundary on
its own. The vocabulary is user-facing (setup, AGENTS.md, the session-start reflex) and freezes at
v1.0 (awowio/AWO-160), so renaming after the gate would break a public contract. Measured cost:
~205 `{HUB}` token refs (substituted centrally at build time), 4 code/test touchpoints, ~15
guide/README mentions.

## Decision
Rename before the v1.0 gate. An **anchor** governs; a repo is **anchored** (formerly a spoke) or
**standalone**. Mechanically: `awow: anchored` and `anchor:` frontmatter, `$AWOW_ANCHOR`,
`.awow/anchor.json`, the `{ANCHOR}` token, and the knowledge-sources `anchored:` block. The
machinery silently dual-accepts the legacy forms (`awow: spoke`, `hub:`, `$AWOW_HUB`,
`.awow/hub.json`); new writes always use the anchor forms. Historical proposals and merged docs
are not rewritten.

## Consequences
Existing anchored repos upgrade with no breakage — legacy registrations keep resolving. The
hub/spoke shorthand disappears from live docs and has to be relearned; the token sweep and test
churn is paid now, pre-1.0. Deliberately unstated: when (or whether) the legacy forms are removed
— v1.0 makes no statement about it, and removal is its own future decision.
