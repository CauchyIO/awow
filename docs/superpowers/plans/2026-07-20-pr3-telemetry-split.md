# PR 3 — Telemetry Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the five telemetry skills out of the base plugin into a second Claude Code plugin, `awow-telemetry@awow`, so the base plugin's resident skill surface is four behavioural skills rather than nine mostly-telemetry ones.

**Architecture:** Add a third `channel:` value — `telemetry` — alongside `vendored` and `bootstrap`. Build it into a second payload root, `dist-telemetry/`, declared as a second entry in the repo-root `.claude-plugin/marketplace.json`. Teach `find_orphans` that there are now two fully-generated roots, split `PLUGIN_TOOL_PATHS` so each plugin carries only its own runtime tooling, and repair the references across the repo that name a moving skill.

**Tech Stack:** Python 3.12 stdlib only (no pytest, no third-party). Bash for the harness suite. `tools/gather.py` is the build; `tools/lint-paths.py` is the token linter; `.github/workflows/ci.yml` runs both plus `tests/harness/run-harness-tests.sh all`.

**Spec:** `docs/superpowers/specs/2026-07-20-plugin-first-readme-design.md` §4.3, plus D2 and §8's channel note. This plan covers PR 3 of five.

**Assumes PRs 1 and 2 have landed.** §10 orders them ahead of this one, and both change the tree this plan measures and edits.

From **PR 1**: `{AWOW_ROOT}` exists in both substitution tables; `PAYLOAD_CONTEXT_PATHS`, `TEAM_DATA_CONTEXT_PATHS`, `classify_context_path`, and `unclassified_context_paths` exist in `tools/gather.py`, and `main()` carries the build guard that calls the last of those; `dist/context/` and `dist/.github/` ship; `tests/gather-tokens/` and `tests/payload-classification/` exist and run in CI; three dangling citations are gone from `.agents/commands/setup-awow.md`, which shifts every line number in that file. **`.agents/skills/using-awow/SKILL.md` already carries all three of its amendments — this PR must not edit that file.**

From **PR 2**: the shipped command surface is **sixteen**, not twenty — `test-setup-awow.md` is deleted from the repo, `update-awow` and `project-manager` are `channel: vendored`, and `daily-routine` and `weekly-digest` are merged into `daily-digest` and deleted. `tools/awow.lock.json` is regenerated. `.claude-plugin/plugin.json` is already at `0.6.0`.

Both facts bite. PR 1's line shifts are why Task 6 Step 4 anchors on literal text rather than a line number, and why Task 3 Step 6 must not replace the manifest guard by line address. PR 2's surface trim is why no step below asserts a bare file count — every count is derived from the source tree at the moment it runs.

## Global Constraints

- **Python 3.12, stdlib only.** No pytest, no network, no third-party. Tests are plain scripts run as `python3 tests/<dir>/test_<name>.py`, following `tests/awow-lock/test_awow_lock.py`. Every test module opens with a docstring ending in a `Run:` line.
- **Channel values, as they stand after PR 2 and before this PR's change:** `vendored` (excluded from the payload — PR 2 moved `update-awow` and `project-manager` into it), `bootstrap` (now `setup-awow.md` **only**, and it *does* ship), and the default. This PR adds a fourth, `telemetry`. Never write code that assumes a binary; `is_vendored_channel` is a predicate over one value, not a partition.
- **Never edit generated files.** `.claude/`, the `.github/` pointer stubs, `dist/`, `dist-telemetry/`, root `AGENTS.md`, `.claude/CLAUDE.md`, `.github/copilot-instructions.md` are all `gather.py` output. Edit the source under `.agents/` and re-run the gather. The repo-root `.claude-plugin/marketplace.json` is **not** generated — it is hand-maintained, and Task 4 edits it directly.
- **After any `.agents/` edit, run `python tools/gather.py`** and commit the regenerated surfaces alongside the source change, or `--check` fails in CI.
- **`tools/lint-paths.py` keeps its behaviour.** It skips only `vendored` and `bootstrap`; `telemetry` files stay linted, which is correct — they use `{AWOW_TOOLS}` and must keep doing so. Task 1 syncs its comments and adds a test that the two channel parsers agree, but changes no logic.
- **Commit message style:** max 2 sentences.
- **Do not create PRs and do not push.** This plan produces commits on the working branch only.

---

## The build directory: `dist-telemetry/` at the repo root

The spec (§4.3) states the constraint but leaves the directory unnamed. Resolved here, because every task below depends on it.

**Decision: `dist-telemetry/`, a sibling of `dist/` at the repo root.**

Verified against the four manifests and the publish script:

- Claude Code installs from `CauchyIO/awow` (spec §5.2: `/plugin marketplace add CauchyIO/awow`). It reads `.claude-plugin/marketplace.json` at the repo root, whose single entry is `"source": "./dist"` (`.claude-plugin/marketplace.json:9`) — a path relative to the cloned **awow** repo. A second entry resolving `"./dist-telemetry"` uses the identical mechanism, with no change to how installs work.
- `tools/sync-dist.sh:41` sets `DIST="$UPSTREAM/dist"`, and `:141` / `:157` rsync `"$DIST/"` into the destination root with `--delete`. A sibling directory is never seen by that script, so `dist-telemetry/` never publishes to `awow-dist`. For the base plugin that would be a defect. For `awow-telemetry` it is **the requirement**: §4.3 makes it Claude-Code-only, and `awow-dist` is exactly the Codex and Pi channel it must stay out of. The publish topology enforces the scope constraint mechanically, at no cost.
- The rejected alternative, `dist/telemetry/`, puts the second plugin *inside* plugin #1. `dist/.agents/plugins/marketplace.json` declares plugin #1 at `source.url = "./"`, so Codex clones the whole tree; `dist/package.json` declares `pi.skills: ["./agent-skills"]` beside it. Telemetry would then ship to Codex and Pi as dead weight nested in the base plugin — precisely the context tax D2 exists to remove.

**What `dist-telemetry/` contains, and what it deliberately does not:**

| Ships | Does not ship | Why not |
|---|---|---|
| `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` | Claude-Code-only (§4.3) |
| `README.md` | `package.json` | Claude-Code-only — no Pi manifest |
| `skills/<5 telemetry skills>/**` | `.agents/plugins/marketplace.json` | Claude-Code-only — no Codex marketplace |
| `tools/mlflow_reader.py` | `agent-skills/` | The Codex/Pi surface; telemetry is not on it |
| `tools/session_timeline.py` | `commands/` | Zero commands move; all sixteen stay in the base plugin |
| `tools/session_timeline_template.html` | `hooks/` | `hooks/hooks.json` registers a SessionStart that reads `${PLUGIN_ROOT}/.agents/skills/using-awow/SKILL.md`. `using-awow` stays in the base plugin, so a telemetry copy would emit `Error reading using-awow skill` on every session — and double-inject for anyone with both plugins installed |
| | `context/` | PR 1's payload machinery serves commands. No telemetry skill reads a `context/` contract |

**The soft-dependency question (§4.3, third bullet) — decided: accept it, vendor nothing.** Every dependency the telemetry skills *execute* — `mlflow_reader.py`, `session_timeline.py`, `session_timeline_template.html` — ships inside `dist-telemetry/tools/`, and Task 3's test asserts that in both directions. What remains are prose references to `/setup-awow` Step 8 (optional context-deepening, not an executable path) and `{AWOW_TOOLS}/gather.py`, which Task 1 removes because it is wrong in every plugin install, base or telemetry. Vendoring base content into the telemetry plugin to close a prose gap would duplicate files across two roots that then drift — the exact failure mode `--check` exists to prevent, reintroduced by hand.

---

### Task 1: The `telemetry` channel

