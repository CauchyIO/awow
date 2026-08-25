# Proposal — preflight prerequisite check for `/setup-awow`

**Status:** Accepted (2026-08-25). Spec derived:
[setup-awow-preflight-design.md](setup-awow-preflight-design.md) — the full check matrix, both
prompt edits verbatim, and complete test definitions. Implementation due.
**Board item:** [CAU-1332 — add a prerequisite preflight to setup-awow](https://linear.app/cauchyio/issue/CAU-1332/add-a-prerequisite-preflight-to-setup-awow)
**Scope:** `/setup-awow` verifies its prerequisites up front and tells the user how to fix what is
missing, instead of failing midway or silently adopting whatever is configured. Explicit non-goals:
per-step prerequisite gating, a machine-checkable `prerequisites:` frontmatter field, and preflight
for other commands — each a separate proposal if it ever earns one.

---

## Why

`/setup-awow` assumes a working environment and only discovers a broken one at the point of use.
From the adopter's perspective: install the plugin, run `/setup-awow`, and the wizard dies
mid-Step-1b with an MCP error, or scaffolds context files into a directory that is not a git
repository. The failure surfaces far from its cause, and the fix-it knowledge lives in the
maintainer's head, not in the wizard's output.

The motivating incident is real: a Linear MCP registered at **local scope** in Claude Code —
available in the one folder it was added from, silently absent everywhere else. A drafting session
could not reach the AWO board and nothing in the session said why (the origin of CAU-1332). Worse,
a wizard that merely *detects* ambient MCP config would have silently adopted whichever server it
found — the right server on one machine, the wrong one on another.

## Acceptance criteria

1. **Preflight checks with install pointers.** Every invocation probes, before the step map:
   git present, workspace-is-a-repo, board surface usable from this session, gh CLI present +
   authenticated (GitHub-family boards only — git is the universal check, gh is not), and
   harness-specific needs (current-harness wiring, the declared harness roster, local payload
   freshness). Each miss is reported with a pointer to the fix.
2. **Explicit board-MCP confirmation.** The board surface is never inherited silently from
   ambient machine config. Candidates are enumerated with provenance (which config file or scope
   supplies each server); the user picks one explicitly at Step 1a; only the identity (server
   name + endpoint) is ever recorded — provenance is machine-local and stays unrecorded.
   Divergence between the recorded identity and the live session triggers re-confirmation, never
   a silent switch.
3. **Preflight makes no changes.** Read-only in full: no installs, no MCP registration, no
   `git init`, no file writes — state files included. The one confirmation write belongs to
   Step 1a's normal flow.

## Decision summary

- **Check matrix P1–P7** (spec §2): git on PATH and workspace-is-a-repo are **fatal** — stop with
  a pointer, print no step map, offer no self-repair. Board surface (P3), gh (P4, GitHub-family
  only), and current-harness wiring (P5) are **soft** — the wizard continues and gates only the
  steps that need the missing piece, using the existing `pending` / `pending-write` vocabulary.
  Declared-other-harness probes (P6) and payload freshness (P7, local channels only, no network)
  are **informational**.
- **Visual Studio covered via its bridge** (spec §2.5–2.7): VS never reads the Copilot plugin
  store, so the checks are the Copilot CLI on PATH, the awow plugin in
  `~/.copilot/installed-plugins/`, and a fresh `~/.copilot/skills/.awow-bridge.json` marker —
  every miss points at the three-command onboarding (`marketplace add` → `plugin install` →
  `/awow-vs`). Specced now; activates when the `visual-studio-channel` proposal lands, with an
  explicit not-yet-shipped note until then.
- **Four-state board check** (spec §3): *n/a* (nothing to check — Step 1a wires it),
  *unconfirmed* (candidates exist, none in use until confirmed), *ok* (recorded identity live +
  one read call succeeds), *blocked* (recorded identity unusable — reason and repair named, incl.
  the local-scope MCP gotcha from the incident).
- **Zero-writes preflight**: the confirmation is asked and recorded only inside a hardened
  Step 1a §2 — enumerate, explicit pick, record `board-mcp: <name> <endpoint> (confirmed <date>)`
  in `setup-progress.md`, verification failure recorded as `surface-verification: pending`,
  never papered over.
- **Re-probed every invocation, never persisted** — recorded auth status lies; the repeated read
  call is the freshness signal.
- **Two prompt edits**, drafted verbatim in the spec: the new `## Preflight` section plus the
  Step 1a §2 replacement in `.agents/commands/setup-awow.md`; rebuild via `tools/gather.py`.
- **Tests** (spec §6): the `/test-awow` runner gains a default `git init -q` in scratch (unless a
  scenario's setup hook owns state); invariants 15–18 join the suite (invariant 1 gains "after a
  passing preflight"); three new scenarios with complete definitions — `preflight-not-a-repo`,
  `preflight-board-blocked`, `preflight-ambient-unconfirmed` — all on deterministic
  `*.example.invalid` decoy endpoints, no real board contact.

## Plan of attack

1. Prompt edits per spec §5; `python tools/gather.py`.
2. Runner default per spec §6.1; canary: `tools/validate-evals.py`, then re-run `clean-clone`
   and `install-step0-inherited`.
3. Author the three scenarios per spec §6.3; run them.
4. Rewalk `install-walkthrough` to confirm no step-map regression.
5. Comment progress on CAU-1332 as each lands.

## Review trail

- 2026-08-25 — brainstorm: scope fixed to a customer-perspective environment preflight
  (plugin-install first); failure semantics fixed to report + gate per check.
- 2026-08-25 — grill: gh made conditional (not everyone uses GitHub; ADO exists — git is the
  universal check); harness checks widened to current wiring + declared roster + local freshness;
  confirmation fixed to zero-writes preflight with Step 1a recording identity only. `git init`
  self-repair dropped against AC 3. All former open decisions closed in spec §8.
- 2026-08-25 — spec review: install pointers platform-matched (winget primary on Windows,
  chocolatey as a team-preference alternative); Visual Studio peculiarities folded in as
  bridge-chain checks (Copilot CLI → plugin store → `.awow-bridge.json`) with roster-conditional
  MCP candidate locations, conditioned on the `visual-studio-channel` draft landing.
- 2026-08-25 — review: VS runs no commands off the bat (per that draft's no-command-surface /
  approval-gated execution findings) — every VS pointer now names the Copilot CLI session as
  where to run it, and a preflight running inside Visual Studio degrades to file-reads-only with
  a CLI redirect instead of a stream of approval prompts.
