# Changelog

What each awow release changed, newest first. A section is added by the pull
request that bumps the version in `.claude-plugin/plugin.json`:
`python tools/release-notes.py --changelog CHANGELOG.md` drafts it from the
pull requests merged since the previous release, and the author trims it in
that same PR. When the PR lands on `main`, the release workflow publishes the
section as the body of the GitHub release and tags the commit. Releases before
v0.9.2 were not tagged individually; `git log` is their record.

## v0.12.0

### Commands
- **Feature** The strategy family on one route: `/strategy-flow` (vision → bets → committed/aspirational KR draft, two gates) and the `bet-refinement-coach` skill (one bet through a live board session, translate round included) join the payload, genericized; `department-coach` becomes the single battery home, and the never-built `/strategic-review` resolves into `/okr-cascade` Review. The route ships in the session reflex, each skill's frontmatter, and the catalog. (#70)
- **Feature** `/board-lifecycle`: govern the project layer — mutually exclusive `shape:*` labels, shape-specific horizons, the reversible `Needs decision` exception via an approval-gated plan (no auto-close in any path), the tripwire convention, the new-work routing ladder, and the sign-off ledger for adopting the mechanism on a lived-in board. Activity timestamps are never the staleness signal. (#70)

## v0.11.0

### Commands
- **Feature** `/migrate-to-plugin`: de-vendor a repo the plugin now serves — read-only classification (lockfile 3-way, vendor-commit compare, source-history match; unresolved means edited), edit migration to plugin-era homes, a plan gate with zero writes before approval, and a before/after parity report. Verified against real pre- and post-lockfile vendored fixtures. (#69)

### Harnesses and distribution
- **API** `/update-awow` is retired from source; existing vendored copies keep working in place, and `/migrate-to-plugin` is the way off the vendored channel. (#69)
- **Feature** The payload ships `tools/awow_lock.py`, so a migration always runs the current engine rather than the repo's vendored vintage. (#69)

## v0.10.0

### Harnesses and distribution
- **API** Retire the vendoring route — `/awowify`, its engine and the vendor stamp — and ship the archetype handler registries under `dist/handlers/` instead of the auto-discovered command surface. (#64)
- **API** Retire the maintainer repo's pointer-stub surface: commands and skills reach every session through the plugin payload, and `awow-add`, `awow-reset`, `awow-status` and `project-manager` are retired with it. (#66)
- **Feature** Self-driving release: a version bump landing on `main` tags the commit, opens the awow-dist publish PR, and publishes the GitHub release from this file. (#67)

### Commands
- **Feature** Team-owned workitem archetypes: `context/team/workitem-archetypes/` overlays the shipped handlers, so a team can add or replace an archetype without vendoring. (#65)
- **Feature** `/handover`: ask who the handover is for, then write for that reader. (#61)
- **Feature** Hat-aware setup orientation, the diff-style board plan gate, and the repo-local invoker profile. (#62)

### Context and contracts
- **Feature** Context resolution — which installation, which board: the two-stage ladder in `AGENTS.md` and the index-form `board.md`. (#44)

### Build and CI
- **Feature** Reserve `awow` on PyPI through a dispatch-only trusted-publishing workflow. (#63)

## v0.9.2

### Harnesses and distribution
- **Enhancement** AWO-156: Authenticate the git push inside sync-dist.sh. (#60)
- **Fix** AWO-156: Tie publishing to the tag, fix the Copilot payload, bump to 0.9.2. (#58)
- **Enhancement** AWO-120: Tier the distribution surface and slim the session reflex. (#46)
- **Fix** Fix department-layer lint violations and wire the m365/department/awow-lock suites into CI. (#42)
- **Enhancement** M365 Copilot harness: design spec + Phase-1 try-out slice (gather --surface m365). (#40)
- **Feature** Support the opencode harness (AWO-48). (#39)
- **Enhancement** PR6: Fail-loud session-start bootstrap + payload path guard. (#36)
- **Enhancement** PR4: Plugin-first README + situation-shaped command descriptions. (#34)
- **API** PR3: Split telemetry into the awow-telemetry plugin. (#33)
- **Enhancement** PR1: Payload addressability via the {AWOW_ROOT} path token. (#31)
- **Enhancement** Hub-and-spoke WI-5: Codex + Pi harness packaging. (#28)
- **Enhancement** Hub-and-spoke design + WI-1/WI-2: path tokens, plugin emitter, path lint. (#25)

### Commands
- **Enhancement** AWO-133: Spoke self-registration — /setup-awow spoke track, tiered session reflex, dual-PR handshake. (#55)
- **Feature** Add meeting-aware transcript setup. (#51)
- **Enhancement** AWO-121: workitem-write — one convention-wired path for board creates and updates. (#47)
- **Enhancement** Dissolve meta/ into proposals/ + tests/fixtures, make docs/ local-only, harden /refinement-prep. (#43)
- **Enhancement** Department layer, increment one: cascade_check sweep, layer profile, /setup-department + /okr-cascade. (#41)
- **Enhancement** PR5: /update-context autofire command. (#35)
- **Enhancement** PR2: Trim the shipped command surface + board fallback. (#37)

### Context and contracts
- **Feature** Add canonical knowledge-source routing. (#52)
- **Enhancement** Safe lockfile backfill for repos that predate the update machinery (AWO-5). (#38)

### Docs
- **Enhancement** Guides: replace the HTML gallery with terse, cross-linked markdown. (#49)
- **Fix** Sanitize internal gateway references in hub-and-spoke design proposal. (#29)

### Other
- **Enhancement** AWO-156: Give the runner a git identity before the publish commit. (#59)
- **Enhancement** AWO-133: Port session-start to Python behind a thin shim. (#57)