**Files:**
- Modify: `tools/gather.py:424-427` (`is_vendored_channel`)
- Modify: `tools/lint-paths.py:14-25` (the sibling channel parser — comments only, no logic change) and `:35-38`
- Modify: `.agents/skills/mlflow-export/SKILL.md`, `.agents/skills/prompt-skill-analysis/SKILL.md`, `.agents/skills/project-timeline/SKILL.md`, `.agents/skills/awow-usage-coach/SKILL.md`, `.agents/skills/session-export/SKILL.md` (frontmatter)
- Modify: `.agents/skills/awow-usage-coach/SKILL.md:131` (the unshippable `{AWOW_TOOLS}/gather.py` reference)
- Create: `tests/telemetry-split/test_telemetry_split.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `declared_channel(text: str) -> str` in `tools/gather.py` — the `channel:` field from the leading frontmatter block, or `"both"` when absent. Return values in play: `"both"`, `"vendored"`, `"bootstrap"`, `"telemetry"`.
  - `is_vendored_channel(text: str) -> bool` — unchanged signature, reimplemented over `declared_channel`.
  - `is_telemetry_channel(text: str) -> bool` — `True` for the five moving skills.

  Tasks 2 and 3 consume all three.

**Why a `declared_channel` accessor rather than a second boolean:** `is_vendored_channel` is called at four sites (`plan_plugin:631`, `plan_plugin:639`, `skill_stubs:461` and `:478`, `command_skill_stub:500`). Adding a parallel `is_telemetry_channel` that re-parses the frontmatter would give two predicates with no shared notion of what the field's value space is — and `bootstrap` already proves the field is not binary. One accessor returning the value, two thin predicates over it, keeps the value space in one place.

- [ ] **Step 1: Write the failing test**

Create `tests/telemetry-split/test_telemetry_split.py`:

```python
"""Regression test for the telemetry channel split in tools/gather.py.

Design spec section 4.3: five skills (mlflow-export, prompt-skill-analysis,
project-timeline, awow-usage-coach, session-export) move out of the base plugin
into a second Claude-Code-only plugin built at dist-telemetry/. Four stay
(using-awow, board-aware-development, architecture-aware-development,
user-story-template).

Asserts, in order of how badly each would fail silently:

  1. Channel routing — every skill source declares the channel it should, and
     gather.py's parser agrees with tools/lint-paths.py's independent one on
     every file both scan. Two parsers, one answer.
  2. Placement, both directions — a telemetry skill is under dist-telemetry/
     and under NEITHER dist/skills/ nor dist/agent-skills/; a staying skill is
     the mirror image. A one-directional check passes a skill that shipped
     twice.
  3. Tool split — each plugin carries its own runtime tooling and only its own.
  4. Claude-Code-only — dist-telemetry/ has no Codex manifest, no Pi package,
     no agent-skills surface, and no hooks.
  5. Executable dependencies resolve — every {AWOW_TOOLS} path a telemetry
     skill body names is a file that ships in dist-telemetry/tools/.

Pure stdlib; no pytest, no network.

Run:  python3 tests/telemetry-split/test_telemetry_split.py
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

# tools/lint-paths.py cannot be imported by name — the hyphen is not a valid
# identifier — so load it from its path. Importing it at all is the point: the
# two channel parsers are independent implementations and must not drift.
_spec = importlib.util.spec_from_file_location(
    "lint_paths", REPO_ROOT / "tools" / "lint-paths.py"
)
lint_paths = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint_paths)

FAILURES = []

TELEMETRY_SKILLS = [
    "awow-usage-coach",
    "mlflow-export",
    "project-timeline",
    "prompt-skill-analysis",
    "session-export",
]
STAYING_SKILLS = [
    "architecture-aware-development",
    "board-aware-development",
    "using-awow",
]
# Declarative skills (a bare <name>.md, not a <name>/SKILL.md directory).
STAYING_DECLARATIVE = ["user-story-template"]
VENDORED_SKILLS = ["session-correlation"]
VENDORED_DECLARATIVE = ["agent-directive-voice"]

# The three runtime tools the telemetry skills execute. Kept literal so a new
# {AWOW_TOOLS} reference in a moving skill fails here and forces a decision
# about which plugin ships it, rather than dangling in a built payload.
TELEMETRY_TOOL_FILES = {
    "mlflow_reader.py",
    "session_timeline.py",
    "session_timeline_template.html",
}
BASE_TOOL_FILES = {"hooks/leak-patterns.txt", "hooks/pre-push"}


def skill_text(name: str) -> str:
    path = REPO_ROOT / ".agents" / "skills" / name / "SKILL.md"
    if not path.is_file():
        path = REPO_ROOT / ".agents" / "skills" / (name + ".md")
    return path.read_text()


def files_under(root: Path) -> set:
    if not root.is_dir():
        return set()
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def check_channels() -> None:
    expected = {}
    for n in TELEMETRY_SKILLS:
        expected[n] = "telemetry"
    for n in STAYING_SKILLS + STAYING_DECLARATIVE:
        expected[n] = "both"
    for n in VENDORED_SKILLS + VENDORED_DECLARATIVE:
        expected[n] = "vendored"
    for name, want in sorted(expected.items()):
        got = gather.declared_channel(skill_text(name))
        if got != want:
            FAILURES.append(f"declared_channel({name}) == {got!r}, expected {want!r}")

    # The two predicates must agree with the accessor, not re-derive it.
    for name in TELEMETRY_SKILLS:
        text = skill_text(name)
        if not gather.is_telemetry_channel(text):
            FAILURES.append(f"is_telemetry_channel({name}) is False")
        if gather.is_vendored_channel(text):
            FAILURES.append(f"is_vendored_channel({name}) is True — telemetry is not vendored")

    # gather.py and lint-paths.py parse `channel:` independently. Drift between
    # them silently changes which files get linted.
    for root in (REPO_ROOT / ".agents" / "commands", REPO_ROOT / ".agents" / "skills"):
        for path in sorted(root.rglob("*.md")):
            if path.name == "README.md":
                continue
            text = path.read_text()
            a, b = gather.declared_channel(text), lint_paths.channel(text)
            if a != b:
                rel = path.relative_to(REPO_ROOT)
                FAILURES.append(f"channel parsers disagree on {rel}: gather={a!r} lint={b!r}")


def main() -> int:
    check_channels()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Telemetry split OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note the module-level constants `TELEMETRY_TOOL_FILES`, `BASE_TOOL_FILES`, `files_under`, and `json` are unused in this step. Task 3 adds the checks that consume them; declaring them now keeps the file's shape stable across the two commits so the Task 3 diff is only new assertions.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/telemetry-split/test_telemetry_split.py`

Expected: FAIL with `AttributeError: module 'gather' has no attribute 'declared_channel'`.

- [ ] **Step 3: Add the channel accessor and predicates**

In `tools/gather.py`, replace lines 424-427:

```python
def is_vendored_channel(text: str) -> bool:
    """channel: vendored files operate on the vendored install itself and are
    excluded from the plugin payload."""
    return parse_frontmatter(text)[0].get("channel") == "vendored"
```

with:

```python
def declared_channel(text: str) -> str:
    """The `channel:` declared in the leading frontmatter, or 'both'.

    The field is NOT binary — four values are in play, and code that treats it
    as ships/doesn't-ship gets `bootstrap` wrong:

      both       (default)  ships in every payload
      vendored              operates on the vendored install itself; never ships
      bootstrap             ships, but *creates* the vendored tree, so its
                            literal paths are the deliverable (lint-paths.py:36-38)
      telemetry             ships in the awow-telemetry payload only, never in
                            the base plugin (design spec 4.3)

    tools/lint-paths.py carries an independent parser for the same field; the
    two are asserted equal on every source file in tests/telemetry-split/."""
    return parse_frontmatter(text)[0].get("channel", "both")


def is_vendored_channel(text: str) -> bool:
    """channel: vendored files operate on the vendored install itself and are
    excluded from every plugin payload."""
    return declared_channel(text) == "vendored"


def is_telemetry_channel(text: str) -> bool:
    """channel: telemetry files build into dist-telemetry/ (the awow-telemetry
    plugin) and are excluded from dist/ — both its Claude skills surface and
    its Codex/Pi agent-skills surface."""
    return declared_channel(text) == "telemetry"
```

- [ ] **Step 4: Sync the comments in `tools/lint-paths.py`**

No logic changes. `telemetry` files must stay linted — they use `{AWOW_TOOLS}` and the token must not rot into a bare path.

Replace `tools/lint-paths.py:17-18` (inside the `channel` docstring):

```python
    body line beginning `channel:` (e.g. prose documenting the field) is not
    mistaken for a declaration. Matches gather.is_vendored_channel."""
```

with:

```python
    body line beginning `channel:` (e.g. prose documenting the field) is not
    mistaken for a declaration. Independent reimplementation of
    gather.declared_channel; tests/telemetry-split/ asserts the two agree on
    every file both scan."""
```

Replace `tools/lint-paths.py:35-38`:

```python
            # vendored: operates on the vendored install, not shipped in the
            # plugin payload. bootstrap: shipped in the payload but *creates*
            # the vendored tree, so its literal paths are the deliverable.
            if channel(text) in ("vendored", "bootstrap"):
```

with:

```python
            # vendored: operates on the vendored install, not shipped in any
            # plugin payload. bootstrap: shipped in the payload but *creates*
            # the vendored tree, so its literal paths are the deliverable.
            # telemetry is NOT exempt — it ships (into dist-telemetry/) and its
            # bodies must keep using {AWOW_TOOLS} for the substitution to work.
            if channel(text) in ("vendored", "bootstrap"):
```

- [ ] **Step 5: Mark the five moving skills**

Add `channel: telemetry` as the last frontmatter line — immediately before the closing `---` — in each of these five files:

- `.agents/skills/mlflow-export/SKILL.md`
- `.agents/skills/prompt-skill-analysis/SKILL.md`
- `.agents/skills/project-timeline/SKILL.md`
- `.agents/skills/awow-usage-coach/SKILL.md`
- `.agents/skills/session-export/SKILL.md`

Each currently has a two-field block (`name:` then `description:`). The result in every file:

```yaml
---
name: <unchanged>
description: "<unchanged>"
channel: telemetry
---
```

This matches how `.agents/skills/session-correlation/SKILL.md:4` places `channel: vendored`. Change nothing else in the frontmatter — `parse_frontmatter` (`gather.py:159-170`) is line-based, and the `description:` values are long single-line double-quoted strings that must stay exactly as they are.

- [ ] **Step 6: Remove the unshippable `gather.py` reference**

`.agents/skills/awow-usage-coach/SKILL.md:131` renders in a plugin install as `${CLAUDE_PLUGIN_ROOT}/tools/gather.py` — a path that does not exist (`gather.py` is deliberately maintainer-only, per `gather.py:66-68`) and that points at the *plugin* rather than at the team's own repo, which is where the reader is being told to run it. The telemetry split makes it worse, not better: the line would now render against a second plugin root.

Replace line 131:

```markdown
10. **Distribution checklist** — three lines max: edit `.agents/AGENTS.md`, run `{AWOW_TOOLS}/gather.py`, do not hand-edit mirrored files.
```

with:

```markdown
10. **Distribution checklist** — three lines max: edit `.agents/AGENTS.md`, re-run the gather, do not hand-edit mirrored files.
```

Dropping the path is the fix, not a weakening: the line is advice the coaching *report* gives a team about their own repo, so any path awow substitutes at build time is the wrong one by construction.

- [ ] **Step 7: Run test to verify it passes, and confirm lint is unmoved**

```bash
python3 tests/telemetry-split/test_telemetry_split.py
python tools/lint-paths.py
```

Expected: `Telemetry split OK.` then `Path tokens clean.`

The build is now knowingly inconsistent — the five skills declare a channel nothing routes on yet, so they still land in `dist/`. Task 3 fixes that. Confirm the gather is unchanged so far:

```bash
python tools/gather.py --check
```

Expected: a list of `update:` lines for `.claude/skills/`, `.github/skills/`, `dist/skills/`, and `dist/agent-skills/` copies of the five skills (their frontmatter changed), and exit 1. This is expected: the sources changed and have not been re-gathered.

- [ ] **Step 8: Regenerate and commit**

```bash
python tools/gather.py
python tools/gather.py --check
```

Expected from the second: `All stubs in sync.`

```bash
git add tools/gather.py tools/lint-paths.py .agents/skills/ tests/telemetry-split/ .claude/ .github/ dist/
git commit -m "Add channel: telemetry as a fourth channel value behind one declared_channel accessor, and mark the five telemetry skills. Assert gather.py and lint-paths.py parse the field identically."
```

---

### Task 2: Orphan detection learns the second root

**Files:**
- Modify: `tools/gather.py:102` (add `DIST_TELEMETRY_DIR` beside `DIST_DIR`), `tools/gather.py:694-716` (`find_orphans`)
- Create: `tests/telemetry-split/test_orphan_roots.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces:
  - `DIST_TELEMETRY_DIR: Path` — `REPO_ROOT / "dist-telemetry"`.
  - `GENERATED_ROOTS: tuple[Path, ...]` — the payload roots under which every unplanned file is an orphan regardless of marker. Currently `(DIST_DIR, DIST_TELEMETRY_DIR)`.

  Task 3 consumes both.

**Why this task comes before the build.** `find_orphans:707` is `if surface == DIST_DIR` — an identity check against one specific path. A second root falls through to the `GENERATED_MARKER` branch, and full-copy payload content carries no marker: `plugin_command_copy:430`, `command_skill_stub:495`, and `skill_stubs:453` all emit source bodies verbatim. Verified empirically — `grep -c 'GENERATED by tools/gather.py' dist/commands/setup-awow.md` returns `0`, as does `dist/skills/mlflow-export/SKILL.md` and `dist/agent-skills/daily-digest/SKILL.md`. So a stale file left in `dist-telemetry/` after a skill is renamed or unmarked would be invisible to `--check`, never removed, and published to adopters. The build would look correct and CI would stay green. Land the detection before the thing it detects, or the window is never tested.

- [ ] **Step 1: Write the failing test**

Create `tests/telemetry-split/test_orphan_roots.py`:

```python
"""Regression test for orphan detection across BOTH generated payload roots.

find_orphans applies two different rules. Under a fully-generated payload root
every unplanned file is an orphan; everywhere else only files carrying the
GENERATED header are, so user-authored files are never deleted.

Before this test the rule was selected by `if surface == DIST_DIR` — an
identity check against one path. The second payload root, dist-telemetry/, fell
through to the marker branch, and full-copy payload content carries NO marker
(plugin_command_copy, command_skill_stub, and skill_stubs all emit source
bodies verbatim). A stale file there would therefore be undetected, never
removed, still published, and `gather.py --check` would stay green. That is a
silent-corruption failure with no visible symptom, which is why it gets its own
test rather than a line in the split suite.

Four assertions:
  1. Both payload roots are registered as fully generated.
  2. A markerless probe under dist-telemetry/ IS reported as an orphan.
  3. The same probe under .claude/ is NOT — the fully-generated rule stays
     scoped, so a user file outside the payload is still safe.
  4. Real payload content carries no marker, which is the premise that makes
     assertion 2 load-bearing rather than incidental.

Pure stdlib; no pytest, no network. Creates and removes one probe file under
each root; leaves no directory it did not find.

Run:  python3 tests/telemetry-split/test_orphan_roots.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

FAILURES = []

PROBE_BODY = (
    "---\nname: orphan-probe\ndescription: \"not a real skill\"\n---\n\n"
    "# orphan probe\n\nFull-copy payload shape: deliberately carries no "
    "GENERATED header, exactly like every real payload file.\n"
)


def make_probe(path: Path):
    """Create `path` and return the directories that had to be created, deepest
    first, so the caller can remove exactly what it added."""
    created = []
    d = path.parent
    while not d.exists():
        created.append(d)
        d = d.parent
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PROBE_BODY)
    return created


def remove_probe(path: Path, created) -> None:
    path.unlink(missing_ok=True)
    for d in created:
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()


