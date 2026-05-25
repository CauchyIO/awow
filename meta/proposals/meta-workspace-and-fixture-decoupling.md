# Proposal — split `dogfood/` into a real `meta/` workspace and standalone test fixtures

**Status:** Landed — `dogfood/` to `meta/` rename and fixture decoupling implemented on `feature/dry_run_awow`.
**Scope:** resolve the dual role `dogfood/` currently plays (illustrative demo *and* regression-fixture master) by promoting it to awow's genuine awow-on-awow workspace, renamed `meta/`, and severing the test fixtures so they stand alone as snapshots of a clean installation. Top-level template surface and the GitHub board as execution source of truth are unchanged.

---

## Why

`dogfood/` was created to demonstrate that the awow starter pack works on itself, and its README frames it as *illustrative only* — "not the source of truth for awow product decisions," "real product work lives on GitHub issues/PRs," "adopters can delete it." But two things drifted from that charter:

1. **Real product proposals accumulated in `dogfood/proposals/`.** `plugin-distribution.md`, `board-noise-pruning.md`, `session-board-correlation.md`, `superpowers-integration-shape.md`, and `setup-awow-regression-tests.md` are genuine meta-work about awow itself — two of them are literally drafts of GitHub issues against `CauchyIO/awow`. They are load-bearing product decisions sitting inside a folder its own README calls deletable and non-authoritative. That contradiction is the trigger for this proposal.

2. **`dogfood/` is also the regression-fixture master.** `tests/setup-awow/README.md` states the suite does two jobs at once: regression coverage of `/setup-awow` *and* "a pinned replay of `dogfood/`," with fixtures past Step 0 being "frozen snapshots of `dogfood/` at the corresponding step." This couples a (would-be) living workspace to a deterministic test corpus — re-walking dogfood forces a fixture re-audit, and a churning workspace would silently break the suite.

So `dogfood/` is simultaneously a demo, a real proposal archive, and the test-fixture source. Those are three different jobs with conflicting requirements (curated-and-stable vs. live-and-evolving).

## Recovered rationale — why dogfood was *not* the real dev workspace

Three structural reasons, recovered from the code and docs, explain why awow's own development was deliberately kept out of a normal workspace:

- **The top-level surface must stay empty stubs.** `context/team/mission.md` etc. read "TODO — `/setup-awow` Step 1 produces this file." Adopters clone via "Use this template" and inherit these blanks. Filling the top level with awow's real content would ship Cauchy's data to every adopter. So there is no top-level real workspace *by design*.
- **Dogfood doubled as the test golden-example,** which requires it to be curated and stable, the opposite of a live workspace.
- **The GitHub board (`CauchyIO/awow`) is already the execution source of truth** — issues, PRs, project. Markdown proposals are drafts en route to issues, not a parallel backlog.

None of these forbids a *real* awow-on-awow workspace; they only explain why it couldn't be the top level and why it shouldn't share a folder with the test fixtures.

## Target architecture

| Surface | Role | Content | Lifecycle |
|---|---|---|---|
| top-level `context/` | **Template** (ships to adopters) | Empty stubs | Unchanged |
| `tests/setup-awow/fixtures/` | **Regression fixtures** | Self-contained snapshots of a clean installation at step N | Frozen; standalone |
| `meta/` (was `dogfood/`) | **Real awow-on-awow workspace** | awow's actual mission, members, conventions, board config (→ `CauchyIO/awow`), and real product proposals | Live; evolves freely |
| GitHub `CauchyIO/awow` | **Execution source of truth** | Issues / PRs / project | Unchanged |

`meta/` is the honest answer to "what does a real awow team repo look like" — because it *is* one. The agent reads it (via `--root meta/`, the mechanism that already backs the `--root dogfood/` example) when maintainers run awow commands on awow.

## The consequence to accept

Severing the fixtures from the master means **the fixtures become standalone synthetic test data** rather than derivatives of a live folder. This is the right call: tests must never depend on a churning workspace. Practically, today's `dogfood/`-derived state is frozen into the fixtures once and stops tracking anything afterward. The maintenance rule "re-audit fixtures whenever dogfood is re-walked" disappears — a net simplification. The suite continues to run the *real* command prompts against the fixtures, so `/test-setup-awow` still proves the wizard works end-to-end as an installation would experience it.

## Migration plan

1. **Sever fixtures from the master.** Freeze current `dogfood/`-derived state into each `fixtures/<scenario>/` so they are standalone. Rename `dogfood-*` scenarios to installation-flavoured names (e.g. `install-step1-cli`, `install-walkthrough`). Update `scripts/`, `rubrics/`, `tests/setup-awow/README.md` (rewrite the "pinned replay of dogfood" principle → "snapshots of a clean installation"), and the `--root dogfood/` example in `.agents/commands/setup-awow.md`.
2. **Rename `dogfood/` → `meta/`** and rewrite its README: from "demonstration / not source of truth / deletable" → "awow's real awow-on-awow workspace; adopters may still delete it."
3. **Relocate the real proposals** into `meta/proposals/` (this file included), as genuine drafts-en-route-to-issues.
4. **Sweep references** to `dogfood` across `mcps/README.md`, board reference docs, `/awow-reset` scope notes, and anywhere else `grep` finds them.
5. **Verify**: run `/test-setup-awow` to confirm the suite still passes against the now-standalone fixtures.

## Open decisions

- **Scenario naming:** drop "dogfood" entirely from the renamed fixtures (assumed yes — it is no longer a concept once severed).
- **Branch:** land on `feature/dry_run_awow` or a fresh branch.
- **`meta/` scope:** confirmed full workspace (real `context/` the agent reads), not just a proposal archive.
