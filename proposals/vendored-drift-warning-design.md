# Vendored Drift Warning — Design Spec

**Status:** Draft (Arie, 2026-08-25). Derived from [CAU-1338.md](CAU-1338.md), which carries the
root cause and review trail; implementation sequencing lives in
[plans/2026-08-25-vendored-drift-warning.md](plans/2026-08-25-vendored-drift-warning.md).
Board item:
[CAU-1338](https://linear.app/cauchyio/issue/CAU-1338/warn-when-a-vendored-installs-machinery-drifts-behind-the-installed).

**Goal:** A session in a vendored awow install stops silently running a stale machinery vintage.
Three acceptance criteria drive everything here: (1) a session detects when vendored machinery is
older than the installed plugin payload and surfaces a one-line drift warning; (2) the precedence
rule (vendored beats payload) and its branch-vintage consequence are documented where adopters
will find them; (3) the payload version string distinguishes rebuilds. This spec defines the
stamp format and digest algorithm, the complete detection decision table, both warning messages
verbatim, both documentation edits verbatim, the full test matrix, and the interaction with every
open PR. Nothing is left open.

## 1. Scope and non-goals

In scope: two helpers plus two per-surface plan wrappers in `tools/gather.py` and two generated
stamp files (`dist/.claude-plugin/build.json`, `dist-telemetry/.claude-plugin/build.json`); one
new tier in `hooks/session-start.py` (two message constants, five pure functions, one
`build_context` branch); one new section in `context/tooling/context-resolution.md` and one
sentence in `.agents/AGENTS.md` §Reading machinery; one new test file
`tests/payload-manifests/test_build_stamp.py`, one `NO_DECLARED_PATHS` registration in
`tests/payload-manifests/test_manifest_integrity.py`, ten checks appended to
`tests/hooks/test_session_start.py`, and one CI step.

One declared dependency: **CAU-1335 (PR #77) must merge first.** It creates
`context/tooling/context-resolution.md` (the file §4.1 appends to) and
`tests/hooks/test_wrong_root_guard.py` (in the close-out battery). `hooks/session-start.py` and
`tests/hooks/test_session_start.py` are byte-identical on main and the CAU-1335 branch, so every
anchor in §3 and §5 is stable across the merge.

Non-goals, closed deliberately:

- **No ordering beyond semver.** When versions are equal but digests differ, the warning says the
  payloads *differ*; it does not claim which is older. Git ancestry or build dates could order
  them, and both were rejected (§8, D-1).
- **No opt-out file.** The warning reports a live condition, the same policy as `SPOKE_DRIFTED`.
  Setup and engine nudges are one-time offers and have opt-outs; drift is neither.
- **No change to `tools/check-dist-published.py`.** Upgrading its bare-version compare to a digest
  compare is a recorded follow-up, not this work.
- **No lockfile backfill.** A vendored adopter predating `tools/awow.lock.json` stays silent
  (§3.4, S-4); `/migrate-to-plugin`'s backfill is the existing route that gives such a repo a
  vintage.
- **No plugin version bump** in this change; releases are driven by their own bump PRs.
- **No eval scenario.** Detection is mechanical — file reads and string compares — so hook unit
  tests carry the regression; conduct is not at stake.
- **No cleanup of this repo's stale `tools/awow.lock.json`** (0.7.0, lists files PR #66 deleted).
  §3.2's ordering makes it harmless here; its cleanup is a separate flagged task.

## 2. The build stamp (AC3)

### 2.1 File and schema

Every generated payload root carries `.claude-plugin/build.json`:

```json
{
  "version": "0.12.0",
  "content": "sha256:3f9a1c2b4d5e"
}
```

- `version` — copied from the canonical `.claude-plugin/plugin.json`, exactly as every payload
  manifest version already is.
- `content` — `"sha256:" + first 12 hex chars` of the digest defined in §2.2.

Stamped roots: `dist/` and `dist-telemetry/`. The `awow-dist` mirror inherits `dist/`'s stamp
verbatim through `tools/sync-dist.sh` (it mirrors the tree; no change needed). The m365 package
is not stamped (§2.4).

### 2.2 Digest algorithm (normative)

Input: the complete list of planned `Stub`s for the surface, **excluding the stamp file itself**
(it cannot be part of its own input or the build never converges). `BinaryStub`s never occur on
the stamped surfaces (m365-only). Then:

```
sort stubs by posix(target relative to the payload root)
D = sha256( concat over stubs of:  utf8(posix relpath) ‖ 0x00 ‖ utf8(content) ‖ 0x00 )
content = "sha256:" + hex(D)[:12]
```

Properties, each load-bearing:

- **Deterministic.** No clock, no commit hash, no randomness: the stamp is a pure function of the
  source tree, so `gather.py --check` (CI, every push) stays green across rebuilds of an
  unchanged tree.
- **Location-independent.** Paths hash relative to the payload root, so every checkout of the
  same tree produces the same digest.
- **Order-independent.** Sorting removes plan-assembly order as an input.
- **Mode-blind.** `Stub.mode` (exec bits) is excluded: content changes are the vintage signal,
  and a mode-only change without a content change does not alter behavior a session would
  observe through machinery reads.
- **Surface-stable.** The dist digest covers exactly the stubs of the five plugin-surface plan
  functions, never the m365 stubs nested under `dist/m365/` — their inclusion depends on
  `--surface`, and a surface-dependent digest would make `--check` disagree between invocations.

12 hex chars = 48 bits: ample to distinguish vintages (the only job), no security claim intended
or needed.

### 2.3 Display form

Wherever a stamp is rendered for a human it reads `<version>+<digest-without-prefix>`, e.g.
`0.12.0+3f9a1c2b4d5e` — semver build-metadata syntax, without touching any manifest's actual
`version` field. The display form appears only in the §3.3 messages; no other surface prints it
in this change.

### 2.4 gather.py integration

Four additions, no behavior change elsewhere:

```
payload_stamp(root: Path, stubs: list[Stub], version: str) -> str   # §2.1 JSON, §2.2 digest
stamp_stub(root: Path, stubs: list[Stub]) -> Stub                   # the planned build.json
dist_surface_plans() -> list[Stub]      # plan_plugin + plan_agent_skills + plan_codex
                                        #   + plan_pi + plan_opencode_plugin, + their stamp
telemetry_surface_plans() -> list[Stub] # plan_telemetry + its stamp
```

`main()` swaps its five dist `plans +=` lines for `dist_surface_plans()` and the telemetry line
for `telemetry_surface_plans()`. The m365 branch is untouched. The stamp is a planned stub, so
the orphan sweep protects it and `--check` validates it like any other payload file.

### 2.5 Guard-rail registration

`tests/payload-manifests/test_manifest_integrity.py` sweeps every `*.json` under the payload
roots and fails on manifests absent from its registry. Both stamp files are registered in
`NO_DECLARED_PATHS` (they declare no filesystem paths). Their version equality with the canonical
manifest is asserted by the new stamp suite (§5.1), so the AWO-155-class protections hold.

## 3. Session-start drift detection (AC1)

### 3.1 Tier placement

`hooks/session-start.py build_context()` gains one branch between the spoke tier and the setup
nudge — the tiers stay mutually exclusive (`spoke_context` returns None for adopted repos, and
the setup nudge already requires not-adopted):

```
spoke        -> spoke tier message (unchanged)
adopted      -> vendored_drift_context(plugin_root, repo_dir), appended when not None   [NEW]
plain repo   -> setup nudge (unchanged)
```

The engine nudge below is untouched and can stack with the drift warning, exactly as it stacks
with tier messages today.

### 3.2 Detection decision table (normative)

`vendored_drift_context(plugin_root, repo_dir)` — `plugin_root` is the installed payload (the
hook's own install location), `repo_dir` the session's repo. First matching row wins:

| # | Condition | Result |
|---|-----------|--------|
| D1 | installed stamp absent or unreadable (`read_stamp(plugin_root)` is None) | **silent** — pre-stamp payload, nothing to compare (§3.5 rollout) |
| D2 | `repo_dir/.claude-plugin/plugin.json` exists (maintainer checkout) and `repo_dir/dist/` has no readable stamp | **maintainer warning**, repo side rendered `unstamped (predates build stamps)` — a checkout too old to carry a stamp is behind every stamped payload by definition; this is the recorded 2026-08-19 incident shape |
| D3 | maintainer checkout, repo `dist/` stamp ≠ installed stamp (either field) | **maintainer warning** naming both stamps in display form |
| D4 | maintainer checkout, stamps equal | **silent** |
| D5 | not a maintainer checkout, `tools/awow.lock.json` has an `awow_version` that parses as dotted integers and is strictly `<` the installed stamp's version (tuple compare) | **adopter warning** |
| D6 | anything else | **silent** |

The maintainer test (D2–D4) is keyed on `.claude-plugin/plugin.json` — the same gate
`gather.py main()` builds behind — and **must precede** the lockfile branch: the maintainer repo
also carries a stale legacy `awow.lock.json` (0.7.0), and routing it into D5 would prescribe
`/migrate-to-plugin` to the repo that builds the plugin.

Pure-function decomposition (house style: decision logic in small pure functions, text in
constants): `read_stamp(root) -> (version, digest) | None`, `stamp_display(stamp) -> str`,
`lock_version(repo_dir) -> str`, `semver_tuple(version) -> tuple | None`,
`vendored_drift_context(plugin_root, repo_dir) -> str | None`. Python floor 3.9 — no
`str.removeprefix`.

### 3.3 The two messages, verbatim

Both begin `awow drift:` — the machine-greppable prefix and the tests' silence sentinel. One
message per session maximum (the decision table yields at most one row).

```python
VENDORED_DRIFT_MAINTAINER = (
    "<important-reminder>awow drift: this checkout's dist/ payload is "
    "{repo_stamp} but the installed plugin payload is {installed_stamp}. "
    "Machinery reads follow this checkout ({{HUB}}-first), so this session "
    "runs the checkout's vintage — if that is unexpected, rebuild and run the "
    "branch payload (python tools/gather.py && claude --plugin-dir dist) or "
    "re-sync the installed plugin.</important-reminder>"
)

VENDORED_DRIFT_ADOPTER = (
    "<important-reminder>awow drift: this repo vendored awow {vendored} but "
    "the installed plugin payload is {installed}. Vendored files win "
    "({{HUB}}-first), so this session runs the {vendored} vintage. Run "
    "/migrate-to-plugin to de-vendor and pick up the installed "
    "payload.</important-reminder>"
)
```

The maintainer message deliberately fires in **both drift directions** (checkout behind the
installed payload *and* installed cache behind the checkout): the inverse direction is the
AWO-156 failure shape at the plugin-cache level, equally silent today, and the remedy line covers
both. The adopter message fires only when strictly older (D5) — a vendored tree *ahead* of the
payload has no sane cause other than deliberate edits, which the precedence rule exists to
protect.

### 3.4 Silence rules

Enumerated, each a deliberate decision:

- **S-1** Installed payload unstamped → silent (D1). No false alarms against pre-stamp installs.
- **S-2** Maintainer stamps equal → silent (D4).
- **S-3** Adopter `awow_version` equal to or newer than the installed version → silent (D6).
- **S-4** Adopter with no lockfile, or an `awow_version` that does not parse as dotted integers →
  silent (D6). An unreadable vintage must never *assert* drift; `/migrate-to-plugin` backfill is
  the route to a comparable vintage.
- **S-5** Unreadable or schema-invalid `build.json` on either side → treated as absent (D1/D2
  semantics). Corruption degrades to the conservative behavior, never a crash — the hook wraps
  every read in the same try/except discipline the spoke tier uses.

### 3.5 Rollout behavior

Detection arms itself: until the *installed* plugin cache updates to a stamped payload, D1 keeps
every session silent. The first cache sync after this ships turns detection live, including
retroactively for old checkouts (D2 needs no cooperation from the old branch). No migration, no
flag day.

## 4. Documentation (AC2)

### 4.1 New section in `context/tooling/context-resolution.md` (verbatim, appended after §The write boundary)

```markdown
## Machinery precedence and vintage

Machinery reads are `{HUB}`-first by design: a contract a team vendored **and deliberately
edited** must keep winning over the shipped `{AWOW_ROOT}` default. The rule keys on file
presence, so a vendored install runs whatever vintage the current checkout carries — a branch
cut before an upstream change, or an install never updated, wins exactly like a customization,
silently serving the older content.

Every built payload names its vintage in `.claude-plugin/build.json`: the canonical version plus
a digest of the payload content, displayed `<version>+<digest>`, so two rebuilds of one version
are distinguishable. At session start the drift check compares the installed payload's stamp
against the checkout — the maintainer repo's `dist/` stamp, or a legacy vendored repo's
`tools/awow.lock.json` vintage — and surfaces a one-line `awow drift:` warning naming both sides
when they differ. `/migrate-to-plugin` retires a legacy vendored tree; in the maintainer repo,
`python tools/gather.py && claude --plugin-dir dist` runs the checkout's own payload.
```

This file ships in the payload (CAU-1335 put it in `PAYLOAD_CONTEXT_PATHS`), so the rule reaches
every adopter through the same `{HUB}`-first/`{AWOW_ROOT}`-fallback read it describes.

### 4.2 `.agents/AGENTS.md` §Reading machinery (verbatim, appended to the paragraph)

> The vintage consequence — a merely *old* vendored file wins exactly like an edited one — and
> the session-start drift warning that names it are specified in §Machinery precedence and
> vintage of the context-resolution contract.

A pointer, not a copy — the CAU-1335 no-drift pattern for AGENTS.md/contract pairs.

### 4.3 Channel coverage

The mechanical check runs on every harness that executes the plugin's SessionStart hook (Claude
Code, Cursor, Copilot CLI — the three platforms `session-start.py` already emits for). Harnesses
without a hook surface (Codex, Pi, opencode) get AC2's documented rule as their guard — the same
hook-where-available / prompt-elsewhere split CAU-1335 shipped for the write boundary.

## 5. Tests

Literal test code lives in the implementation plan; this section is the normative assertion list.

### 5.1 Build-stamp suite — `tests/payload-manifests/test_build_stamp.py` (new)

Stdlib check-style, imports `gather` like `tests/gather-tokens/test_tokens.py`. Asserts, against
the *plan* (no disk writes):

1. `dist_surface_plans()` carries exactly one stamp stub at `dist/.claude-plugin/build.json`.
2. The stamp's `version` equals the canonical `.claude-plugin/plugin.json` version.
3. The digest matches `sha256:[0-9a-f]{12}`.
4. Two consecutive plan builds produce identical stamps (determinism).
5. The digest recomputes from the non-stamp stubs alone (self-exclusion, §2.2).
6. Reversing stub order leaves the digest unchanged (order-independence).
7. Mutating one planned stub's content changes the digest (sensitivity).
8. No m365 path appears in the dist digest input (surface-stability).
9. `telemetry_surface_plans()` is stamped by the same mechanism with the canonical version.
10. The two payloads' digests differ.

### 5.2 Hook-tier checks — appended to `tests/hooks/test_session_start.py`

Two fixtures (`_stamped_plugin(version, digest)`, `_vendored_project(maintainer, dist_stamp,
lock_version)`), then, with an installed stamp of `0.13.0+aaaa11112222`:

| Check | Fixture | Asserts |
|---|---|---|
| maintainer drift names both stamps | maintainer, dist `0.12.0+bbbb33334444` | both display forms in context (D3) |
| maintainer drift explains precedence + remedies | same | `{HUB}-first` and `--plugin-dir dist` in context |
| matching stamps stay silent | maintainer, dist `0.13.0+aaaa11112222` | no `awow drift` (D4) |
| unstamped maintainer checkout warns | maintainer, no dist stamp | `unstamped` + installed display form (D2) |
| stale lockfile cannot misroute | maintainer, dist stamp differs, lock `0.7.0` | maintainer message, no `/migrate-to-plugin` (§3.2 ordering) |
| older adopter warned toward the exit | lock `0.7.0` | `0.7.0` + `/migrate-to-plugin` (D5) |
| adopter equal stays silent | lock `0.13.0` | no `awow drift` (S-3) |
| adopter newer stays silent | lock `0.14.0` | no `awow drift` (S-3) |
| unparseable vintage stays silent | lock `not-a-version` | no `awow drift` (S-4) |
| unstamped installed payload stays silent | unstamped plugin, maintainer + lock `0.7.0` | no `awow drift` (S-1/D1) |

Every pre-existing check in the file must still pass (the drift tier is inert for all existing
fixtures: none carries an installed stamp). The existing dist-verbatim-copy assertions force the
gather rebuild into the same commit.

### 5.3 CI

One step after "Payload manifest integrity":
`python3 tests/payload-manifests/test_build_stamp.py`. The session-start step already runs the
§5.2 checks; `gather.py --check` already validates the committed stamps.

## 6. Interaction with open PRs (reviewed 2026-08-25)

Touch set: `tools/gather.py`, `hooks/session-start.py`, `tests/hooks/test_session_start.py`,
`tests/payload-manifests/*`, `.github/workflows/ci.yml`, `context/tooling/context-resolution.md`,
`.agents/AGENTS.md`, regenerated `dist/` + `dist-telemetry/`.

| PR | Overlap | Verdict |
|---|---|---|
| **#77** CAU-1335 | `AGENTS.md`, `ci.yml`, creates `context-resolution.md`, `hooks/hooks.json`, dist | **Declared dependency, not a conflict** — this work branches after it merges (plan Task 0 verifies). |
| **#76** CAU-1332 preflight impl | dist renders of `setup-awow` only | **No source overlap.** Post-merge interplay: its next gather rebuild updates `build.json` — expected (§6.1). Note: its spec's P7 "payload freshness" check is adjacent in spirit; P7 probes install-channel staleness inside `/setup-awow`, this work probes vintage divergence at session start — complementary, no shared code. |
| **#75** CAU-1410 hub→anchor rename | none today (two KB decision docs) | **Coordination note, not a conflict.** Its *implementation* will sweep `{HUB}` tokens and rework the spoke tier in `session-start.py`, the file our tier lands in. Our tier touches no spoke/anchor resolution code, and our `{{HUB}}-first` literals in the two message constants are exactly the "code touchpoints" its sweep enumerates — whichever lands second pays a two-line rebase. |
| **#74** board-source wiring | none (`board.md` is team data, not payload) | No conflict. |
| **#73** CAU-1333 setup surface | `.agents/AGENTS.md` | **No textual conflict** — its only AGENTS.md hunk is the session-correlation step renumber at ~line 123; ours appends at line 27. Its dist/context churn interacts only via §6.1. |
| **#72** README rewrite | none | No conflict. |
| **#71** CAU-1332 proposal+spec | `proposals/` only | No conflict. Establishes the committed-spec practice this file follows (`git add -f` past `proposals/.gitignore`). |
| **#53 / #50 / #45** eval PRs (stale, ≤2026-08-08) | #45 touches `ci.yml` | Both changes append independent steps; a revival resolves trivially. No other overlap. |

### 6.1 The standing dist-churn rule, extended

Every payload-touching PR already regenerates `dist/`; after this lands, each such rebuild also
updates the affected `build.json` — that is the stamp doing its job. Cross-PR `dist/` collisions
resolve today by rebasing and re-running `python tools/gather.py`; the stamp adds one more
generated file to that same rule and changes nothing about it.

## 7. Acceptance criteria, restated testable

1. **Detect + one-line warning.** A session whose installed payload stamp differs from its
   vendored vintage per §3.2 receives exactly one `awow drift:` line in its session-start
   context; every §3.4 silence case receives none. Proven by the ten §5.2 checks, including the
   recorded incident shape (D2/D3).
2. **Documented where adopters find it.** §Machinery precedence and vintage ships inside the
   payload's own copy of the resolution contract (grep-verified post-gather), and AGENTS.md
   §Reading machinery points at it.
3. **Version string distinguishes rebuilds.** Two payloads built from different source trees
   carry different `<version>+<digest>` stamps even at the same semver; the same tree always
   restamps identically. Proven by §5.1 assertions 4–7.

## 8. Decisions closed

- **D-1 Content digest, not commit hash or build date.** A commit or clock stamp breaks
  `--check` idempotency (CI would flap or every commit would churn `dist/`); content is the only
  input that is both deterministic and exactly the thing vintage means.
- **D-2 Sidecar `build.json`, not semver build-metadata in the manifests.** Mutating manifest
  `version` fields risks marketplace/installer version-compare semantics on four harnesses for
  zero gain; a sidecar is inert everywhere except where it is read.
- **D-3 12-hex truncation.** Distinguishing vintages needs collision resistance against
  accident, not adversaries; 48 bits is plenty and keeps the display form scannable.
- **D-4 Maintainer warning is bidirectional; adopter warning is strictly-older-only.** §3.3
  rationale: the inverse maintainer direction is AWO-156 at the cache level; an "ahead" vendored
  adopter is the deliberate-edit case the precedence rule protects.
- **D-5 Maintainer marker is `.claude-plugin/plugin.json`, checked before the lockfile.** Same
  gate gather.py builds behind; ordering defuses the maintainer repo's own stale lockfile.
- **D-6 An unstamped maintainer checkout warns (D2)** rather than staying silent: it is provably
  behind every stamped payload, and it is the exact recorded incident.
- **D-7 No opt-out; mode bits excluded; unparseable vintages silent** — §1, §2.2, §3.4.
- **D-8 The stamp is a planned stub** (orphan-swept, `--check`-validated, registered in
  `NO_DECLARED_PATHS`), never a post-build side effect.