def main() -> int:
    # 1. Both payload roots registered.
    roots = tuple(getattr(gather, "GENERATED_ROOTS", ()))
    for want in (gather.DIST_DIR, getattr(gather, "DIST_TELEMETRY_DIR", None)):
        if want is None or want not in roots:
            FAILURES.append(
                f"GENERATED_ROOTS is {[str(r) for r in roots]} — missing {want}. "
                "A payload root outside this set has its orphans silently ignored."
            )

    # 4. Premise: real payload content carries no marker.
    sample = gather.DIST_DIR / "commands" / "setup-awow.md"
    if sample.is_file() and gather.GENERATED_MARKER in sample.read_text():
        FAILURES.append(
            f"{sample} carries the GENERATED marker — the marker branch would "
            "have caught payload orphans after all, so this test's premise is stale."
        )

    # 2. Markerless probe under the telemetry payload root IS an orphan.
    tele_probe = getattr(gather, "DIST_TELEMETRY_DIR", REPO_ROOT / "dist-telemetry")
    tele_probe = tele_probe / "skills" / "_orphan-probe" / "SKILL.md"
    created = make_probe(tele_probe)
    try:
        if gather.GENERATED_MARKER in tele_probe.read_text():
            FAILURES.append("probe body accidentally contains the GENERATED marker")
        found = gather.find_orphans(set(), [tele_probe.parents[2]])
        if tele_probe not in found:
            FAILURES.append(
                f"{tele_probe.relative_to(REPO_ROOT)} was NOT reported as an orphan — "
                "dist-telemetry/ is not being treated as a fully generated root."
            )
    finally:
        remove_probe(tele_probe, created)

    # 3. The same probe under .claude/ is NOT an orphan.
    claude_probe = gather.CLAUDE_DIR / "skills" / "_orphan-probe" / "SKILL.md"
    created = make_probe(claude_probe)
    try:
        found = gather.find_orphans(set(), [gather.CLAUDE_DIR])
        if claude_probe in found:
            FAILURES.append(
                f"{claude_probe.relative_to(REPO_ROOT)} WAS reported as an orphan — "
                "the fully-generated rule leaked outside the payload roots, so a "
                "user-authored file under .claude/ would be deleted."
            )
    finally:
        remove_probe(claude_probe, created)

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Orphan detection covers both payload roots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/telemetry-split/test_orphan_roots.py`

Expected: FAIL, exit 1, with two failures — the missing constant and, critically, the undetected orphan:

```
FAIL GENERATED_ROOTS is [] — missing None. A payload root outside this set has its orphans silently ignored.
FAIL dist-telemetry/skills/_orphan-probe/SKILL.md was NOT reported as an orphan — dist-telemetry/ is not being treated as a fully generated root.

2 failure(s).
```

The second line is the whole reason this task exists. Confirm you see it before continuing.

- [ ] **Step 3: Add the second root and the roots tuple**

In `tools/gather.py`, replace line 102:

```python
DIST_DIR = REPO_ROOT / "dist"
```

with:

```python
DIST_DIR = REPO_ROOT / "dist"
# Second payload root: the awow-telemetry plugin (design spec 4.3). A sibling of
# dist/, not a child, for two reasons. Claude Code installs from CauchyIO/awow
# and resolves .claude-plugin/marketplace.json's relative `source` against the
# repo root, so "./dist-telemetry" needs no new install mechanism. And
# tools/sync-dist.sh mirrors only dist/ into awow-dist, so a sibling never
# reaches the Codex/Pi channel — which is exactly the Claude-Code-only scope
# constraint, enforced by the publish topology rather than by a rule someone
# has to remember.
DIST_TELEMETRY_DIR = REPO_ROOT / "dist-telemetry"
```

Then, immediately after `GENERATED_MARKER` (line 133 before this edit), add:

```python
# Payload roots that this script wholly owns: under one of these, EVERY
# unplanned file is an orphan, marker or not. That distinction is load-bearing,
# because full-copy payload content carries no GENERATED header at all —
# plugin_command_copy, command_skill_stub, and skill_stubs each emit the source
# body verbatim. A payload root missing from this tuple therefore has its
# orphans silently ignored while --check stays green. Add every new payload
# root here in the same change that creates it.
GENERATED_ROOTS = (DIST_DIR, DIST_TELEMETRY_DIR)
```

- [ ] **Step 4: Replace the identity check in `find_orphans`**

In `tools/gather.py`, replace lines 704-709:

```python
            # dist/ is wholly generated — every unplanned file there is an
            # orphan. Elsewhere only files carrying the GENERATED header are,
            # so user-added files are never deleted.
            if surface == DIST_DIR:
                orphans.append(path)
                continue
