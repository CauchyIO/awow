# One discovery worker: assess-or-replay, land, activate

**Date:** 2026-08-25
**Status:** Accepted

## Context
leadgen ran two discovery lanes: a certified, ledger-driven worker whose admission demanded an
empty grid matching a 6-seat manifest (locked out since the grid grew on 2026-08-20), and an
uncertified, file-driven drain that authored recipes 19-wide but dropped the vacancies it verified.
Nothing landed a vacancy after 2026-08-20; 56 active recipes were never replayed.

## Decision
One ledger-driven worker: per claimed domain, author-and-verify a recipe or replay the active one
(generic crawl as fallback), land verified facts in `company_vacancy`, seal evidence, and activate
under the worker's own claim (env kill-switch). Admission is "free seats ≥ width" with the grid's
identity and capacity still pinned — exclusivity goes, certification stays. The drain lane is retired.
Design: leadgen `docs/superpowers/specs/2026-08-25-one-discovery-worker-design.md`.

## Consequences
Vacancies land again and recipes are validated continuously; the grid is shared by width. Accepted:
recipes activate without a human (merge gate, decay revisits, kill-switch guard it); a batch seal
claims "certified grid, N free seats", not "idle grid"; an LLM walk per new domain. "The product is
the delta to the scraper" stays the priority and the measure — facts-on-first-visit is an addition.
