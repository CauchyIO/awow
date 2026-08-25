# Vendored Drift Warning (CAU-1338) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A session in a vendored awow install detects when its machinery vintage differs from the installed plugin payload and surfaces a one-line drift warning, backed by a content-derived build stamp that distinguishes payload rebuilds.

**Architecture:** `tools/gather.py` stamps each payload root with `.claude-plugin/build.json` — the canonical version plus a sha256 digest of the planned payload content (deterministic: no clock, no commit, so CI's `gather.py --check` never flaps). The SessionStart hook grows a vendored-tier drift check mirroring the existing spoke tier: maintainer checkouts compare their `dist/` stamp against the installed payload's stamp; legacy vendored adopters compare their `tools/awow.lock.json` vintage against the installed version. The precedence rule and its branch-vintage consequence land in the shipped context-resolution contract.

**Tech Stack:** Python (stdlib only — house rule: no pytest), bash test shims, GitHub Actions CI.

**Spec:** `proposals/vendored-drift-warning-design.md` (normative design: stamp format, detection decision table, verbatim messages and doc edits, test matrix, open-PR review). Root cause and review trail: `proposals/CAU-1338.md`. Board item: [CAU-1338](https://linear.app/cauchyio/issue/CAU-1338/warn-when-a-vendored-installs-machinery-drifts-behind-the-installed). On any divergence between this plan's inline code and the spec's normative sections, the spec wins — fix the plan.

**Dependency — do not start before CAU-1335 merges to main.** Task 3 appends to `context/tooling/context-resolution.md` and Task 4's battery runs `tests/hooks/test_wrong_root_guard.py`; both exist only in the CAU-1335 work (branch `arie/cau-1335-reproduce-and-fix-proposal-writes-landing-in-the-wrong-repo`, commit d1500f7), which is not yet on main. Task 0 verifies this precondition. (`hooks/session-start.py` and `tests/hooks/test_session_start.py` are identical on both branches, so Task 2's anchors are safe either way; `tools/gather.py` differs by one `PAYLOAD_CONTEXT_PATHS` line, hence the `~` line references.)

**Board linkage / intent:** Bug — a stale vendored file silently beats a newer plugin payload under the `{HUB}`-first rule (observed 2026-08-19: pre-PR-#62 branch rendered the old board-plan gate under an installed 0.9.2 payload). Acceptance criteria from the ticket:
1. A session detects when vendored machinery is older than the installed plugin payload and surfaces a one-line drift warning → **Task 2**.
2. The precedence rule (vendored beats payload) and its branch-vintage consequence are documented where adopters will find them → **Task 3**.
3. The payload version string distinguishes rebuilds → **Task 1**.

## Global Constraints

- **Stdlib only** in hooks and tests; no pytest. Tests are executable scripts printing `PASS`/`FAIL` lines, exit 1 on any failure (see `tests/hooks/test_session_start.py`).
- **Hook message wording is asserted by tests** — change text and tests together (stated at `hooks/session-start.py:26-27`).
- **Hook house style:** decision logic in small pure functions; user-facing text in module-level constants (`hooks/session-start.py:14-16`). Tier messages are wrapped in `<important-reminder>…</important-reminder>`.
- **`dist/` and `dist-telemetry/` are generated — never hand-edit.** Any change to `hooks/*` or `context/` machinery requires `python tools/gather.py` in the same commit; CI's `gather.py --check` and the verbatim-copy assertions in `tests/hooks/test_session_start.py:231-234` enforce this.
- **Payload content must be a deterministic function of the source tree.** No timestamps, commit hashes, or randomness anywhere in planned content — CI runs `python tools/gather.py --check` on every push (`.github/workflows/ci.yml:16`).
- **Stamp schema (exact):** `{"version": "<semver>", "content": "sha256:<12 hex>"}` written to `<payload root>/.claude-plugin/build.json`. Digest input: `(path relative to the payload root, content)` pairs sorted by path, the stamp file excluded from its own input, `mode` bits excluded.
- **Drift messages begin `awow drift:`** (inside the reminder tag) — tests use that prefix as the silence sentinel.
- **Hook Python floor:** `session-start.py` runs on adopter machines via `python3`; avoid APIs newer than Python 3.9 (no `str.removeprefix`).
- **Commits:** `CAU-1338: <what>` style, ending with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- **Branch:** work on `arie/cau-1338-warn-when-a-vendored-installs-machinery-drifts-behind-the`, cut from `main` **after** the CAU-1335 PR has merged (Task 0 verifies).

## File Structure

| File | Responsibility |
|---|---|
| `tools/gather.py` | Stamp helpers (`payload_stamp`, `stamp_stub`) + per-surface plan wrappers (`dist_surface_plans`, `telemetry_surface_plans`) used by `main()` |
| `tests/payload-manifests/test_build_stamp.py` | **New.** Stamp determinism, recomputability, order-independence, content sensitivity |
| `tests/payload-manifests/test_manifest_integrity.py` | Register the two `build.json` files in `NO_DECLARED_PATHS` (its sweep rglobs `*.json` under payload roots and fails on unknown manifests) |
| `.github/workflows/ci.yml` | One new step running the stamp test |
| `hooks/session-start.py` | Vendored-tier drift check: message constants + pure functions + `build_context` wiring |
| `tests/hooks/test_session_start.py` | New fixtures (`_stamped_plugin`, `_vendored_project`) + drift-tier checks |
| `context/tooling/context-resolution.md` | New §Machinery precedence and vintage (ships in the payload) |
| `.agents/AGENTS.md` | One consequence sentence in §Reading machinery pointing at the contract |
| `dist/`, `dist-telemetry/` | Regenerated by gather (never hand-edited) |
| `proposals/CAU-1338.md` | Status + verification updates at the end; committed with the spec and plan via `git add -f` in Task 4 (house practice per PRs #71/#77) |

---

### Task 0: Branch setup

**Files:** none (git only)

- [ ] **Step 1: Verify the CAU-1335 dependency has landed, then cut the working branch**

```bash
cd "$(git rev-parse --show-toplevel)"
git checkout main && git pull
test -f context/tooling/context-resolution.md && test -f tests/hooks/test_wrong_root_guard.py \
  && echo DEPENDENCY-MET || echo "STOP: CAU-1335 not merged yet"
git checkout -b arie/cau-1338-warn-when-a-vendored-installs-machinery-drifts-behind-the
```

Expected: `DEPENDENCY-MET`. On `STOP`: do not proceed — report that CAU-1335's PR must merge first.

---

### Task 1: Content-derived payload build stamp (AC3)

**Files:**
- Modify: `tools/gather.py` (imports at ~line 66; new helpers after `plan_plugin()` ends at ~line 981; `main()` surface wiring at ~lines 1075-1082)
- Create: `tests/payload-manifests/test_build_stamp.py`
- Modify: `tests/payload-manifests/test_manifest_integrity.py` (`NO_DECLARED_PATHS`, ~line 31)
- Modify: `.github/workflows/ci.yml` (after the "Payload manifest integrity" step, ~line 28)

**Interfaces:**
- Consumes: existing `gather.Stub` (frozen dataclass: `target: Path`, `content: str`, `mode: int | None`), `gather.PLUGIN_MANIFEST`, `gather.DIST_DIR`, `gather.DIST_TELEMETRY_DIR`, `gather.M365_ROOT`, and the five dist plan functions `plan_plugin/plan_agent_skills/plan_codex/plan_pi/plan_opencode_plugin` plus `plan_telemetry`.
- Produces (Task 2 and tests rely on these exact names):
  - `payload_stamp(root: Path, stubs: list[Stub], version: str) -> str` — the `build.json` content string.
  - `stamp_stub(root: Path, stubs: list[Stub]) -> Stub` — the planned stamp file for a payload root.
  - `dist_surface_plans() -> list[Stub]` and `telemetry_surface_plans() -> list[Stub]` — full per-surface plans **including** their stamp.
  - On-disk artifacts: `dist/.claude-plugin/build.json` and `dist-telemetry/.claude-plugin/build.json` with the exact schema from Global Constraints.

- [ ] **Step 1: Write the failing test**

Create `tests/payload-manifests/test_build_stamp.py`:

```python
#!/usr/bin/env python3
"""Build-stamp determinism over the payload plans (CAU-1338 AC3).

The stamp at <payload root>/.claude-plugin/build.json distinguishes rebuilds:
same source tree -> same stamp; any planned content change -> a new digest.
It must be a pure function of the plan (no clock, no commit), or
`gather.py --check` would flap on every CI run.

Pure stdlib; no pytest, no network.

Run:  python3 tests/payload-manifests/test_build_stamp.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import importlib

gather = importlib.import_module("gather")

FAILURES = []


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILURES.append(label)


def stamp_of(plans, root):
    target = root / ".claude-plugin" / "build.json"
    found = [p for p in plans if p.target == target]
    check(f"{root.name}: plan carries exactly one build stamp", len(found) == 1)
    return json.loads(found[0].content) if found else {}


def main() -> int:
    version = json.loads(gather.PLUGIN_MANIFEST.read_text())["version"]
    plans = gather.dist_surface_plans()
    stamp = stamp_of(plans, gather.DIST_DIR)
    others = [p for p in plans
              if p.target != gather.DIST_DIR / ".claude-plugin" / "build.json"]

    check("stamp carries the canonical version", stamp.get("version") == version)
    check("digest is sha256:<12 hex>",
          re.fullmatch(r"sha256:[0-9a-f]{12}", stamp.get("content", "")) is not None)
    check("a second plan build produces an identical stamp",
          stamp == stamp_of(gather.dist_surface_plans(), gather.DIST_DIR))
    check("digest recomputes from the non-stamp stubs alone",
          json.loads(gather.payload_stamp(gather.DIST_DIR, others, version))["content"]
          == stamp.get("content"))
    check("stub order does not affect the digest",
          json.loads(gather.payload_stamp(
              gather.DIST_DIR, list(reversed(others)), version))["content"]
          == stamp.get("content"))
    mutated = [gather.Stub(others[0].target, others[0].content + "x",
                           others[0].mode)] + others[1:]
    check("a planned content change flips the digest",
          json.loads(gather.payload_stamp(gather.DIST_DIR, mutated, version))["content"]
          != stamp.get("content"))
    check("m365 never enters the dist digest input",
          all(gather.M365_ROOT not in p.target.parents for p in others))

    tstamp = stamp_of(gather.telemetry_surface_plans(), gather.DIST_TELEMETRY_DIR)
    check("telemetry stamp carries the canonical version",
          tstamp.get("version") == version)
    check("the two payloads carry different digests",
          tstamp.get("content") != stamp.get("content"))

    if FAILURES:
        print(f"\n{len(FAILURES)} failing")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/payload-manifests/test_build_stamp.py`
Expected: traceback ending `AttributeError: module 'gather' has no attribute 'dist_surface_plans'` — the correct red (feature missing). Any other error (ImportError, SyntaxError) is a test bug: fix and re-run.

- [ ] **Step 3: Implement the stamp in gather.py**

3a. Add `import hashlib` to the import block (alphabetical, next to `import json` at ~line 66).

3b. After `plan_plugin()` (it ends returning `plans` at ~line 981, just before `SURFACE_ROOTS`), add:

```python
def payload_stamp(root: Path, stubs: list[Stub], version: str) -> str:
    """build.json content for one payload root: the canonical version plus a
    digest of the planned payload, so two rebuilds of the same version are
    distinguishable (CAU-1338). Content-derived only — no clock, no commit —
    keeping the build a deterministic function of the source tree so --check
    cannot flap. Paths hash relative to the payload root and sorted, so
    neither the checkout location nor plan assembly order matters; mode bits
    are excluded (content changes are the vintage signal)."""
    h = hashlib.sha256()
    for stub in sorted(stubs, key=lambda s: s.target.relative_to(root).as_posix()):
        h.update(stub.target.relative_to(root).as_posix().encode())
        h.update(b"\0")
        h.update(stub.content.encode())
        h.update(b"\0")
    return json.dumps(
        {"version": version, "content": f"sha256:{h.hexdigest()[:12]}"},
        indent=2, ensure_ascii=False) + "\n"


def stamp_stub(root: Path, stubs: list[Stub]) -> Stub:
    """The planned stamp file for a payload root, digesting every OTHER stub
    (the stamp cannot be part of its own input or the build never converges)."""
    version = json.loads(PLUGIN_MANIFEST.read_text())["version"]
    return Stub(root / ".claude-plugin" / "build.json",
                payload_stamp(root, stubs, version))


def dist_surface_plans() -> list[Stub]:
    """Every dist/ stub for --surface plugin, plus the build stamp over them.

    m365 (independently managed, nested under dist/) deliberately never enters
    the digest: its stubs join the plan only under --surface m365/all, and a
    surface-dependent digest would make --check disagree between invocations."""
    plans = (plan_plugin() + plan_agent_skills() + plan_codex() + plan_pi()
             + plan_opencode_plugin())
    return plans + [stamp_stub(DIST_DIR, plans)]


def telemetry_surface_plans() -> list[Stub]:
    """The dist-telemetry/ plan plus its build stamp — same mechanism as dist/."""
    plans = plan_telemetry()
    return plans + [stamp_stub(DIST_TELEMETRY_DIR, plans)]
```

3c. In `main()` (~lines 1075-1082), replace the surface wiring:

```python
    if DIST_DIR in surfaces:
        plans += plan_plugin()
        plans += plan_agent_skills()
        plans += plan_codex()
        plans += plan_pi()
        plans += plan_opencode_plugin()
    if DIST_TELEMETRY_DIR in surfaces:
        plans += plan_telemetry()
```

with:

```python
    if DIST_DIR in surfaces:
        plans += dist_surface_plans()
    if DIST_TELEMETRY_DIR in surfaces:
        plans += telemetry_surface_plans()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/payload-manifests/test_build_stamp.py`
Expected: all `PASS`, exit 0. (The test never touches disk — it exercises the plan, so an unrebuilt `dist/` cannot fail it.)

- [ ] **Step 5: Apply the build and prove idempotency + the second red**

```bash
python tools/gather.py            # writes the two build.json files
python tools/gather.py --check    # must print "All payloads in sync." (idempotent)
python3 tests/payload-manifests/test_manifest_integrity.py
```

Expected: `--check` green on the second run; the manifest integrity test **FAILS**, naming `dist/.claude-plugin/build.json` (and the telemetry one) as manifests not listed in `EXTRACTORS`/`NO_DECLARED_PATHS` — the correct red for step 6.

- [ ] **Step 6: Register the stamps as path-free manifests**

In `tests/payload-manifests/test_manifest_integrity.py` extend `NO_DECLARED_PATHS` (~line 31):

```python
NO_DECLARED_PATHS: tuple[str, ...] = (
    # source "./" is the payload root itself, which trivially exists.
    "dist/.agents/plugins/marketplace.json",
    # Build stamps: version + content digest, no filesystem paths (CAU-1338).
    "dist/.claude-plugin/build.json",
    "dist-telemetry/.claude-plugin/build.json",
)
```

- [ ] **Step 7: Verify green across the touched suites**

```bash
python3 tests/payload-manifests/test_manifest_integrity.py
python3 tests/payload-manifests/test_build_stamp.py
python3 tests/telemetry-split/test_telemetry_split.py
python3 tests/telemetry-split/test_orphan_roots.py
python tools/gather.py --check
```

Expected: all pass. (telemetry-split and orphan tests guard payload-root ownership the stamp files now participate in.)

- [ ] **Step 8: Wire the stamp test into CI**

In `.github/workflows/ci.yml`, after the "Payload manifest integrity" step:

```yaml
      - name: Payload build stamp determinism
        run: python3 tests/payload-manifests/test_build_stamp.py
```

- [ ] **Step 9: Commit**

```bash
git add tools/gather.py tests/payload-manifests/test_build_stamp.py \
  tests/payload-manifests/test_manifest_integrity.py .github/workflows/ci.yml \
  dist/ dist-telemetry/
git commit -m "CAU-1338: stamp each payload with a content-derived build.json so two rebuilds of one version are distinguishable — sha256 over the planned stubs, deterministic by construction, --check-safe

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Vendored-tier drift check in the SessionStart hook (AC1)

**Files:**
- Modify: `hooks/session-start.py` (constants after `ENGINE_NUDGE` ~line 88; pure functions after `spoke_context` ~line 198; wiring in `build_context` ~lines 213-231)
- Modify: `tests/hooks/test_session_start.py` (fixtures after `_spoke_project` ~line 113; checks after the "plain root AGENTS.md" block ~line 223, before the payload-guard section)
- Regenerate: `dist/` (the hook ships verbatim; `tests/hooks/test_session_start.py:231-234` compares source vs dist byte-for-byte)

**Interfaces:**
- Consumes: `dist/.claude-plugin/build.json` schema from Task 1; `tools/awow.lock.json`'s top-level `awow_version` key (written by the legacy vendoring install, see `tools/awow_lock.py` docstring); the maintainer-repo marker `.claude-plugin/plugin.json` (the same gate `gather.py main()` uses at ~line 1067).
- Produces (all in `hooks/session-start.py`):
  - `VENDORED_DRIFT_MAINTAINER`, `VENDORED_DRIFT_ADOPTER` — message constants, both beginning `<important-reminder>awow drift:`.
  - `read_stamp(root) -> tuple[str, str] | None` — `(version, digest)` from `<root>/.claude-plugin/build.json`.
  - `stamp_display(stamp) -> str` — `"<version>+<digest>"`.
  - `lock_version(repo_dir) -> str` — `awow_version` or `""`.
  - `semver_tuple(version) -> tuple | None`.
  - `vendored_drift_context(plugin_root, repo_dir) -> str | None` — the tier message, `None` when aligned or undecidable.

- [ ] **Step 1: Write the failing tests**

In `tests/hooks/test_session_start.py`, add two fixtures directly after `_spoke_project` (after ~line 113):

```python
def _stamped_plugin(version, digest):
    """A plugin root whose payload carries a build stamp (Task-1 schema)."""
    d = _plugin(payload_skill="PAYLOAD-SENTINEL")
    os.makedirs(os.path.join(d, ".claude-plugin"))
    with open(os.path.join(d, ".claude-plugin", "build.json"), "w") as f:
        json.dump({"version": version, "content": "sha256:" + digest}, f)
    return d


def _vendored_project(maintainer=False, dist_stamp=None, lock_version=None):
    """An adopted (vendored) repo: .agents/AGENTS.md always; optionally the
    maintainer marker (.claude-plugin/plugin.json), a dist/ build stamp, and
    a legacy lockfile with an awow_version."""
    d = _tmpdir()
    os.makedirs(os.path.join(d, ".agents"))
    open(os.path.join(d, ".agents", "AGENTS.md"), "w").close()
    if maintainer:
        os.makedirs(os.path.join(d, ".claude-plugin"))
        with open(os.path.join(d, ".claude-plugin", "plugin.json"), "w") as f:
            json.dump({"name": "awow", "version": "0.0.0"}, f)
    if dist_stamp is not None:
        os.makedirs(os.path.join(d, "dist", ".claude-plugin"))
        with open(os.path.join(d, "dist", ".claude-plugin", "build.json"), "w") as f:
            json.dump({"version": dist_stamp[0],
                       "content": "sha256:" + dist_stamp[1]}, f)
    if lock_version is not None:
        os.makedirs(os.path.join(d, "tools"))
        with open(os.path.join(d, "tools", "awow.lock.json"), "w") as f:
            json.dump({"awow_version": lock_version, "files": {}}, f)
    return d
```

Then add the check block after the "plain root AGENTS.md still gets the setup nudge" check (~line 223), before the `# Payload guard` section:

```python
# --- Vendored drift tier (CAU-1338) -----------------------------------------
# Messages begin "awow drift:", the silence sentinel for every negative check.
STAMPED = _stamped_plugin("0.13.0", "aaaa11112222")

# Maintainer checkout whose dist/ stamp differs from the installed payload:
# the recorded incident shape — warn, naming both stamps and the remedies.
ctx, _, _ = _run(STAMPED, project=_vendored_project(
    maintainer=True, dist_stamp=("0.12.0", "bbbb33334444")))
check("maintainer drift names both stamps",
      "0.12.0+bbbb33334444" in ctx and "0.13.0+aaaa11112222" in ctx)
check("maintainer drift explains precedence and the remedies",
      "{HUB}-first" in ctx and "--plugin-dir dist" in ctx)

# Matching stamps: silent.
ctx, _, _ = _run(STAMPED, project=_vendored_project(
    maintainer=True, dist_stamp=("0.13.0", "aaaa11112222")))
check("matching stamps stay silent", "awow drift" not in ctx)

# A maintainer branch too old to carry a stamp is behind every stamped
# payload by definition: warn, never fall through to the adopter branch.
ctx, _, _ = _run(STAMPED, project=_vendored_project(maintainer=True))
check("unstamped maintainer checkout warns",
      "unstamped" in ctx and "0.13.0+aaaa11112222" in ctx)

# The maintainer repo also carries a stale legacy lockfile; the maintainer
# compare must win or the repo that builds the plugin would be told to
# /migrate-to-plugin (misroute guard).
ctx, _, _ = _run(STAMPED, project=_vendored_project(
    maintainer=True, dist_stamp=("0.12.0", "bbbb33334444"), lock_version="0.7.0"))
check("maintainer with stale lockfile gets the maintainer message",
      "--plugin-dir dist" in ctx and "/migrate-to-plugin" not in ctx)

# Legacy vendored adopter behind the installed payload: warn, name the exit.
ctx, _, _ = _run(STAMPED, project=_vendored_project(lock_version="0.7.0"))
check("older vendored adopter is pointed at /migrate-to-plugin",
      "0.7.0" in ctx and "/migrate-to-plugin" in ctx)

# Adopter at, ahead of, or unparseable vs the payload: silent.
for v in ("0.13.0", "0.14.0", "not-a-version"):
    ctx, _, _ = _run(STAMPED, project=_vendored_project(lock_version=v))
    check(f"adopter lock {v} vs 0.13.0 stays silent", "awow drift" not in ctx)

# Pre-stamp installed payload (no build.json): nothing to compare — silent
# even when the repo looks maximally drifty.
ctx, _, _ = _run(_plugin(payload_skill="PAYLOAD-SENTINEL"),
                 project=_vendored_project(maintainer=True, lock_version="0.7.0"))
check("unstamped installed payload stays silent", "awow drift" not in ctx)
```

- [ ] **Step 2: Run the tests to verify they fail correctly**

Run: `python3 tests/hooks/test_session_start.py`
Expected: the new drift checks print `FAIL` (positive checks — no warning is emitted yet); the negative "stays silent" checks print `PASS` (nothing warns today); every pre-existing check still `PASS`; exit 1. If anything errors instead of failing, fix the fixture and re-run.

- [ ] **Step 3: Implement the drift tier**

3a. In `hooks/session-start.py`, after `ENGINE_NUDGE` (~line 88), add the constants:

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

3b. After `spoke_context` (~line 198), add the pure functions:

```python
def read_stamp(root):
    """(version, digest) from <root>/.claude-plugin/build.json, or None when
    absent or unreadable. Payloads predating the stamp have no file; the
    caller treats None on the installed side as nothing-to-compare."""
    try:
        with open(os.path.join(root, ".claude-plugin", "build.json"),
                  encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    version = str(data.get("version", ""))
    digest = str(data.get("content", ""))
    if digest.startswith("sha256:"):
        digest = digest[len("sha256:"):]
    if not version or not digest:
        return None
    return version, digest


def stamp_display(stamp):
    return "%s+%s" % stamp


def lock_version(repo_dir):
    """awow_version from tools/awow.lock.json — the vintage a legacy vendored
    install recorded at setup; "" when absent or unreadable."""
    try:
        with open(os.path.join(repo_dir, "tools", "awow.lock.json"),
                  encoding="utf-8") as f:
            return str(json.load(f).get("awow_version", ""))
    except (OSError, ValueError):
        return ""


def semver_tuple(version):
    """Comparable tuple, or None for anything that is not digits-and-dots —
    an unparseable vintage must stay silent, never misreport drift."""
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return None


def vendored_drift_context(plugin_root, repo_dir):
    """Tier message when a vendored install's machinery vintage differs from
    the installed payload; None when aligned or undecidable (CAU-1338).

    Maintainer checkout first, keyed on .claude-plugin/plugin.json — the same
    gate gather.py builds behind. Its payload-to-payload compare must win over
    the lockfile branch: the maintainer repo also carries a stale legacy
    awow.lock.json, and routing it there would prescribe /migrate-to-plugin
    to the repo that builds the plugin. A maintainer checkout with no dist/
    stamp at all predates stamping and is behind every stamped payload by
    definition — the recorded incident shape."""
    installed = read_stamp(plugin_root)
    if installed is None:
        return None
    if os.path.isfile(os.path.join(repo_dir, ".claude-plugin", "plugin.json")):
        local = read_stamp(os.path.join(repo_dir, "dist"))
        if local is None:
            return VENDORED_DRIFT_MAINTAINER.format(
                repo_stamp="unstamped (predates build stamps)",
                installed_stamp=stamp_display(installed))
        if local != installed:
            return VENDORED_DRIFT_MAINTAINER.format(
                repo_stamp=stamp_display(local),
                installed_stamp=stamp_display(installed))
        return None
    vendored = lock_version(repo_dir)
    old, new = semver_tuple(vendored), semver_tuple(installed[0])
    if old is not None and new is not None and old < new:
        return VENDORED_DRIFT_ADOPTER.format(
            vendored=vendored, installed=stamp_display(installed))
    return None
```

3c. In `build_context` (~lines 213-231), insert the drift branch between the spoke branch and the setup nudge — the final `elif` keeps its exact behavior because `adopted` and the spoke tier are mutually exclusive (`spoke_context` returns None for adopted repos):

```python
    sections = [PREAMBLE, read_bootstrap(plugin_root)]
    if spoke is not None:
        sections.append(spoke)
    # Vendored install: warn when the machinery vintage this session will
    # read ({HUB}-first) differs from the installed payload (CAU-1338).
    elif adopted:
        drift = vendored_drift_context(plugin_root, repo_dir)
        if drift is not None:
            sections.append(drift)
    # One-time setup nudge: only a repo that is neither vendored nor a spoke,
    # and has not opted out. A connectable spoke gets its tier message instead.
    elif not os.path.isfile(
            os.path.join(repo_dir, ".awow", "no-setup-prompt")):
        sections.append(SETUP_NUDGE)
```

(The engine-nudge block below stays untouched.)

- [ ] **Step 4: Rebuild the payload and run the tests to verify they pass**

```bash
python tools/gather.py     # dist/hooks must be a verbatim copy; the dist stamp updates too
python3 tests/hooks/test_session_start.py
```

Expected: all `PASS` (new and pre-existing), exit 0. A failure on `dist/hooks/session-start.py matches` means the rebuild was skipped.

- [ ] **Step 5: Verify the adjacent suites still pass**

```bash
python tools/gather.py --check
python3 tests/hooks/test_lifecycle_seam_check.py
python3 tests/payload-manifests/test_build_stamp.py
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add hooks/session-start.py tests/hooks/test_session_start.py dist/
git commit -m "CAU-1338: session-start drift warning for vendored installs — maintainer checkouts compare their dist/ stamp against the installed payload (stale lockfile can never misroute them), legacy vendored adopters compare their lockfile vintage and are pointed at /migrate-to-plugin

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Document the precedence rule and its vintage consequence (AC2)

Documentation task — no TDD cycle (prose has no failing test; the mechanical guards are `gather.py --check`, the token lint, and the context-writes suite, run in Step 3).

**Files:**
- Modify: `context/tooling/context-resolution.md` (append a section after §The write boundary)
- Modify: `.agents/AGENTS.md` (one sentence at the end of §Reading machinery, line 27)
- Regenerate: `dist/` (the contract ships in the payload)

**Interfaces:**
- Consumes: the stamp semantics from Task 1 and the warning behavior from Task 2 (the text below names both — it must not land before they exist).

- [ ] **Step 1: Append the section to `context/tooling/context-resolution.md`**

After the §The write boundary section (end of file), add:

```markdown
## Machinery precedence and vintage

Machinery reads are `{HUB}`-first by design: a contract a team vendored **and deliberately edited** must keep winning over the shipped `{AWOW_ROOT}` default. The rule keys on file presence, so a vendored install runs whatever vintage the current checkout carries — a branch cut before an upstream change, or an install never updated, wins exactly like a customization, silently serving the older content.

Every built payload names its vintage in `.claude-plugin/build.json`: the canonical version plus a digest of the payload content, displayed `<version>+<digest>`, so two rebuilds of one version are distinguishable. At session start the drift check compares the installed payload's stamp against the checkout — the maintainer repo's `dist/` stamp, or a legacy vendored repo's `tools/awow.lock.json` vintage — and surfaces a one-line `awow drift:` warning naming both sides when they differ. `/migrate-to-plugin` retires a legacy vendored tree; in the maintainer repo, `python tools/gather.py && claude --plugin-dir dist` runs the checkout's own payload.
```

- [ ] **Step 2: Add the consequence sentence to `.agents/AGENTS.md`**

At the end of the §Reading machinery paragraph (line 27), directly after "…absent means absent, and commands branch on that.", append:

```markdown
The vintage consequence — a merely *old* vendored file wins exactly like an edited one — and the session-start drift warning that names it are specified in §Machinery precedence and vintage of the context-resolution contract.
```

- [ ] **Step 3: Rebuild and run the guards**

```bash
python tools/gather.py
python tools/gather.py --check
python tools/lint-paths.py
python3 tests/gather-tokens/test_tokens.py
python3 tests/context-writes/test_context_writes.py
grep -q "Machinery precedence and vintage" dist/context/tooling/context-resolution.md && echo SHIPPED
```

Expected: all green; `SHIPPED` prints (the section reaches the payload).

- [ ] **Step 4: Commit**

```bash
git add context/tooling/context-resolution.md .agents/AGENTS.md dist/
git commit -m "CAU-1338: document vendored-beats-payload and its branch-vintage consequence in the shipped context-resolution contract, with AGENTS.md pointing at it

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Full battery, proposal close-out, board, PR

**Files:**
- Modify: `proposals/CAU-1338.md` (status line + verification section)
- Commit (via `git add -f`, past `proposals/.gitignore`): `proposals/CAU-1338.md`, `proposals/vendored-drift-warning-design.md`, `proposals/plans/2026-08-25-vendored-drift-warning.md` — house practice per PR #77 (ships `proposals/CAU-1335.md`) and PR #71 (ships its proposal + design spec): the proposal set that a PR implements travels with the PR
- Board: CAU-1338 → In Progress with a root-cause comment (approval for this write is the user's approval of this plan; if that approval is in doubt, ask before touching the board)

- [ ] **Step 1: Run the full local CI battery**

```bash
python tools/gather.py --check && \
python tools/lint-paths.py && \
python3 tests/context-writes/test_context_writes.py && \
python3 tests/command-frontmatter/test_frontmatter.py && \
python3 tests/gather-tokens/test_tokens.py && \
python3 tests/payload-classification/test_classification.py && \
python3 tests/payload-manifests/test_manifest_integrity.py && \
python3 tests/payload-manifests/test_build_stamp.py && \
python3 tests/payload-commands/test_command_surface.py && \
python3 tests/payload-commands/test_migrate_surface.py && \
python3 tests/payload-commands/test_strategy_routing.py && \
python3 tests/telemetry-split/test_telemetry_split.py && \
python3 tests/telemetry-split/test_orphan_roots.py && \
python3 -m unittest discover -s tests/m365 && \
python3 -m unittest discover -s tests/department && \
python3 -m unittest discover -s tests/awow-lock && \
python3 tests/hooks/test_session_start.py && \
python3 tests/hooks/test_lifecycle_seam_check.py && \
python3 tests/hooks/test_wrong_root_guard.py && \
python3 tests/release/test_release_notes.py && \
python3 tools/release-notes.py --verify CHANGELOG.md && \
bash tests/harness/run-harness-tests.sh all && \
echo ALL-GREEN
```

Expected: `ALL-GREEN`. Any failure: stop, apply superpowers:systematic-debugging — no fix without the failing layer identified. (`test_wrong_root_guard.py` arrives with the CAU-1335 merge that Task 0 verified; its absence here means the branch was cut too early.)

- [ ] **Step 2: Update the proposal**

In `proposals/CAU-1338.md`: set the status line to `**Status:** APPROVED <date> — implemented; verification results recorded below` and append a `## Verification (<date>)` section recording the actual battery results, in the style of `proposals/CAU-1335.md`.

- [ ] **Step 3: Board update (gated)**

With the user's plan approval standing in as the awow gate: move CAU-1338 to In Progress and comment the root cause (three layers: intent-blind `{HUB}`-first precedence; no vendored-tier check in session-start; no comparable vintage marker — bare semver copied across rebuilds). Use the Linear MCP tools. If approval is in doubt, ask first.

- [ ] **Step 4: Commit the proposal set, push, and open the PR**

```bash
git add -f proposals/CAU-1338.md proposals/vendored-drift-warning-design.md \
  proposals/plans/2026-08-25-vendored-drift-warning.md
git commit -m "CAU-1338: proposal, design spec, and plan close-out

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git push -u origin arie/cau-1338-warn-when-a-vendored-installs-machinery-drifts-behind-the
gh pr create --title "CAU-1338: warn when a vendored install's machinery drifts behind the installed plugin payload" --body "$(cat <<'EOF'
A stale vendored file silently beats a newer plugin payload under the {HUB}-first rule (observed 2026-08-19: a pre-#62 branch rendered the old board-plan gate under an installed 0.9.2 payload). Three-layer fix per proposals/CAU-1338.md:

- **AC3** — every payload root carries a content-derived `.claude-plugin/build.json` (canonical version + sha256 digest of the planned stubs, deterministic, `--check`-safe), so two rebuilds of one version are distinguishable.
- **AC1** — the SessionStart hook grows a vendored drift tier mirroring the spoke tier: maintainer checkouts compare their `dist/` stamp against the installed payload (a stale legacy lockfile can never misroute them); legacy vendored adopters compare their lockfile vintage and are pointed at `/migrate-to-plugin`. One line, both directions, pre-stamp payloads degrade silent.
- **AC2** — §Machinery precedence and vintage lands in the shipped context-resolution contract; AGENTS.md §Reading machinery points at it.

Closes CAU-1338.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Notes for the executor

- **Known limitation (accepted in the spec):** a vendored adopter predating the lockfile gets no warning (`lock_version` returns `""` → silent). `/migrate-to-plugin`'s backfill is the route that gives such a repo a vintage.
- **Rollout behavior:** until the *installed* plugin cache updates to a stamped payload, `read_stamp(plugin_root)` is None and every session stays silent — detection goes live on the first cache sync after this ships. That is by design (graceful, no false alarms against pre-stamp installs).
- **Do not** add an opt-out file for the drift warning: it reports a live condition, same policy as `SPOKE_DRIFTED`.
- **Do not** bump the plugin version in this PR; releases are driven separately (version bump PRs own CHANGELOG.md sections).