```

with:

```python
            # A payload root is wholly generated — every unplanned file there
            # is an orphan. Elsewhere only files carrying the GENERATED header
            # are, so user-added files are never deleted. Membership, not
            # identity: there is more than one payload root (GENERATED_ROOTS).
            if surface in GENERATED_ROOTS:
                orphans.append(path)
                continue
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 tests/telemetry-split/test_orphan_roots.py`

Expected: `Orphan detection covers both payload roots.` and exit 0.

- [ ] **Step 6: Confirm nothing was left behind and the build is clean**

```bash
test -e dist-telemetry && echo "LEFTOVER: dist-telemetry still exists" || echo "probe cleaned up"
test -e .claude/skills/_orphan-probe && echo "LEFTOVER: claude probe" || echo "claude probe cleaned up"
python tools/gather.py --check && python tools/lint-paths.py
```

Expected: `probe cleaned up`, `claude probe cleaned up`, `All stubs in sync.`, `Path tokens clean.`

- [ ] **Step 7: Commit**

```bash
git add tools/gather.py tests/telemetry-split/test_orphan_roots.py
git commit -m "Teach find_orphans that there is more than one wholly-generated payload root, replacing the dist/ identity check with GENERATED_ROOTS membership. Payload content carries no GENERATED marker, so a root outside that set has its orphans silently ignored."
```

---

### Task 3: Build `dist-telemetry/`

**Files:**
- Modify: `tools/gather.py:123-129` (`PLUGIN_TOOL_PATHS` split), `:453-457` (`skill_stubs`), `:599-652` (`plan_plugin`), `:516-538` (`plan_agent_skills`), `SURFACE_ROOTS`, `filter_surface`, the `--surface` choices, the manifest guard in `main()`, and the plan assembly; add `plan_telemetry`

  The five `main()`-neighbourhood regions are listed by name, not by line: PR 1 inserts its `unclassified_context_paths()` guard into `main()`, so every line number from `SURFACE_ROOTS` down has already shifted. Step 6 gives the literal old text for each.
- Modify: `tests/telemetry-split/test_telemetry_split.py` (add the placement, tool-split, isolation, and dependency assertions)
- Create (generated): `dist-telemetry/**`

**Interfaces:**
- Consumes: `declared_channel`, `is_telemetry_channel`, `is_vendored_channel` from Task 1; `DIST_TELEMETRY_DIR` and `GENERATED_ROOTS` from Task 2.
- Produces:
  - `TELEMETRY_TOOL_PATHS: list[str]` — repo-relative-to-`tools/` paths shipped in the telemetry payload.
  - `PLUGIN_TOOL_PATHS: list[str]` — same shape, base plugin only. Narrowed by this task.
  - `plan_telemetry() -> list[Stub]` — the whole `dist-telemetry/` tree.

  Task 4 consumes `plan_telemetry`'s manifest output for the version check.

- [ ] **Step 1: Write the failing assertions**

In `tests/telemetry-split/test_telemetry_split.py`, add these two functions immediately before `def main()`:

```python
def check_placement() -> None:
    dist_skills = files_under(gather.DIST_DIR / "skills")
    dist_agent = files_under(gather.DIST_DIR / "agent-skills")
    tele_skills = files_under(gather.DIST_TELEMETRY_DIR / "skills")

    def owns(files, name):
        return any(f.split("/")[0] == name for f in files)

    for name in TELEMETRY_SKILLS:
        if not owns(tele_skills, name):
            FAILURES.append(f"{name} is telemetry but absent from dist-telemetry/skills/")
        if owns(dist_skills, name):
            FAILURES.append(f"{name} is telemetry but still in dist/skills/ — it shipped twice")
        if owns(dist_agent, name):
            FAILURES.append(
                f"{name} is telemetry but still in dist/agent-skills/ — it reached "
                "Codex and Pi, which awow-telemetry does not target"
            )
    for name in STAYING_SKILLS + STAYING_DECLARATIVE:
        if not owns(dist_skills, name):
            FAILURES.append(f"{name} stays in the base plugin but is absent from dist/skills/")
        if owns(tele_skills, name):
            FAILURES.append(f"{name} stays in the base plugin but leaked into dist-telemetry/skills/")
    for name in VENDORED_SKILLS + VENDORED_DECLARATIVE:
        if owns(dist_skills, name) or owns(tele_skills, name):
            FAILURES.append(f"{name} is vendored and must ship in no payload")


def check_tools_and_isolation() -> None:
    base_tools = files_under(gather.DIST_DIR / "tools")
    tele_tools = files_under(gather.DIST_TELEMETRY_DIR / "tools")
    if base_tools != BASE_TOOL_FILES:
        FAILURES.append(f"dist/tools/ == {sorted(base_tools)}, expected {sorted(BASE_TOOL_FILES)}")
    if tele_tools != TELEMETRY_TOOL_FILES:
        FAILURES.append(
            f"dist-telemetry/tools/ == {sorted(tele_tools)}, expected {sorted(TELEMETRY_TOOL_FILES)}"
        )

    # Claude-Code-only (design spec 4.3): no Codex manifest, no Pi package, no
    # agent-skills surface, no hooks. The SessionStart hook reads using-awow,
    # which lives in the base plugin — a copy here would inject an error string
    # into every session and double-inject for anyone with both installed.
    for rel in (
        ".codex-plugin/plugin.json",
        "package.json",
        ".agents/plugins/marketplace.json",
        "agent-skills",
        "commands",
        "hooks",
        "context",
    ):
        if (gather.DIST_TELEMETRY_DIR / rel).exists():
            FAILURES.append(f"dist-telemetry/{rel} exists — awow-telemetry is Claude-Code-only")

    # Every {AWOW_TOOLS} path a telemetry skill names must ship beside it.
    import re
    pat = re.compile(r"\{AWOW_TOOLS\}/([A-Za-z0-9_.-]+)")
    for name in TELEMETRY_SKILLS:
        for ref in sorted(set(pat.findall(skill_text(name)))):
            if ref not in TELEMETRY_TOOL_FILES:
                FAILURES.append(
                    f"{name} references {{AWOW_TOOLS}}/{ref}, which dist-telemetry/tools/ "
                    "does not ship — add it to TELEMETRY_TOOL_PATHS or drop the reference"
                )
```

and register them in `main()` by replacing:

```python
def main() -> int:
    check_channels()
```

with:

```python
def main() -> int:
    check_channels()
    check_placement()
    check_tools_and_isolation()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/telemetry-split/test_telemetry_split.py`

Expected: FAIL with 20 failures — five `absent from dist-telemetry/skills/`, five `still in dist/skills/`, five `still in dist/agent-skills/`, and the two tool-directory mismatches, plus the `dist/tools/` set still holding all five entries. The exact count is not the assertion; every one of the three placement families must appear.

- [ ] **Step 3: Split the tool paths**

In `tools/gather.py`, replace lines 120-129:

```python
# Runtime tools shipped in the plugin payload. Everything else under tools/
# stays maintainer-only: those scripts resolve REPO_ROOT from __file__ and
# would operate on the plugin install dir if shipped (hub-and-spoke WI-4).
PLUGIN_TOOL_PATHS = [
    "mlflow_reader.py",
    "session_timeline.py",
    "session_timeline_template.html",
    "hooks/leak-patterns.txt",
    "hooks/pre-push",
]
```

with:

```python
# Runtime tools shipped in a plugin payload, split by which plugin needs them.
# Everything else under tools/ stays maintainer-only: those scripts resolve
# REPO_ROOT from __file__ and would operate on the plugin install dir if
# shipped (hub-and-spoke WI-4).
#
# Base plugin: the pre-push leak scan and its pattern file. Nothing else — the
# three session-analysis tools below served only skills that have moved.
PLUGIN_TOOL_PATHS = [
    "hooks/leak-patterns.txt",
    "hooks/pre-push",
]

# awow-telemetry: the session-analysis runtime. project-timeline has no
# scripts/ directory of its own — session_timeline.py plus its HTML template
# ARE its implementation, reached as {AWOW_TOOLS}/… from the skill body. And
# mlflow_reader.py is shared: awow-usage-coach's bundled awow_extract.py
# imports it (scripts/awow_extract.py:52-61), so the two must land in the same
# payload or that import fails at runtime.
TELEMETRY_TOOL_PATHS = [
    "mlflow_reader.py",
    "session_timeline.py",
    "session_timeline_template.html",
]
```

- [ ] **Step 4: Exclude telemetry from the base plugin's two skill surfaces**

Both surfaces route through `skill_stubs`, which already returns `[]` for vendored entries. Extend that filter rather than adding a check at each call site — the base plugin has two callers (`plan_plugin:645`, `plan_agent_skills:537`) and `plan_telemetry` will be a third that must invert the rule.

In `tools/gather.py`, replace the signature and docstring of `skill_stubs` (lines 453-457):

```python
def skill_stubs(entry: Path, dest_root: Path, render=render_plugin_body) -> list[Stub]:
    """Render one `.agents/skills/<entry>` into `dest_root/<name>/…` as full-content
    SKILL.md (+ any bundled files). Shared by the Claude plugin payload (dist/skills)
    and the commands-as-skills surface (dist/agent-skills, which passes
    render_agent_skills_body). Returns [] for vendored or non-skill entries."""
```

with:

```python
def skill_stubs(
    entry: Path, dest_root: Path, render=render_plugin_body, channel: str = "both"
) -> list[Stub]:
    """Render one `.agents/skills/<entry>` into `dest_root/<name>/…` as full-content
    SKILL.md (+ any bundled files). Shared by the Claude plugin payload (dist/skills),
    the commands-as-skills surface (dist/agent-skills, which passes
    render_agent_skills_body), and the telemetry payload (dist-telemetry/skills).

    `channel` selects which payload is being built: 'both' takes everything that
    is not vendored and not telemetry; 'telemetry' takes exactly the telemetry
    entries. Returns [] for vendored or non-skill entries either way."""
```

Then replace the two vendored guards inside it. Line 461-462:

```python
        if is_vendored_channel(skill_text):
            return []
```

becomes:

```python
        if is_vendored_channel(skill_text):
            return []
        if is_telemetry_channel(skill_text) != (channel == "telemetry"):
            return []
```

and line 477-478:

```python
        text = entry.read_text()
        if is_vendored_channel(text):
            return []
```

becomes:

```python
        text = entry.read_text()
        if is_vendored_channel(text):
            return []
        if is_telemetry_channel(text) != (channel == "telemetry"):
            return []
```

The `!=` is deliberate and covers both directions in one line: a telemetry entry is dropped from a base build, and a non-telemetry entry is dropped from the telemetry build. Writing it as two separate `if channel == …` branches invites the second one being forgotten, which is how `mlflow-export` would ship twice.

No changes are needed at `plan_plugin:645` or `plan_agent_skills:537` — both call `skill_stubs` with the default `channel="both"`.

**Commands are untouched.** Zero commands move (§4.3 moves skills only), so `plan_plugin`'s command loops at `:626-640` and `plan_agent_skills`'s at `:521-533` keep their `is_vendored_channel` filter unchanged.

- [ ] **Step 5: Add `plan_telemetry`**

In `tools/gather.py`, insert immediately after `plan_pi()` ends (line 596) and before `def plan_plugin()`:

```python
def plan_telemetry() -> list[Stub]:
    """dist-telemetry/ — the awow-telemetry plugin payload (design spec 4.3).

    Claude Code only, this release. Deliberately absent: the Codex manifest,
    the Pi package.json, the agent-skills surface, and hooks/. The SessionStart
    hook reads ${PLUGIN_ROOT}/.agents/skills/using-awow/SKILL.md, and using-awow
    stays in the base plugin — a copy of hooks/ here would emit the error string
    into every session, and double-inject for anyone running both plugins.

    Name, description, and version derive from the one canonical
    .claude-plugin/plugin.json, exactly as plan_codex and plan_pi do, so the two
    plugins version in lockstep with no second file to keep in sync."""
    src = json.loads(PLUGIN_MANIFEST.read_text())
    manifest = {
        "name": "awow-telemetry",
        "displayName": "awow-telemetry — the evidence layer",
        "description": (
            "Session analysis for awow: export agent traces, build a visual "
            "project timeline, score prompt craft, and coach a team or an "
            "individual off what the sessions actually show. Installs beside "
            "awow@awow; neither requires the other."
        ),
        "version": src["version"],
        "author": src.get("author", {"name": "awow maintainers"}),
        "license": src.get("license", "MIT"),
        "homepage": src.get("homepage"),
        "repository": src.get("repository"),
    }
    plans = [
        Stub(
            DIST_TELEMETRY_DIR / ".claude-plugin" / "plugin.json",
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        ),
        Stub(
            DIST_TELEMETRY_DIR / "README.md",
            f"{GENERATED_MARKER} — DO NOT EDIT. -->\n\n"
            "# dist-telemetry/ — built awow-telemetry plugin payload\n\n"
            "This directory is the installable `awow-telemetry` Claude Code "
            "plugin, built by `python tools/gather.py --surface telemetry` from "
            "the `channel: telemetry` skills under `.agents/skills/` plus a "
            "runtime slice of `tools/`. The repo-root "
            "`.claude-plugin/marketplace.json` points installers here as the "
            "second entry, so `/plugin install awow-telemetry@awow` resolves.\n\n"
            "**Claude Code only this release.** `tools/sync-dist.sh` mirrors "
            "only `dist/` into `awow-dist`, which is the Codex and Pi install "
            "source — so nothing here reaches those harnesses. That is the "
            "intended scope, not an omission.\n\n"
            "Do not edit files in this directory — edit the source and re-run "
            "the gather. Any file here that the build did not plan is deleted "
            "on the next run.\n",
        ),
    ]
    for entry in sorted((AGENTS_DIR / "skills").iterdir()):
        if entry.name in SKIP_FILENAMES:
            continue
        plans.extend(
            skill_stubs(entry, DIST_TELEMETRY_DIR / "skills", channel="telemetry")
        )
    for rel in TELEMETRY_TOOL_PATHS:
        plans.append(copy_stub(DIST_TELEMETRY_DIR / "tools" / rel, REPO_ROOT / "tools" / rel))
    return plans
```

- [ ] **Step 6: Wire the surface**

Five edits in `tools/gather.py`, all needed together — leaving any one out either drops the plans or scans a root nothing plans into, and the second failure mode deletes the payload it just built.

**Match on the literal old text below, not on the line numbers.** PR 1 inserts its `unclassified_context_paths()` build guard into `main()`, so every line number in this neighbourhood has already moved by the time this step runs. The line numbers given are pre-PR-1 orientation only.

Replace `SURFACE_ROOTS` — old text:

```python
SURFACE_ROOTS = {
    "claude": [CLAUDE_DIR],
    "github": [GITHUB_DIR],
    "plugin": [DIST_DIR],
    "both": [CLAUDE_DIR, GITHUB_DIR],
    "all": [CLAUDE_DIR, GITHUB_DIR, DIST_DIR],
}
```

with:

```python
SURFACE_ROOTS = {
    "claude": [CLAUDE_DIR],
    "github": [GITHUB_DIR],
    "plugin": [DIST_DIR],
    "telemetry": [DIST_TELEMETRY_DIR],
    "both": [CLAUDE_DIR, GITHUB_DIR],
    "all": [CLAUDE_DIR, GITHUB_DIR, DIST_DIR, DIST_TELEMETRY_DIR],
}
```

`plugin` stays `dist/` alone. `tools/sync-dist.sh` and the harness suites reason about `--surface plugin` meaning the published payload, and widening it would silently change what those checks cover.

Replace `filter_surface`'s repo-root branch — old text:

```python
        if p.target.parent == REPO_ROOT:
            # Repo-root instruction files (AGENTS.md) are harness-neutral: they
            # belong to every in-repo surface but never to the dist/ payload,
            # which owns only its own tree.
            if surface != "plugin":
                kept.append(p)
```

with:

```python
        if p.target.parent == REPO_ROOT:
            # Repo-root instruction files (AGENTS.md) are harness-neutral: they
            # belong to every in-repo surface but never to a payload root,
            # which owns only its own tree.
            if surface not in ("plugin", "telemetry"):
                kept.append(p)
```

Replace the `--surface` choices — old text:

```python
    parser.add_argument(
        "--surface", choices=["claude", "github", "plugin", "both", "all"], default="all"
    )
```

with:

```python
    parser.add_argument(
        "--surface",
        choices=["claude", "github", "plugin", "telemetry", "both", "all"],
        default="all",
    )
```

Next, the manifest guard — **the one edit here that can silently destroy someone else's work.** PR 1 Task 2 Step 5 inserts a build guard into this same `main()`, a few lines above, immediately after `args = parser.parse_args()`:

```python
    stray = unclassified_context_paths()
    if stray:
        print(
            "Unclassified path(s) under context/. Add each to "
            ...
        return 1
```

That guard **must survive this edit.** Match exactly the block quoted below — start at `surfaces = list(SURFACE_ROOTS[args.surface])`, end at the `print(f"note: …plugin surface skipped")` line — and touch nothing above it. A line-addressed wholesale replacement of the old `:734-743` would now straddle PR 1's guard and delete it, and nothing downstream would notice: the payload-classification test asserts the *function* is correct, not that `main()` still calls it, so `--check`, CI, and every test in this plan would stay green with the build guard gone.

Old text:

```python
    surfaces = list(SURFACE_ROOTS[args.surface])
    if DIST_DIR in surfaces and not PLUGIN_MANIFEST.exists():
        # Vendored adopter repos have no plugin manifest and no payload to
        # build; only the maintainer repo carries .claude-plugin/plugin.json.
        if args.surface == "plugin":
            print(f"error: {PLUGIN_MANIFEST} does not exist — not the awow "
                  f"maintainer repo, nothing to build", file=sys.stderr)
            return 1
        surfaces.remove(DIST_DIR)
        print(f"note: {PLUGIN_MANIFEST.relative_to(REPO_ROOT)} not found — plugin surface skipped")
```

with:

```python
    surfaces = list(SURFACE_ROOTS[args.surface])
    payload_roots = [r for r in (DIST_DIR, DIST_TELEMETRY_DIR) if r in surfaces]
    if payload_roots and not PLUGIN_MANIFEST.exists():
        # Vendored adopter repos have no plugin manifest and no payload to
        # build; only the maintainer repo carries .claude-plugin/plugin.json.
        # Both payload roots derive their manifests from it.
        if args.surface in ("plugin", "telemetry"):
            print(f"error: {PLUGIN_MANIFEST} does not exist — not the awow "
                  f"maintainer repo, nothing to build", file=sys.stderr)
            return 1
        for root in payload_roots:
            surfaces.remove(root)
        print(f"note: {PLUGIN_MANIFEST.relative_to(REPO_ROOT)} not found — payload surfaces skipped")
```

Replace the plan assembly — old text:

```python
    if DIST_DIR in surfaces:
        plans += plan_plugin()
        plans += plan_agent_skills()
        plans += plan_codex()
        plans += plan_pi()
```

with:

```python
    if DIST_DIR in surfaces:
        plans += plan_plugin()
        plans += plan_agent_skills()
        plans += plan_codex()
        plans += plan_pi()
    if DIST_TELEMETRY_DIR in surfaces:
        plans += plan_telemetry()
```

Before moving on, confirm PR 1's build guard is still wired in and still fires:

```bash
grep -n "unclassified_context_paths()" tools/gather.py
touch context/tooling/unclassified-probe.md
python tools/gather.py --check; echo "exit=$?"
rm context/tooling/unclassified-probe.md
```

Expected: **two** hits from the grep — the `def` and the call inside `main()`. Then, from `--check`, the guard's `Unclassified path(s) under context/` message naming `context/tooling/unclassified-probe.md`, and `exit=1`.

Read that output, not just the exit code. `dist-telemetry/` has not been built yet at this point, so `--check` would exit 1 either way; what distinguishes a live guard is that it returns *before* the plan is built, so the guard message is the **only** output. A wall of `update:` lines instead means the guard was deleted — one grep hit, definition surviving without its call site, which is exactly the failure this check exists to catch. Restore it from PR 1 Task 2 Step 5 before continuing.

- [ ] **Step 7: Build and verify placement in both directions**

```bash
python tools/gather.py
python3 tests/telemetry-split/test_telemetry_split.py
python3 tests/telemetry-split/test_orphan_roots.py
```

Expected: `Telemetry split OK.` then `Orphan detection covers both payload roots.`

Now check placement against the **sources**, not against a remembered number. Each surface's expected membership is computed from `.agents/` plus the two constants in `gather.py`, so the check stays true whatever else has landed on the branch:

```bash
python3 - <<'PY'
import pathlib, sys
sys.path.insert(0, "tools")
import gather

R = pathlib.Path(".")

def channel(p):
    lines = p.read_text().split("\n")
    if not lines or lines[0].strip() != "---":
        return "both"
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("channel:"):
            return line.split(":", 1)[1].strip()
    return "both"

# Command sources: .agents/commands/**.md plus the legacy root commands/,
# minus READMEs, minus the archetype directory, minus vendored.
cmd_srcs = [p for p in (R / ".agents/commands").rglob("*.md")
            if p.name != "README.md" and "_workitem-archetypes" not in p.parts]
cmd_srcs += [p for p in (R / "commands").glob("*.md") if p.name != "README.md"]
want_cmds = {p.name for p in cmd_srcs if channel(p) != "vendored"}

# Skill sources: a <name>/SKILL.md directory or a bare <name>.md.
skills = [e for e in (R / ".agents/skills").iterdir() if e.name != "README.md"]
def sname(e): return e.name[:-3] if e.suffix == ".md" else e.name
def schan(e): return channel((e / "SKILL.md") if e.is_dir() else e)
want_base = {sname(e) for e in skills if schan(e) not in ("vendored", "telemetry")}
want_tele = {sname(e) for e in skills if schan(e) == "telemetry"}

def listing(d):
    d = R / d
    return {p.name for p in d.iterdir()} if d.is_dir() else set()

def report(label, want, got):
    if want == got:
        print(f"{label} OK ({len(want)})")
    else:
        print(f"{label} MISMATCH: missing={sorted(want - got)} unexpected={sorted(got - want)}")

report("commands", want_cmds, {p.name for p in (R / "dist/commands").glob("*.md")})
report("dist/skills", want_base, listing("dist/skills"))
# agent-skills renders commands AND skills as <name>/SKILL.md.
report("agent-skills", want_base | {n[:-3] for n in want_cmds}, listing("dist/agent-skills"))
report("dist-telemetry/skills", want_tele, listing("dist-telemetry/skills"))
report("dist/tools", set(gather.PLUGIN_TOOL_PATHS),
       {p.relative_to(R / "dist/tools").as_posix() for p in (R / "dist/tools").rglob("*") if p.is_file()})
report("dist-telemetry/tools", set(gather.TELEMETRY_TOOL_PATHS),
       {p.relative_to(R / "dist-telemetry/tools").as_posix()
        for p in (R / "dist-telemetry/tools").rglob("*") if p.is_file()})

# Whole-tree totals, derived from the build plan rather than remembered.
for root, plans in (
    ("dist", gather.plan_plugin() + gather.plan_agent_skills() + gather.plan_codex() + gather.plan_pi()),
    ("dist-telemetry", gather.plan_telemetry()),
):
    planned = {p.target for p in plans}
    actual = {p for p in (R / root).rglob("*") if p.is_file()}
    print(f"{root} tree {'OK' if len(planned) == len(actual) else 'MISMATCH'} "
          f"(planned {len(planned)}, actual {len(actual)})")
PY
```

Expected:

```
commands OK (16)
dist/skills OK (4)
agent-skills OK (20)
dist-telemetry/skills OK (5)
dist/tools OK (2)
dist-telemetry/tools OK (3)
dist tree OK (planned N, actual N)
dist-telemetry tree OK (planned 14, actual 14)
```

`dist`'s total is left as `N` deliberately: PR 1 adds `dist/context/` and `dist/.github/prompts/` to that tree, and this plan has no business asserting how many files those contain. What matters is that the two numbers on the line agree.

The numbers are context, not the assertion — the script derives every one of them and prints `MISMATCH` with the offending names if the build disagrees. Read them as a sanity check on the shape: `dist/skills` drops from nine to the four staying skills; `agent-skills` is PR 2's sixteen commands plus those four; `dist/tools` keeps only the two `hooks/` files; `dist-telemetry` is 1 manifest + 1 README + 9 skill files + 3 tools. `dist/commands` is untouched by *this* PR — it is sixteen because PR 2 made it sixteen, and the check derives that rather than asserting it.

The `tree` lines are a weaker claim than the rest — they compare cardinality only. `python tools/gather.py --check` is the real guarantee that each tree contains exactly its planned targets; these lines just surface the totals while you are already looking.

- [ ] **Step 8: Verify the second root is genuinely orphan-managed**

The point of Task 2, exercised against a real build rather than a probe:

```bash
echo "stale" > dist-telemetry/skills/mlflow-export/STALE.md
python tools/gather.py --check; echo "exit=$?"
```

Expected: a line `orphan: dist-telemetry/skills/mlflow-export/STALE.md`, a summary naming 1 orphan, and `exit=1`.

```bash
python tools/gather.py
test -e dist-telemetry/skills/mlflow-export/STALE.md && echo "STILL THERE" || echo "orphan removed"
python tools/gather.py --check
```

Expected: `removed orphan: dist-telemetry/skills/mlflow-export/STALE.md`, then `orphan removed`, then `All stubs in sync.`

- [ ] **Step 9: Verify each surface flag independently**

```bash
python tools/gather.py --surface telemetry --check
python tools/gather.py --surface plugin --check
python tools/gather.py --surface claude --check
python tools/gather.py --check
python tools/lint-paths.py
```

Expected: `All stubs in sync.` five times, then `Path tokens clean.` If `--surface plugin` reports orphans under `dist-telemetry/`, `SURFACE_ROOTS["plugin"]` was widened — revert it to `[DIST_DIR]`.

- [ ] **Step 10: Verify the harness suite and PR 1's tests still pass**

```bash
bash tests/harness/run-harness-tests.sh all
python3 tests/payload-classification/test_classification.py
python3 tests/gather-tokens/test_tokens.py
```

Expected: `all checks passed`, `Payload classification OK.`, `Path-token substitution OK.`

`tests/harness/codex/wiring.sh:14` asserts `dist/.codex-plugin/plugin.json` still points `skills` at `./agent-skills/`, and `tests/harness/pi/wiring.sh:16` asserts `dist/package.json` still registers `./agent-skills`. Both stay true — that directory is unchanged in name and simply carries five fewer skills.

- [ ] **Step 11: Commit**

```bash
git add tools/gather.py tests/telemetry-split/ dist/ dist-telemetry/
git commit -m "Build the five telemetry skills into a second payload root, dist-telemetry/, and split PLUGIN_TOOL_PATHS so each plugin ships only its own runtime tooling. Assert placement in both directions so a skill cannot ship twice."
```

---

### Task 4: The second marketplace entry and the version bump

**Files:**
- Modify: `.claude-plugin/marketplace.json` (hand-maintained, not generated)
- Modify: `.claude-plugin/plugin.json:5` (version)
- Modify: `tests/telemetry-split/test_telemetry_split.py` (marketplace assertions)

**Interfaces:**
- Consumes: `plan_telemetry` from Task 3 (its manifest is what the version check compares against).
- Produces: no new symbols. `/plugin install awow-telemetry@awow` becomes resolvable, which PR 4's README documents.

**On the version.** §8 requires `0.6.0` minimum, and names two independent causes: four commands leaving `dist/commands/` (PR 2) and a second plugin shipping (this PR). Whichever lands second finds it already done. Step 2 below states both branches explicitly so the implementer does not need to guess which PR is ahead.

- [ ] **Step 1: Write the failing assertions**

In `tests/telemetry-split/test_telemetry_split.py`, add this function immediately before `def main()`:

```python
def check_marketplace() -> None:
    mk = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    entries = {p["name"]: p for p in mk.get("plugins", [])}
    if set(entries) != {"awow", "awow-telemetry"}:
        FAILURES.append(
            f"marketplace declares {sorted(entries)}, expected ['awow', 'awow-telemetry']"
        )
        return
    for name, want_source in (("awow", "./dist"), ("awow-telemetry", "./dist-telemetry")):
        got = entries[name].get("source")
        if got != want_source:
            FAILURES.append(f"marketplace entry {name} source == {got!r}, expected {want_source!r}")
        # A source that resolves to nothing is an install failure with no build error.
        target = REPO_ROOT / want_source
        if not (target / ".claude-plugin" / "plugin.json").is_file():
            FAILURES.append(f"{want_source}/.claude-plugin/plugin.json is missing — {name} cannot install")

    # Lockstep (design spec 8): awow-telemetry versions with awow this release.
    canonical = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
    for rel in (
        "dist/.claude-plugin/plugin.json",
        "dist-telemetry/.claude-plugin/plugin.json",
        "dist/.codex-plugin/plugin.json",
        "dist/package.json",
    ):
        built = json.loads((REPO_ROOT / rel).read_text())["version"]
        if built != canonical:
            FAILURES.append(f"{rel} version {built!r} != canonical {canonical!r}")
    if tuple(int(x) for x in canonical.split(".")) < (0, 6, 0):
        FAILURES.append(
            f"version is {canonical} — a second plugin ships this release, so "
            "design spec section 8 requires 0.6.0 minimum"
        )
```

and register it in `main()` by replacing:

```python
    check_tools_and_isolation()
```

with:

```python
    check_tools_and_isolation()
    check_marketplace()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/telemetry-split/test_telemetry_split.py`

Expected: FAIL with

```
FAIL marketplace declares ['awow'], expected ['awow', 'awow-telemetry']
```

- [ ] **Step 3: Add the second marketplace entry**

Replace the whole of `.claude-plugin/marketplace.json`:

```json
{
  "name": "awow",
  "owner": {
    "name": "awow maintainers"
  },
  "plugins": [
    {
      "name": "awow",
      "source": "./dist",
      "description": "Bring the Agentic Way of Working to any repo — brand-new or already full of code. /awowify adds the files an AI coding agent needs and walks you through connecting your issue board and conventions, without changing anything you've already built."
    },
    {
      "name": "awow-telemetry",
      "source": "./dist-telemetry",
      "description": "The evidence layer for awow. Export your agent sessions, build a visual timeline of how a project actually got built, score prompt craft, and coach a team or an individual off what the sessions show. Installs beside awow; neither requires the other."
    }
  ]
}
```

The `source` values are paths relative to the cloned `CauchyIO/awow` repo, which is why `dist-telemetry/` sits at the repo root — see the build-directory section above. This file is not generated; `gather.py` writes `dist/.claude-plugin/plugin.json` and `dist/.agents/plugins/marketplace.json` but never this one.

- [ ] **Step 4: Set the version**

Read the current value:

```bash
python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])"
```

- If it prints `0.6.0`, PR 2 already bumped it. Change nothing and go to Step 5.
- If it prints `0.5.0` (the value on `main`), edit `.claude-plugin/plugin.json:5` from `"version": "0.5.0",` to `"version": "0.6.0",`.

Everything downstream derives from this one field — `plan_plugin:601`, `plan_codex:547`, `plan_pi:585`, and Task 3's `plan_telemetry` all read `PLUGIN_MANIFEST`, so there is no second place to edit and the harness suites' lockstep assertions (`tests/harness/codex/wiring.sh:27-31`, `tests/harness/pi/wiring.sh:27-31`) hold automatically.

- [ ] **Step 5: Regenerate and verify**

```bash
python tools/gather.py
python3 tests/telemetry-split/test_telemetry_split.py
python tools/gather.py --check
bash tests/harness/run-harness-tests.sh all
```

Expected: `Telemetry split OK.`, `All stubs in sync.`, `all checks passed`.

```bash
python3 -c "
import json
for f in ['.claude-plugin/plugin.json','dist/.claude-plugin/plugin.json','dist-telemetry/.claude-plugin/plugin.json','dist/.codex-plugin/plugin.json','dist/package.json']:
    d = json.load(open(f)); print(f\"{d['version']}  {d['name']}  {f}\")
"
```

Expected:

```
0.6.0  awow  .claude-plugin/plugin.json
0.6.0  awow  dist/.claude-plugin/plugin.json
0.6.0  awow-telemetry  dist-telemetry/.claude-plugin/plugin.json
0.6.0  awow  dist/.codex-plugin/plugin.json
0.6.0  awow  dist/package.json
```

Note the telemetry manifest is the only one whose `name` differs — that is what makes `awow-telemetry@awow` a distinct install.

- [ ] **Step 6: Commit**

```bash
git add .claude-plugin/ tests/telemetry-split/ dist/ dist-telemetry/
git commit -m "Declare awow-telemetry as a second marketplace entry sourced from ./dist-telemetry, and take the version to 0.6.0 for the second shipped plugin. Both manifests derive from the one canonical plugin.json, so they version in lockstep."
```

---

### Task 5: `awow_extract.py` — two layouts, and a command that no longer exists

**Files:**
- Modify: `.agents/skills/awow-usage-coach/scripts/awow_extract.py:52-61` (the `mlflow_reader` import) and `:69-80` (`KNOWN_COMMANDS`)

**Interfaces:**
- Consumes: Task 3's `dist-telemetry/tools/mlflow_reader.py`.
- Produces: no new symbols. Closes the one runtime dependency the split could break silently.

**The two defects, both verified by reading the file:**

1. `:55` is `sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))`. From `.agents/skills/awow-usage-coach/scripts/awow_extract.py` the parents are `scripts` → `awow-usage-coach` → `skills` → `.agents` → **repo root**, so `parents[4]/tools` is correct in this repo. In the built payload the file lands at `dist-telemetry/skills/awow-usage-coach/scripts/awow_extract.py`: `scripts` → `awow-usage-coach` → `skills` → **plugin root** → the directory *above* the plugin. `parents[4]/tools` therefore resolves outside the install and the import fails. §9's human checklist item *"Live install of awow-telemetry@awow resolves its tooling"* is unreachable until this is fixed.
2. `:78` is `"weekly-digest": "standardise"` inside `KNOWN_COMMANDS`. PR 2 removes `/weekly-digest` outright with no alias (§4.4, §12). A moving skill would keep naming a deleted command, and the "coverage" report the dict feeds would list a command that cannot be invoked.

**No silent fallback.** The import tries a named list of candidate layouts and, if none holds, raises `SystemExit` naming every path it looked in. That is the existing behaviour's shape (`:56-61` already raises `SystemExit` on `ImportError`), made accurate about where the file can legitimately live.

- [ ] **Step 1: Fix the import to cover both layouts**

Replace `.agents/skills/awow-usage-coach/scripts/awow_extract.py:52-61`:

```python
# Shared, canonical reader for an mlflow_export — the single source of the mlflow.*
# field strings, used by both this extractor and tools/session_timeline.py so the two
# consumers can't silently diverge on the trace format. Lives under the repo's tools/.
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
try:
    import mlflow_reader as mr
except ImportError as e:
    raise SystemExit(
        "could not import the shared mlflow_reader (expected at <repo>/tools/mlflow_reader.py); "
        f"is this script running inside the awow repo tree? ({e})")
```

with:

```python
# Shared, canonical reader for an mlflow_export — the single source of the mlflow.*
# field strings, used by both this extractor and session_timeline.py so the two
# consumers can't silently diverge on the trace format.
#
# Two legitimate layouts, because this skill ships in the awow-telemetry plugin
# as well as living in the maintainer repo:
#   <repo>/.agents/skills/awow-usage-coach/scripts/ -> parents[4] is <repo>
#   <plugin>/skills/awow-usage-coach/scripts/       -> parents[3] is <plugin>
# Both put the reader at <root>/tools/mlflow_reader.py. Try each; if neither
# holds, fail loudly naming every path tried — a missing reader means the trace
# format is unknown, and guessing it is worse than stopping.
_HERE = Path(__file__).resolve()
_CANDIDATE_TOOL_DIRS = [_HERE.parents[4] / "tools", _HERE.parents[3] / "tools"]
for _d in _CANDIDATE_TOOL_DIRS:
    if (_d / "mlflow_reader.py").is_file():
        sys.path.insert(0, str(_d))
        break
else:
    raise SystemExit(
        "could not locate the shared mlflow_reader.py. Looked in:\n  "
        + "\n  ".join(str(d) for d in _CANDIDATE_TOOL_DIRS)
        + "\nExpected either the awow repo tree (<repo>/tools/) or an installed "
          "awow-telemetry plugin (<plugin>/tools/).")
import mlflow_reader as mr
```

The `for … else` runs the `else` only when the loop completes without `break`, so a missing reader raises before the import rather than after — and the `import` itself is left bare so a genuinely broken `mlflow_reader.py` raises its own traceback instead of being flattened into a path-not-found message.

- [ ] **Step 2: Drop the deleted command from `KNOWN_COMMANDS`**

Replace `.agents/skills/awow-usage-coach/scripts/awow_extract.py:69-80`:

```python
KNOWN_COMMANDS = {
    "setup-awow": "kickoff",
    "awow-add": "meta",
    "awow-status": "meta",
    "refinement-prep": "seed",
    "process-workitem": "seed",
    "process-transcript": "seed",
    "board-skill": "spread",
    "daily-digest": "standardise",
    "weekly-digest": "standardise",
    "cross-team-view": "standardise",
}
```

with:

```python
# The set is enumerated so reports can call out *coverage* — which commands
# exist, which go unused. It must therefore name only commands that can still
# be invoked: `weekly-digest` and `cross-team-view` were removed from the
# surface, and the weekly window survives as a /daily-digest parameter rather
# than as its own command (design spec 4.4).
KNOWN_COMMANDS = {
    "setup-awow": "kickoff",
    "awow-add": "meta",
    "awow-status": "meta",
    "refinement-prep": "seed",
    "process-workitem": "seed",
    "process-transcript": "seed",
    "board-skill": "spread",
    "daily-digest": "standardise",
}
```

`cross-team-view` goes with it: `grep -rn 'cross-team-view' .agents/commands/` returns nothing — it was already culled from `main`, and the spec names it at §5.3 as a stale reference in `guides/index.html:638`. Leaving it here would be the same defect as `weekly-digest`, one release older.

- [ ] **Step 3: Verify the script still parses and both layouts resolve**

```bash
python3 -c "import ast,sys; ast.parse(open('.agents/skills/awow-usage-coach/scripts/awow_extract.py').read()); print('parses')"
python3 .agents/skills/awow-usage-coach/scripts/awow_extract.py --help >/dev/null && echo "repo layout resolves"
```

Expected: `parses`, then `repo layout resolves`. The `--help` path exercises the import block before argparse exits, so a broken `sys.path` insert fails here.

```bash
python tools/gather.py
python3 dist-telemetry/skills/awow-usage-coach/scripts/awow_extract.py --help >/dev/null && echo "plugin layout resolves"
```

Expected: `plugin layout resolves`. This is the check that would have failed before Step 1 — the built copy sits one directory shallower than the source.

```bash
python3 -c "
import json,sys
sys.argv=['x']
" ; grep -c 'weekly-digest\|cross-team-view' .agents/skills/awow-usage-coach/scripts/awow_extract.py
```

Expected: `0`.

- [ ] **Step 4: Verify the build and commit**

```bash
python tools/gather.py --check && python tools/lint-paths.py && python3 tests/telemetry-split/test_telemetry_split.py
```

Expected: `All stubs in sync.`, `Path tokens clean.`, `Telemetry split OK.`

```bash
git add .agents/skills/awow-usage-coach/scripts/awow_extract.py .claude/ .github/ dist/ dist-telemetry/
git commit -m "Resolve mlflow_reader from either the repo tree or an installed telemetry plugin, failing loudly with every path tried when neither holds. Drop weekly-digest and cross-team-view from KNOWN_COMMANDS — neither is invokable."
```

---

### Task 6: The dangling references

**Files:**
- Modify: `.agents/AGENTS.md:95`, `.agents/skills/README.md:31-33`, `.agents/skills/session-correlation/SKILL.md:11` and `:106`, `.agents/commands/setup-awow.md` (the `- **mlflow-export** — swap the exporter script` block; PR 1 shifted its line numbers)
- Modify: `guides/guide-trace-analysis.html`, `guides/guide-session-timeline.html`, `guides/guide-session-correlation.html`, `guides/guide-prompt-taxonomy.html`, `guides/index.html`

**Interfaces:**
- Consumes: the channel marks from Task 1 and the build from Task 3.
- Produces: nothing consumed by later tasks. Documentation only — no code, no build behaviour.

**The rule generating this list:** every file that names a moving skill and states or implies where it lives. A file that merely *uses* a moving skill's name as a label needs no edit; a file that tells the reader it is part of the base awow install does. Verified with:

```bash
grep -rln "mlflow-export\|prompt-skill-analysis\|project-timeline\|awow-usage-coach\|session-export" \
  --include="*.md" --include="*.html" .agents/ guides/
```

That returns ten source files. `tools/awow.lock.json` also matches but is regenerated, not hand-edited, and belongs to PR 2 (§4.4). `meta/proposals/*.md` match too — those are historical records of decisions already taken and are deliberately left as written.

- [ ] **Step 1: `.agents/AGENTS.md`**

Replace line 95:

```markdown
- **Never write session-derived output to a tracked path** (`proposals/`, `context/`, the knowledge base, anywhere git tracks). The `mlflow-export`, `awow-usage-coach`, `prompt-skill-analysis`, and `project-timeline` skills produce this kind of output — route it to the gitignored `coach_reviews/` (or `mlflow_export/`) only.
```

with:

```markdown
- **Never write session-derived output to a tracked path** (`proposals/`, `context/`, the knowledge base, anywhere git tracks). The `awow-telemetry` skills — `mlflow-export`, `awow-usage-coach`, `prompt-skill-analysis`, `project-timeline`, `session-export` — produce this kind of output; route it to the gitignored `coach_reviews/` (or `mlflow_export/`) only. They ship in the separate `awow-telemetry` plugin, but this rule binds in this repo whether or not that plugin is installed.
```

`session-export` was missing from the original list and writes whole transcripts to disk — the largest producer of exactly the data this rule exists to keep untracked. Adding it is the point of doing the sweep by rule rather than by the names that happened to be there.

- [ ] **Step 2: `.agents/skills/README.md`**

Replace lines 31-33:

```markdown
- [`mlflow-export/`](./mlflow-export/) — export agent traces + sessions to local JSON. Ships with a Databricks-MLflow exporter; swap the script for your backend's equivalent.
- [`prompt-skill-analysis/`](./prompt-skill-analysis/) — assess prompt quality from an agent session. Ships with parsers for raw Claude Code JSONL and the `mlflow-export` output shape; extend for other harnesses.
- [`awow-usage-coach/`](./awow-usage-coach/) — propose CLAUDE.md nudges or coach an individual based on workflow shape. Consumes the `mlflow-export` JSON; rubric is harness-agnostic.
```

with:

```markdown
- [`mlflow-export/`](./mlflow-export/) — export agent traces + sessions to local JSON. Ships with a Databricks-MLflow exporter; swap the script for your backend's equivalent.
- [`prompt-skill-analysis/`](./prompt-skill-analysis/) — assess prompt quality from an agent session. Ships with parsers for raw Claude Code JSONL and the `mlflow-export` output shape; extend for other harnesses.
- [`awow-usage-coach/`](./awow-usage-coach/) — propose AGENTS.md nudges or coach an individual based on workflow shape. Consumes the `mlflow-export` JSON; rubric is harness-agnostic.

### Two plugins, one source tree

Skills marked `channel: telemetry` in their frontmatter build into the separate **`awow-telemetry`** plugin rather than into `awow` — `mlflow-export`, `prompt-skill-analysis`, `project-timeline`, `awow-usage-coach`, `session-export`. The base plugin keeps the four behavioural skills: `using-awow`, `board-aware-development`, `architecture-aware-development`, `user-story-template`. Different audience, different dependency profile, different privacy posture; and every skill description loads into every session, so a telemetry surface nobody uses is a tax on everybody.

The source stays here either way — `channel:` selects the payload, not the location. Install with `/plugin install awow-telemetry@awow`. **Claude Code only this release:** `tools/sync-dist.sh` publishes only `dist/` to `awow-dist`, which is the Codex and Pi install source, so telemetry does not reach those harnesses.
```

The `CLAUDE.md` → `AGENTS.md` correction in the third bullet matches the skill's own description, which already says `.agents/AGENTS.md / copilot-instructions`.

- [ ] **Step 3: `.agents/skills/session-correlation/SKILL.md`**

Replace line 11:

```markdown
Agent-originated board entries normally have no link back to the trace that produced them, so the downstream skills (`awow-usage-coach`, `daily-digest`, `weekly-digest`, `prompt-skill-analysis`) cannot join board content to session data. This skill closes that gap with a one-line **session footer** on every entry the agent authors.
```

with:

```markdown
Agent-originated board entries normally have no link back to the trace that produced them, so the downstream consumers (`daily-digest`, plus the `awow-telemetry` skills `awow-usage-coach` and `prompt-skill-analysis`) cannot join board content to session data. This skill closes that gap with a one-line **session footer** on every entry the agent authors.
```

Replace, in line 79 (inside the numbered list):

```
   `mlflow.trace.session` tag, so `awow-usage-coach`, `daily-digest`, and
```

with:

```
   `mlflow.trace.session` tag, so `daily-digest` and the `awow-telemetry` skills
```

Read the two lines following `:79` before editing and keep the sentence grammatical across the wrap — the replacement drops one clause, so the continuation may need its leading word adjusted.

Replace, in line 106, the final sentence:

```
Exporting and analysing the traces is `mlflow-export` + `prompt-skill-analysis` / `awow-usage-coach`.
```

with:

```
Exporting and analysing the traces is the separate `awow-telemetry` plugin (`mlflow-export` + `prompt-skill-analysis` / `awow-usage-coach`), installed with `/plugin install awow-telemetry@awow`.
```

Leave the `../claudetracing` reference on line 106 alone — PR 1 owns the dangling-citation sweep, and this file was not in its scope. Note it in the PR description instead.

- [ ] **Step 4: `.agents/commands/setup-awow.md`**

Locate the block by its first line — `- **mlflow-export** — swap the exporter script` — not by line number. PR 1 Task 8 edits this file above the block: it drops dangling citations at `:189` and `:239` and rewrites the Step 8 / Step 9 payload paths. The net line shift is not predictable from here (some are inline citation removals, some are multi-line rewrites), which is the point — `:262-264` was measured on `main` and cannot be trusted once PR 1 has landed. Anchor on the text and let the line fall where it falls.

Replace the three-bullet block beginning `- **mlflow-export** — swap the exporter script`:

```markdown
     - **mlflow-export** — swap the exporter script for the team's tracing backend (LangSmith, Helicone, OTLP, raw JSONL). The downstream skills consume the JSON layout documented in `mlflow-export/SKILL.md`; match that shape or update the consumers too.
     - **prompt-skill-analysis** — add a parser for the team's harness session format (Copilot, Cursor, etc.). The rubric is harness-agnostic; only the input branch needs work.
     - **awow-usage-coach** — adjust the intent taxonomy if the team's vocabulary doesn't fit; otherwise rely on the harness-agnostic `working_directory` + `files_modified` lenses.
```

with:

```markdown
     - **mlflow-export**, **prompt-skill-analysis**, **awow-usage-coach**, **project-timeline**, **session-export** — these five ship in the separate `awow-telemetry` plugin, not in `awow`. If the team has not installed it (`/plugin install awow-telemetry@awow`), say so once and move on; do not offer to customise skills that are not present. If it is installed, or the repo is vendored and carries the sources under `.agents/skills/`, the customisations worth surfacing are:
       - **mlflow-export** — swap the exporter script for the team's tracing backend (LangSmith, Helicone, OTLP, raw JSONL). The downstream skills consume the JSON layout documented in `mlflow-export/SKILL.md`; match that shape or update the consumers too.
       - **prompt-skill-analysis** — add a parser for the team's harness session format (Copilot, Cursor, etc.). The rubric is harness-agnostic; only the input branch needs work.
       - **awow-usage-coach** — adjust the intent taxonomy if the team's vocabulary doesn't fit; otherwise rely on the harness-agnostic `working_directory` + `files_modified` lenses.
```

The presence check matters: this step's script tells the agent to read each skill's frontmatter and open its bundled files. In a base-plugin-only install those paths do not exist, and the step would stall on a file that is legitimately absent.

- [ ] **Step 5: The four guides plus the index**

Each gets one sentence establishing which plugin the skills come from. The guides are standalone HTML with no shared include, so this is five separate edits.

`guides/guide-trace-analysis.html` — replace the TL;DR paragraph at line 122:

```html
    <p>One skill <strong>pulls</strong> the traces down to local JSON (<code>mlflow-export</code>); two skills <strong>read</strong> that JSON to produce markdown reports &mdash; <code>prompt-skill-analysis</code> (how well someone prompts) and <code>awow-usage-coach</code> (how a team or person works, and what to change). In every case the script only counts and extracts; the qualitative judgment lives in the agent.</p>
```

with:

```html
    <p>One skill <strong>pulls</strong> the traces down to local JSON (<code>mlflow-export</code>); two skills <strong>read</strong> that JSON to produce markdown reports &mdash; <code>prompt-skill-analysis</code> (how well someone prompts) and <code>awow-usage-coach</code> (how a team or person works, and what to change). In every case the script only counts and extracts; the qualitative judgment lives in the agent.</p>
    <p style="font-size:0.85rem;color:var(--text-3);margin:8px 0 0;">All three ship in <code>awow-telemetry</code>, a separate plugin from <code>awow</code> &mdash; install with <code>/plugin install awow-telemetry@awow</code>. Claude Code only for now; the Codex and Pi payload carries the base plugin alone.</p>
```

and its footer at line 281:

```html
    <p style="font-size:0.78rem;color:var(--text-3);margin:0;">Sources of truth: the three <code>SKILL.md</code> files under <code>.agents/skills/</code>. Companion guide: <code>guide-session-correlation.html</code> (the write side). This guide is self-contained &mdash; no external resources.</p>
```

with:

```html
    <p style="font-size:0.78rem;color:var(--text-3);margin:0;">Sources of truth: the three <code>SKILL.md</code> files under <code>.agents/skills/</code>, built into the <code>awow-telemetry</code> plugin. Companion guide: <code>guide-session-correlation.html</code> (the write side). This guide is self-contained &mdash; no external resources.</p>
```

`guides/guide-session-timeline.html` — replace the callout at line 130:

```html
      <strong>No tracing required.</strong> The trace-analysis path (<code>mlflow-export</code> &rarr; <code>prompt-skill-analysis</code> / <code>awow-usage-coach</code>) needs traces to already exist in MLflow, written by a Stop hook. This tool reads the JSONL Claude Code writes for you anyway. If the logs are on disk, you can render the timeline &mdash; that is the whole point.
```

with:

```html
      <strong>No tracing required.</strong> The trace-analysis path (<code>mlflow-export</code> &rarr; <code>prompt-skill-analysis</code> / <code>awow-usage-coach</code>) needs traces to already exist in MLflow, written by a Stop hook. This tool reads the JSONL Claude Code writes for you anyway. If the logs are on disk, you can render the timeline &mdash; that is the whole point. All of it, this tool included, ships in the <code>awow-telemetry</code> plugin: <code>/plugin install awow-telemetry@awow</code>.
```

`guides/guide-session-correlation.html` — replace the intro line of the downstream list at line 325:

```html
    <p>Correlation is the join. Acting on it is a separate pipeline of analysis skills &mdash; the <em>read</em> side. They share only one thing with this guide: they need the traces to exist. Each is covered in its own guide; in brief:</p>
```

with:

```html
    <p>Correlation is the join. Acting on it is a separate pipeline of analysis skills &mdash; the <em>read</em> side &mdash; shipped as a separate plugin, <code>awow-telemetry</code> (<code>/plugin install awow-telemetry@awow</code>). They share only one thing with this guide: they need the traces to exist. Each is covered in its own guide; in brief:</p>
```

`guides/guide-prompt-taxonomy.html` — replace the footer at line 238:

```html
    <p style="font-size:0.78rem;color:var(--text-3);margin:0;">Used by: <code>/awow-usage-coach</code> (forward-lens reflection), <code>/weekly-digest</code> and <code>/daily-digest</code> (intent-tagged synthesis). The canonical definitions live in <code>.agents/skills/awow-usage-coach/SKILL.md</code>; this guide is the human-facing companion.</p>
```

with:

```html
    <p style="font-size:0.78rem;color:var(--text-3);margin:0;">Used by: <code>/awow-usage-coach</code> (forward-lens reflection, in the <code>awow-telemetry</code> plugin) and <code>/daily-digest</code> (intent-tagged synthesis). The canonical definitions live in <code>.agents/skills/awow-usage-coach/SKILL.md</code>; this guide is the human-facing companion.</p>
```

`/weekly-digest` is dropped here because PR 2 — which this plan assumes has landed — removes it outright with no alias (§4.4). The file describes the shipped surface, and by the time this step runs that surface no longer has the command.

`guides/index.html` — replace the Prompt-taxonomy card description at line 344:

```html
        <p class="c-desc">Name what you&rsquo;re doing before you ask &mdash; an eight-intent vocabulary (<code>investigate</code> &middot; <code>plan</code> &middot; <code>propose</code> &middot; <code>implement</code> &middot; <code>refine</code> &middot; <code>verify</code> &middot; <code>document</code> &middot; <code>inform</code>) that sharpens prompts and is the lens <code>/awow-usage-coach</code> reads sessions back through.</p>
```

with:

```html
        <p class="c-desc">Name what you&rsquo;re doing before you ask &mdash; an eight-intent vocabulary (<code>investigate</code> &middot; <code>plan</code> &middot; <code>propose</code> &middot; <code>implement</code> &middot; <code>refine</code> &middot; <code>verify</code> &middot; <code>document</code> &middot; <code>inform</code>) that sharpens prompts and is the lens <code>/awow-usage-coach</code> (in the <code>awow-telemetry</code> plugin) reads sessions back through.</p>
```

Leave `guides/index.html:638`'s `cross-team-view` reference and the `guide-setup-and-two-harnesses.html` title alone — §5.3 assigns the wider guides sweep to PR 4.

- [ ] **Step 6: Verify every remaining mention is deliberate**

```bash
grep -rn "mlflow-export\|prompt-skill-analysis\|project-timeline\|awow-usage-coach\|session-export" \
  --include="*.md" --include="*.html" .agents/ guides/ | grep -vc "awow-telemetry"
```

Expected: a non-zero count. Every remaining hit is a *usage* mention (a skill naming its own sibling, a code block invoking a script) rather than a placement claim; the placement claims are the ones now qualified. Read the list once and confirm none of them tells a reader the skill is part of the base install.

```bash
python tools/gather.py --check
```

Expected: `update:` lines for `.claude/`, `.github/`, `dist/`, and `dist-telemetry/` copies of the edited `.agents/` sources, and exit 1.

- [ ] **Step 7: Regenerate, verify, commit**

```bash
python tools/gather.py
python tools/gather.py --check && python tools/lint-paths.py
python3 tests/telemetry-split/test_telemetry_split.py
python3 tests/telemetry-split/test_orphan_roots.py
```

Expected: `All stubs in sync.`, `Path tokens clean.`, `Telemetry split OK.`, `Orphan detection covers both payload roots.`

```bash
git add .agents/ guides/ .claude/ .github/ AGENTS.md dist/ dist-telemetry/
git commit -m "Point every reference to a moving skill at the awow-telemetry plugin, and stop /setup-awow offering to customise skills a base-plugin install does not have. Adds session-export to the untracked-output rule, which the original list missed."
```

---

### Task 7: Wire CI and run the full suite

**Files:**
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: everything above.
- Produces: the evidence that PR 3 is complete, and the two CI steps that keep it true.

- [ ] **Step 1: Add the two test steps**

In `.github/workflows/ci.yml`, add to the `gather-check` job immediately after the `Payload classification` step that PR 1 added (which itself follows `Path-token substitution`, which follows `Path-token lint` at `:17-18`):

```yaml
      - name: Telemetry split
        run: python3 tests/telemetry-split/test_telemetry_split.py
      - name: Orphan detection across payload roots
        run: python3 tests/telemetry-split/test_orphan_roots.py
```

Both must run *after* `python tools/gather.py --check` at `:15-16`, because both read the built payload. The step order in the file already guarantees that.

- [ ] **Step 2: Run every check CI runs, plus every test in the repo**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/gather-tokens/test_tokens.py \
  && python3 tests/payload-classification/test_classification.py \
  && python3 tests/telemetry-split/test_telemetry_split.py \
  && python3 tests/telemetry-split/test_orphan_roots.py \
  && python3 tests/awow-lock/test_awow_lock.py \
  && python3 tests/hooks/test_lifecycle_seam_check.py \
  && bash tests/harness/run-harness-tests.sh all
```

Expected: every one passes, ending in `all checks passed`.

- [ ] **Step 3: Confirm the two payloads are disjoint**

```bash
comm -12 \
  <(cd dist && find . -type f | sort) \
  <(cd dist-telemetry && find . -type f | sort)
echo "--- overlap above (expected: only ./README.md and ./.claude-plugin/plugin.json) ---"
```

Expected: exactly two lines, `./.claude-plugin/plugin.json` and `./README.md`. Those are same-named, different-content per-plugin manifests and front pages — every other path is unique to one payload. Any third line is a file shipping twice.

- [ ] **Step 4: Confirm the Claude-Code-only constraint holds at the file level**

```bash
for p in .codex-plugin package.json .agents agent-skills commands hooks context; do
  test -e "dist-telemetry/$p" && echo "LEAK: dist-telemetry/$p" || true
done
echo "isolation check done"
grep -rl "mlflow-export\|prompt-skill-analysis\|project-timeline\|awow-usage-coach\|session-export" \
  dist/agent-skills/ | head
echo "--- agent-skills references above (expected: none) ---"
```

Expected: no `LEAK:` lines, then `isolation check done`; and no paths from the second grep. Codex and Pi read `dist/agent-skills/` exclusively, so a hit there means telemetry reached a harness it does not target.

- [ ] **Step 5: Confirm the base plugin's session start is unaffected**

```bash
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/session-start | grep -c "Error reading" || true
test -e dist-telemetry/hooks && echo "LEAK: telemetry ships hooks" || echo "telemetry ships no hooks"
```

Expected: `0`, then `telemetry ships no hooks`. `using-awow` stays in the base plugin, so the hook is unmoved; and the absence of a telemetry `hooks/` is what stops a both-plugins-installed session double-injecting the reflex.

- [ ] **Step 6: Commit and report**

```bash
git add .github/workflows/ci.yml
git commit -m "Run the telemetry-split and orphan-root suites in CI, after the gather check that builds the payloads they read."
```

Summarise: files changed, the two suites added, the six CI steps now guarding the build, and the version now at `0.6.0`. Note explicitly that `awow-telemetry` does not publish to `awow-dist` by design, so `tools/sync-dist.sh` needs no change and the Codex/Pi payload is unchanged in shape. Do not open a PR and do not push — both need explicit approval.

---

## Self-Review

**Spec coverage.** §4.3 `channel: telemetry` → Task 1. §4.3 orphan detection (`find_orphans:707`, `SURFACE_ROOTS:667`, `filter_surface:684`, `--surface` choices, the `DIST_DIR in surfaces` guard at `:735`) → Tasks 2 and 3. §4.3 `PLUGIN_TOOL_PATHS` split and the `awow_extract.py` note → Tasks 3 and 5. §4.3 second marketplace entry → Task 4. §4.3 Claude-Code-only scope constraint → the build-directory section, enforced by Task 3's isolation assertions and Task 7 Step 4. §4.3's third bullet (*"Telemetry soft-depends on base-plugin content. Acceptable? Decide before shipping."*) → decided in the build-directory section: accept, vendor nothing, and turn the executable half into a CI check. §4.3 dangling references → Task 6. §8 version `0.6.0` and the three-channel warning → Task 4 and Global Constraints.

**Deliberately not here.** Zero commands move — §4.3 moves skills only, and §4.4's command work is PR 2. `tools/awow.lock.json` lists the five moving skills' hashes, which change in Task 1 when the frontmatter gains `channel: telemetry`. PR 2 already regenerated the lock under §4.4, but it did so against the pre-split frontmatter, so this PR leaves those five hashes stale again. Nothing goes red — `tests/awow-lock/test_awow_lock.py` builds throwaway repos rather than validating the committed lockfile — and no step here regenerates it, because the lock is a vendored-adopter upgrade artefact and PR 4 is the last PR before `sync-dist`. Flag it in the PR description so whoever lands PR 4 regenerates once, after the surface has stopped moving. `tools/sync-dist.sh` needs no change — that is the finding, not an omission. `.agents/skills/using-awow/SKILL.md` is untouched, per §10's consolidation into PR 1.

**Where I found the spec wrong or underdetermined.**

1. **"ELEVEN dangling references" is ten files, or eleven defects.** §4.3 names `.agents/skills/session-correlation/SKILL.md`, `.agents/commands/setup-awow.md`, `.agents/AGENTS.md`, `.agents/skills/README.md`, `awow_extract.py`, four guides, and `guides/index.html` — ten files. The count reaches eleven only if `awow_extract.py` is counted twice, which is defensible: it carries two independent defects, the `"weekly-digest"` entry the spec names at `:78` **and** the `parents[4]` import at `:55`, which the spec does not mention at all and which breaks the telemetry plugin outright. Tasks 5 and 6 fix all eleven defects across ten files.
2. **§4.3's `find_orphans:707` line number is right; `:694-720` is not.** `find_orphans` spans `:694-716`. The identity check is at `:707` exactly as stated.
3. **The `--surface` choices are at `:726`, not `:727`.** `:725` is `parser.add_argument(`, `:726` is the `"--surface", choices=[…]` line, `:727` is the closing paren. Both numbers are moot by the time this PR runs — PR 1 shifts them — which is why every §4.3 line citation in `main()` is re-expressed as literal old text in Task 3 Step 6.
4. **§4.3's claim that a sibling `dist-telemetry/` "never publishes" is stated as a problem; it is the solution.** The spec presents non-publication as the reason a sibling fails, then separately concludes telemetry must be Claude-Code-only. Those are the same fact. Claude Code installs from `CauchyIO/awow` and resolves `.claude-plugin/marketplace.json`'s `source` relative to the repo root, so a sibling installs fine on the one harness that is in scope, and is structurally invisible to the two that are not. Reading them as opposed is what makes the build directory look undecidable.
5. **`{AWOW_TOOLS}/gather.py` at `awow-usage-coach/SKILL.md:131` is a pre-existing rendering defect the spec does not list.** It renders to `${CLAUDE_PLUGIN_ROOT}/tools/gather.py`, and `gather.py` is deliberately never shipped (`gather.py:66-68`). Task 1 Step 6 removes the path. Found because Task 3's dependency assertion refused to pass with it present — which is the argument for that assertion existing.
6. **`session-export` was missing from `.agents/AGENTS.md:95`'s untracked-output rule.** The rule names four telemetry skills; `session-export` writes full session transcripts to disk and is the largest producer of the data the rule protects. Task 6 Step 1 adds it. This is the same omission class §4.1.2's convention warns about — a list without its generating rule.
7. **`cross-team-view` survives in `awow_extract.py:79` although it was culled from `main` before this release.** `grep -rn 'cross-team-view' .agents/commands/` is empty. Task 5 Step 2 removes it alongside `weekly-digest`.

**Type consistency.** `declared_channel(text: str) -> str` returns one of `"both"`, `"vendored"`, `"bootstrap"`, `"telemetry"`, spelled identically in Tasks 1 and 3 and in the test's `expected` map. `is_vendored_channel` and `is_telemetry_channel` both keep the `(text: str) -> bool` shape the four existing call sites already pass. `skill_stubs` gains a fourth parameter `channel: str = "both"`, defaulted so `plan_plugin:645` and `plan_agent_skills:537` need no edit. `plan_telemetry() -> list[Stub]` matches `plan_plugin`, `plan_codex`, and `plan_pi`; `Stub` is the frozen dataclass at `gather.py:136-140` with fields `target: Path`, `content: str`, `mode: int | None`. `DIST_TELEMETRY_DIR: Path` and `GENERATED_ROOTS: tuple[Path, ...]` are consumed by `find_orphans` and by both tests under the same names. `TELEMETRY_TOOL_PATHS: list[str]` matches `PLUGIN_TOOL_PATHS`'s existing shape — paths relative to `tools/`, joined against `REPO_ROOT / "tools"` at `copy_stub` time.

**Placeholder scan.** None remain. Three points where a placeholder was tempting, and what was decided instead: (a) the build directory — resolved to `dist-telemetry/` with the manifest and rsync evidence written out, rather than deferred to the implementer; (b) the version bump, which could collide with PR 2 — resolved by stating both branches with the exact command that distinguishes them, rather than a "bump if needed"; (c) the `mlflow_reader` import, where a `try/except ImportError: pass` would have been the shortest path — resolved as an explicit candidate list with a `for/else` that raises naming every path tried, since a silent fallback here would mean analysing traces with an unknown schema. Task 1 Step 1's unused constants are flagged as such in prose with the reason (diff stability across two commits), not left to look like an oversight.

**Task boundaries.** Seven tasks, each ending in a commit a reviewer could reject independently. Tasks 2 and 3 could technically be one — the orphan fix has no user-visible effect until a second root exists — but they stay split deliberately: a reviewer can approve the orphan-detection change on its own merits without also approving the payload topology, and landing detection first is what makes Task 3 Step 8's real-build orphan test meaningful rather than tautological. Task 7 adds no production code; it exists because the disjointness and isolation checks are the deliverable that proves the split actually split, and folding them into Task 6 would let them be skipped.
