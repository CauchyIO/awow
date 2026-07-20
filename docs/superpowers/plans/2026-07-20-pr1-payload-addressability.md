# PR 1 — Payload Addressability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the shipped `dist/` payload addressable, so a plugin-installed command can read awow's own machinery instead of looking for it in the adopter's repo.

**Architecture:** Add a fourth path token, `{AWOW_ROOT}`, substituted at build time exactly as `{AWOW_TOOLS}` already is — `${CLAUDE_PLUGIN_ROOT}` on the Claude channel, `../..` on the agent-skills channel. Ship the machinery files under `context/` into `dist/`, selected by a testable predicate rather than a hand-maintained list, and enforce that selection in CI in both directions. Then rewrite the command bodies that read machinery to use `{HUB}` first (so a vendored override wins) and fall back to `{AWOW_ROOT}`.

**Tech Stack:** Python 3.12 stdlib only (no pytest, no third-party). Bash for the harness suite. `tools/gather.py` is the build; `tools/lint-paths.py` is the token linter; `.github/workflows/ci.yml` runs both plus `tests/harness/run-harness-tests.sh all`.

**Spec:** `docs/superpowers/specs/2026-07-20-plugin-first-readme-design.md` §4.1, §4.2, §4.6 (the reflex paragraph only). This plan covers PR 1 of five.

## Global Constraints

- **Python 3.12, stdlib only.** No pytest, no network. Tests are plain scripts run as `python3 tests/<dir>/test_<name>.py`, following `tests/awow-lock/test_awow_lock.py`. Every test module opens with a docstring ending in a `Run:` line.
- **Never edit generated files.** `.claude/`, `.github/` (except the new generated payload), `dist/`, root `AGENTS.md`, `.claude/CLAUDE.md`, `.github/copilot-instructions.md` are `gather.py` output. Edit the source under `.agents/` and re-run the gather.
- **Three channels exist, not two:** `vendored` (6 files, excluded from payload), `bootstrap` (2 files — `setup-awow.md`, `update-awow.md` — which *do* ship), and the default. Do not assume a binary.
- **`tools/lint-paths.py` needs no change.** Its `BARE` regex at `:11` is `(?<![{/\w.\-])(context|tools|proposals)/`; the `/` in `{AWOW_ROOT}/context/` falls inside the negative lookbehind. Verified empirically. If a task makes lint fail, the task is wrong, not the linter.
- **After any `.agents/` edit, run `python tools/gather.py`** and commit the regenerated surfaces alongside the source change, or `--check` fails in CI.
- **Commit message style:** max 2 sentences.
- **Do not create PRs.** This plan produces commits on `feat/plugin-first-readme` only.

---

### Task 1: The `{AWOW_ROOT}` token

**Files:**
- Modify: `tools/gather.py:397-399` (`PLUGIN_TOKEN_SUBSTITUTIONS`), `tools/gather.py:413-415` (`AGENT_SKILLS_TOKEN_SUBSTITUTIONS`)
- Create: `tests/gather-tokens/test_tokens.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `{AWOW_ROOT}` resolves to `${CLAUDE_PLUGIN_ROOT}` via `render_plugin_body(text: str) -> str`, and to `../..` via `render_agent_skills_body(text: str) -> str`. Both already exist at `gather.py:402` and `:418`; this task only extends their substitution tables. Tasks 3 and 6 depend on both.

- [ ] **Step 1: Write the failing test**

Create `tests/gather-tokens/test_tokens.py`:

```python
"""Regression test for the path-token substitution tables in tools/gather.py.

{AWOW_TOOLS} and {AWOW_ROOT} are resolved at build time per channel; {HUB} and
{PROJECT} ship as-is because the session reflex teaches their resolution. This
asserts all four behaviours on both channels, and that the agent-skills channel
never emits ${CLAUDE_PLUGIN_ROOT} (Codex and Pi cannot resolve it).

Pure stdlib; no pytest, no network.

Run:  python3 tests/gather-tokens/test_tokens.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import importlib

gather = importlib.import_module("gather")

FAILURES = []


def check(label, actual, expected):
    if actual != expected:
        FAILURES.append(f"{label}\n  expected: {expected!r}\n  actual:   {actual!r}")


def main() -> int:
    plugin = gather.render_plugin_body
    skills = gather.render_agent_skills_body

    check(
        "plugin: {AWOW_ROOT} -> ${CLAUDE_PLUGIN_ROOT}",
        plugin("read {AWOW_ROOT}/context/tooling/mining.md"),
        "read ${CLAUDE_PLUGIN_ROOT}/context/tooling/mining.md",
    )
    check(
        "plugin: {AWOW_TOOLS} still resolves",
        plugin("run {AWOW_TOOLS}/gather.py"),
        "run ${CLAUDE_PLUGIN_ROOT}/tools/gather.py",
    )
    check(
        "agent-skills: {AWOW_ROOT} -> ../..",
        skills("read {AWOW_ROOT}/context/tooling/mining.md"),
        "read ../../context/tooling/mining.md",
    )
    check(
        "agent-skills: {AWOW_TOOLS} still resolves",
        skills("run {AWOW_TOOLS}/gather.py"),
        "run ../../tools/gather.py",
    )
    # {HUB}/{PROJECT} are session-resolved, never build-substituted.
    for name, render in (("plugin", plugin), ("agent-skills", skills)):
        check(
            f"{name}: {{HUB}} passes through",
            render("read {HUB}/context/tooling/board.md"),
            "read {HUB}/context/tooling/board.md",
        )
        check(
            f"{name}: {{PROJECT}} passes through",
            render("write {PROJECT}/proposals/x.md"),
            "write {PROJECT}/proposals/x.md",
        )
    # Codex and Pi cannot resolve ${CLAUDE_PLUGIN_ROOT}.
    out = skills("{AWOW_ROOT}/context/x.md and {AWOW_TOOLS}/y.py")
    if "${CLAUDE_PLUGIN_ROOT}" in out:
        FAILURES.append(f"agent-skills leaked ${{CLAUDE_PLUGIN_ROOT}}: {out!r}")

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Path-token substitution OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/gather-tokens/test_tokens.py`

Expected: FAIL, with two lines naming the unsubstituted `{AWOW_ROOT}`:

```
FAIL plugin: {AWOW_ROOT} -> ${CLAUDE_PLUGIN_ROOT}
  expected: 'read ${CLAUDE_PLUGIN_ROOT}/context/tooling/mining.md'
  actual:   'read {AWOW_ROOT}/context/tooling/mining.md'
FAIL agent-skills: {AWOW_ROOT} -> ../..
...
2 failure(s).
```

- [ ] **Step 3: Add the token to both substitution tables**

In `tools/gather.py`, replace lines 394-399:

```python
# Path tokens (see .agents/AGENTS.md "Path tokens"): {AWOW_TOOLS} and
# {AWOW_ROOT} resolve at build time for the plugin surface — the payload knows
# where it lives. {HUB} and {PROJECT} ship as-is; the session reflex teaches
# their resolution.
PLUGIN_TOKEN_SUBSTITUTIONS = [
    ("{AWOW_TOOLS}", "${CLAUDE_PLUGIN_ROOT}/tools"),
    ("{AWOW_ROOT}", "${CLAUDE_PLUGIN_ROOT}"),
]
```

And replace lines 413-415:

```python
AGENT_SKILLS_TOKEN_SUBSTITUTIONS = [
    ("{AWOW_TOOLS}", "../../tools"),
    ("{AWOW_ROOT}", "../.."),
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tests/gather-tokens/test_tokens.py`
Expected: `Path-token substitution OK.` and exit 0.

- [ ] **Step 5: Verify the build and linter are still clean**

Run: `python tools/gather.py --check && python tools/lint-paths.py`
Expected: both pass. No source yet uses `{AWOW_ROOT}`, so `dist/` is unchanged.

- [ ] **Step 6: Wire the test into CI**

In `.github/workflows/ci.yml`, add a step to the `gather-check` job immediately after the `Path-token lint` step:

```yaml
      - name: Path-token substitution
        run: python3 tests/gather-tokens/test_tokens.py
```

- [ ] **Step 7: Commit**

```bash
git add tools/gather.py tests/gather-tokens/test_tokens.py .github/workflows/ci.yml
git commit -m "Add the {AWOW_ROOT} path token so payload machinery is addressable from a plugin install."
```

---

### Task 2: Payload classification, enforced both ways

**Files:**
- Modify: `tools/gather.py` (add manifest constants after `PLUGIN_TOOL_PATHS` at `:123-130`; add `classify_context_path`, `unclassified_context_paths`; call from `main()` at `:722`)
- Create: `tests/payload-classification/test_classification.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces:
  - `PAYLOAD_CONTEXT_PATHS: list[str]` — repo-relative paths under `context/`, each a file or a directory prefix, that ship.
  - `TEAM_DATA_CONTEXT_PATHS: list[str]` — same shape, never ships.
  - `classify_context_path(rel: str) -> str` — returns `"payload"`, `"team-data"`, or `"unclassified"`. `rel` is POSIX, relative to `context/`, e.g. `"tooling/board.md"`.
  - `unclassified_context_paths() -> list[str]` — every path under `context/` that classifies as `"unclassified"`, sorted.

  Task 3 consumes `PAYLOAD_CONTEXT_PATHS`.

**Why a manifest and not per-file frontmatter:** §11 of the spec left this open. Decided here: a manifest, following the existing `PLUGIN_TOOL_PATHS` pattern at `gather.py:123`. Per-file frontmatter would add it to a layer `context/kb-inbox/README.md` deliberately keeps frontmatter-light, and `boards/*/reference/**` alone is 31 files. Manifest drift is exactly what this task's bidirectional check catches.

- [ ] **Step 1: Write the failing test**

Create `tests/payload-classification/test_classification.py`:

```python
"""Regression test for the payload classification in tools/gather.py.

The predicate (design spec section 4.1.2): a file under context/ ships if a
default exists that is useful before /setup-awow runs. Contract files are
identical for every adopter; template files ship a working default that
/setup-awow tunes; team data has no meaningful default, and a generic stub is
worse than absence because commands can branch on absence.

Asserts three things: every path under context/ is classified, the two
manifests never overlap, and a representative sample lands in the right class.

Pure stdlib; no pytest, no network.

Run:  python3 tests/payload-classification/test_classification.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import importlib

gather = importlib.import_module("gather")

FAILURES = []

# Representative sample. Not exhaustive — the unclassified check covers the rest.
EXPECTED = {
    # contract: identical for everyone
    "tooling/boards/linear/reference/states.md": "payload",
    "tooling/boards/github-issues/reference/hierarchy.md": "payload",
    "tooling/activity-collection.md": "payload",
    "tooling/harnesses/codex.md": "payload",
    "knowledge-base/mining.md": "payload",
    "knowledge-base/synthesis.md": "payload",
    "kb-inbox/README.md": "payload",
    "retros/canon.md": "payload",
    "retros/anti-patterns.md": "payload",
    # template: ships a working default, /setup-awow tunes it
    "knowledge-base/mining-policy.md": "payload",
    "tooling/knowledge-base.md": "payload",
    "tooling/design-system.md": "payload",
    # team data: no useful default
    "team/mission.md": "team-data",
    "team/members.md": "team-data",
    "team/vision.md": "team-data",
    "team/conventions/REQUIRED/branches.md": "team-data",
    "team/style/prose.md": "team-data",
    "company/stakeholders.md": "team-data",
    "tooling/board.md": "team-data",
    "tooling/architecture.md": "team-data",
    "knowledge-base/glossary.md": "team-data",
    "kb-inbox/_synthesis-log.md": "team-data",
    "quarterly/INPUT.md": "team-data",
}


def main() -> int:
    for rel, want in sorted(EXPECTED.items()):
        got = gather.classify_context_path(rel)
        if got != want:
            FAILURES.append(f"classify({rel!r}) == {got!r}, expected {want!r}")

    # Every real path under context/ must be classified.
    stray = gather.unclassified_context_paths()
    if stray:
        FAILURES.append(
            "unclassified path(s) under context/ — add each to "
            "PAYLOAD_CONTEXT_PATHS or TEAM_DATA_CONTEXT_PATHS:\n    "
            + "\n    ".join(stray)
        )

    # The two manifests must be disjoint; an overlap makes classification
    # order-dependent and therefore silently wrong.
    overlap = set(gather.PAYLOAD_CONTEXT_PATHS) & set(gather.TEAM_DATA_CONTEXT_PATHS)
    if overlap:
        FAILURES.append(f"path(s) in both manifests: {sorted(overlap)}")

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Payload classification OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/payload-classification/test_classification.py`
Expected: FAIL with `AttributeError: module 'gather' has no attribute 'classify_context_path'`.

- [ ] **Step 3: Add the manifests and classifier**

In `tools/gather.py`, insert immediately after `PLUGIN_TOOL_PATHS` (ends line 130):

```python
CONTEXT_DIR = REPO_ROOT / "context"

# Which context/ files ship in the payload. The predicate (design spec 4.1.2):
# a file ships if a default exists that is useful before /setup-awow runs.
#   contract — identical for every adopter, nobody edits it
#   template — ships a working default that /setup-awow tunes
# Entries are POSIX paths relative to context/; a bare directory name covers
# its whole subtree. Addressed in prompt bodies as {AWOW_ROOT}/context/...
PAYLOAD_CONTEXT_PATHS = [
    "kb-inbox/README.md",                 # contract
    "knowledge-base/README.md",           # contract
    "knowledge-base/mining.md",           # contract
    "knowledge-base/synthesis.md",        # contract
    "retros/anti-patterns.md",            # contract
    "retros/canon.md",                    # contract
    "tooling/README.md",                  # contract
    "tooling/activity-collection.md",     # contract
    "tooling/boards",                     # contract (subtree, 35 files)
    "tooling/harnesses",                  # contract (subtree, 5 files)
    "knowledge-base/mining-policy.md",    # template — selectivity: 2
    "tooling/design-system.md",           # template — mode: absent
    "tooling/knowledge-base.md",          # template — default kb_root
]

# Team data: /setup-awow authors these per adopter. No useful default exists,
# and a generic stub is worse than absence — commands branch on absence
# (see the board fallback, design spec 4.2), but cannot branch on boilerplate.
TEAM_DATA_CONTEXT_PATHS = [
    "README.md",
    "company",
    "kb-inbox/_synthesis-log.md",
    "knowledge-base/architecture",
    "knowledge-base/decisions",
    "knowledge-base/glossary.md",
    "knowledge-base/patterns",
    "knowledge-base/runbooks",
    "quarterly",
    "team",
    "tooling/architecture.md",
    "tooling/board.md",
]


def _covers(entry: str, rel: str) -> bool:
    """True if manifest `entry` covers `rel` — exact file, or directory prefix."""
    return rel == entry or rel.startswith(entry + "/")


def classify_context_path(rel: str) -> str:
    """'payload', 'team-data', or 'unclassified' for a POSIX path relative to
    context/. Longest matching entry wins, so a file may be carved out of a
    directory-level classification."""
    best, verdict = -1, "unclassified"
    for entry in PAYLOAD_CONTEXT_PATHS:
        if _covers(entry, rel) and len(entry) > best:
            best, verdict = len(entry), "payload"
    for entry in TEAM_DATA_CONTEXT_PATHS:
        if _covers(entry, rel) and len(entry) > best:
            best, verdict = len(entry), "team-data"
    return verdict


def unclassified_context_paths() -> list[str]:
    """Every file under context/ that no manifest entry covers. A new file that
    nobody classified fails the build rather than silently not shipping."""
    if not CONTEXT_DIR.is_dir():
        return []
    stray = []
    for path in sorted(CONTEXT_DIR.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        rel = path.relative_to(CONTEXT_DIR).as_posix()
        if classify_context_path(rel) == "unclassified":
            stray.append(rel)
    return stray
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tests/payload-classification/test_classification.py`
Expected: `Payload classification OK.` and exit 0.

If it reports unclassified paths, add each to the correct manifest by applying the predicate — do not silence it by broadening a directory entry past what you have actually reviewed.

- [ ] **Step 5: Fail the build on an unclassified path**

In `tools/gather.py`, inside `main()`, immediately after the args are parsed and before any plan is built, add:

```python
    stray = unclassified_context_paths()
    if stray:
        print(
            "Unclassified path(s) under context/. Add each to "
            "PAYLOAD_CONTEXT_PATHS or TEAM_DATA_CONTEXT_PATHS in tools/gather.py "
            "(see the predicate in the docstring above them):",
            file=sys.stderr,
        )
        for rel in stray:
            print(f"  context/{rel}", file=sys.stderr)
        return 1
```

- [ ] **Step 6: Verify the guard fires, then clean up**

```bash
touch context/tooling/unclassified-probe.md
python tools/gather.py --check; echo "exit=$?"
```

Expected: exit=1 and `context/tooling/unclassified-probe.md` listed.

```bash
rm context/tooling/unclassified-probe.md
python tools/gather.py --check; echo "exit=$?"
```

Expected: exit=0.

- [ ] **Step 7: Wire the test into CI**

In `.github/workflows/ci.yml`, add after the `Path-token substitution` step:

```yaml
      - name: Payload classification
        run: python3 tests/payload-classification/test_classification.py
```

- [ ] **Step 8: Commit**

```bash
git add tools/gather.py tests/payload-classification/test_classification.py .github/workflows/ci.yml
git commit -m "Classify every context/ path as payload or team data behind a testable predicate, and fail the build on an unclassified file."
```

---

### Task 3: Ship the machinery into `dist/`

**Files:**
- Modify: `tools/gather.py:599-652` (`plan_plugin`), `tools/gather.py:516-540` (`plan_agent_skills`)
- Modify: `tests/payload-classification/test_classification.py` (add the bidirectional payload assertion)

**Interfaces:**
- Consumes: `PAYLOAD_CONTEXT_PATHS` and `classify_context_path` from Task 2; `render_plugin_body` / `render_agent_skills_body` from Task 1.
- Produces: `plan_context_payload(dest_root: Path, render) -> list[Stub]` — the shipped `context/` files as Stubs rooted at `dest_root/context/…`. Called by both `plan_plugin` (into `DIST_DIR`) and `plan_agent_skills` (into `AGENT_SKILLS_DIR`'s parent, so `../../context/…` resolves).

- [ ] **Step 1: Write the failing assertion**

In `tests/payload-classification/test_classification.py`, add before the `for f in FAILURES:` loop in `main()`:

```python
    # Bidirectional: the built payload must equal the payload manifest exactly.
    # An unshipped contract file fails as loudly as a shipped team-data file.
    dist_context = gather.DIST_DIR / "context"
    shipped = set()
    if dist_context.is_dir():
        for p in dist_context.rglob("*"):
            if p.is_file():
                shipped.add(p.relative_to(dist_context).as_posix())
    wanted = {
        p.relative_to(gather.CONTEXT_DIR).as_posix()
        for p in gather.CONTEXT_DIR.rglob("*")
        if p.is_file()
        and p.name != ".gitkeep"
        and gather.classify_context_path(
            p.relative_to(gather.CONTEXT_DIR).as_posix()
        ) == "payload"
    }
    for missing in sorted(wanted - shipped):
        FAILURES.append(f"classified payload but not shipped: context/{missing}")
    for extra in sorted(shipped - wanted):
        FAILURES.append(f"shipped but not classified payload: dist/context/{extra}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/payload-classification/test_classification.py`
Expected: FAIL listing ~48 `classified payload but not shipped:` lines — nothing under `context/` ships yet.

- [ ] **Step 3: Add the payload planner**

In `tools/gather.py`, insert immediately before `def plan_plugin()` (line 599):

```python
def plan_context_payload(dest_root: Path, render=render_plugin_body) -> list[Stub]:
    """The context/ machinery that ships, rendered for one channel. Commands
    reach these as {AWOW_ROOT}/context/... — {HUB} first so a vendored override
    wins, then {AWOW_ROOT}. See the predicate above PAYLOAD_CONTEXT_PATHS."""
    plans: list[Stub] = []
    for path in sorted(CONTEXT_DIR.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        rel = path.relative_to(CONTEXT_DIR).as_posix()
        if classify_context_path(rel) != "payload":
            continue
        plans.append(
            Stub(
                dest_root / "context" / rel,
                render(path.read_text()),
                path.stat().st_mode & 0o777,
            )
        )
    return plans
```

- [ ] **Step 4: Call it from both channels**

In `plan_plugin`, immediately before `return plans` (line 652):

```python
    plans.extend(plan_context_payload(DIST_DIR, render_plugin_body))
```

In `plan_agent_skills`, immediately before its `return`: the agent-skills channel resolves `{AWOW_ROOT}` to `../..`, which from `dist/agent-skills/<name>/SKILL.md` reaches `dist/`. So it shares the plugin channel's copy and needs no second one. Add this comment there instead of a second call:

```python
    # No second context/ copy: {AWOW_ROOT} renders to ../.. on this channel,
    # which from dist/agent-skills/<name>/ resolves to dist/ — the same files
    # plan_plugin already ships. Adding a copy here would double the payload
    # and desync the two.
```

- [ ] **Step 5: Build and verify**

```bash
python tools/gather.py
python3 tests/payload-classification/test_classification.py
```

Expected: classification test prints `Payload classification OK.`

```bash
git ls-files --others --exclude-standard dist/context | wc -l
```
Expected: `51`. (An earlier draft of this plan said 48; the manifest is right and the plan miscounted — 35 under `tooling/boards`, 5 under `tooling/harnesses`, 11 listed explicitly.)

```bash
ls dist/context/tooling/ dist/context/knowledge-base/
```
Expected: `activity-collection.md  boards  design-system.md  harnesses  knowledge-base.md  README.md` and `README.md  mining-policy.md  mining.md  synthesis.md`.

- [ ] **Step 6: Verify team data did NOT ship**

```bash
ls dist/context/team dist/context/company dist/context/quarterly 2>&1
test -e dist/context/tooling/board.md && echo "LEAK: board.md shipped" || echo "board.md correctly absent"
```
Expected: three `No such file or directory` errors, then `board.md correctly absent`.

- [ ] **Step 7: Verify the full build is clean**

Run: `python tools/gather.py --check && python tools/lint-paths.py && bash tests/harness/run-harness-tests.sh all`
Expected: all three pass.

- [ ] **Step 8: Commit**

```bash
git add tools/gather.py tests/payload-classification/test_classification.py dist/
git commit -m "Ship the classified context/ machinery into dist/ and assert the built payload matches the manifest in both directions."
```

---

### Task 4: Document the fourth token in `AGENTS.md`

**Files:**
- Modify: `.agents/AGENTS.md:16-24` ("Path tokens" section)

**Interfaces:**
- Consumes: the token from Task 1.
- Produces: the canonical prose definition every command body and Task 5's skill amendment refer to. No code.

- [ ] **Step 1: Replace the Path tokens section**

In `.agents/AGENTS.md`, replace the section spanning lines 16-24 with:

```markdown
## Path tokens

Prompt bodies never hardcode where context or tools live. Four tokens, resolved per channel:

- `{HUB}` — shared team context root (team, company, knowledge base, retros, board config).
- `{PROJECT}` — this project's context and drafts (mission, board-scope, do-not-propose, proposals/).
- `{AWOW_TOOLS}` — awow's runtime tool scripts.
- `{AWOW_ROOT}` — awow's own bundled machinery: the board references, the collection and mining contracts, the retro canon. Shipped with the plugin, identical for every team.

**In this repo (and any vendored install): `{HUB}` and `{PROJECT}` are the repo root, `{AWOW_TOOLS}` is `tools/`, `{AWOW_ROOT}` is the repo root.** So `{HUB}/context/tooling/board.md` means `context/tooling/board.md` here. In a plugin install `{AWOW_ROOT}` resolves into the payload instead, which is how a command reads awow's machinery without the adopter having vendored it.

**Reading machinery: `{HUB}` first, then `{AWOW_ROOT}`.** A team that has vendored and edited a contract must win over the shipped default, so read `{HUB}/context/<path>` and fall back to `{AWOW_ROOT}/context/<path>`. Team data — mission, members, conventions, style, `board.md`, `architecture.md` — is `{HUB}` only and has no fallback: absent means absent, and commands branch on that.

In a hub-connected spoke, the session reflex tells you where `{HUB}` resolves instead; if it is not resolvable, stop and say so — never guess a location or improvise conventions.
```

- [ ] **Step 2: Regenerate and verify**

Run: `python tools/gather.py && python tools/lint-paths.py`
Expected: lint passes. `.claude/CLAUDE.md`, `.github/copilot-instructions.md`, and root `AGENTS.md` are regenerated mirrors — expect them in `git status`.

- [ ] **Step 3: Commit**

```bash
git add .agents/AGENTS.md .claude/ .github/ AGENTS.md dist/
git commit -m "Document {AWOW_ROOT} as the fourth path token, with {HUB}-first precedence for machinery and no fallback for team data."
```

---

### Task 5: All three `using-awow` amendments

**Files:**
- Modify: `.agents/skills/using-awow/SKILL.md` — the "Where the paths point" section (around `:12-14`), and append two new sections

**Interfaces:**
- Consumes: Task 4's token definitions.
- Produces: the session-resident reflex text. `hooks/session-start` `cat`s this file wholesale into every session, so this is the only always-on behavioural surface. PR 2's board fallback and PR 5's `/update-context` both depend on the paragraphs added here; neither may edit this file again.

**Why all three land here:** the spec consolidates every `using-awow` edit into PR 1 so PRs 2 and 5 do not contend for one file. The board and `/update-context` paragraphs are inert until their machinery arrives — the first describes a fallback the commands do not yet implement, the second gates on a command that does not yet exist.

- [ ] **Step 1: Amend the path-resolution paragraph**

In `.agents/skills/using-awow/SKILL.md`, replace the paragraph under `## Where the paths point` (the one beginning "Paths here never hardcode a location — they use three tokens.") with:

```markdown
Paths here never hardcode a location — they use four tokens. **In this repo, and in any vendored or plugin install, `{HUB}` and `{PROJECT}` both resolve to the repo root and `{AWOW_TOOLS}` to awow's bundled tools** — so `{HUB}/context/tooling/board.md` is the board pointer read at that path under the root. `{AWOW_ROOT}` is awow's own machinery: the repo root here, the plugin payload in a plugin install.

**Machinery reads `{HUB}` first, then `{AWOW_ROOT}`** — a team that vendored and edited a contract beats the shipped default. Team data (mission, members, conventions, style, `board.md`, `architecture.md`) is `{HUB}` only.

In a hub-connected spoke, a hub pointer tells you where `{HUB}` resolves instead. If `{HUB}` is ever unresolvable, stop and say so — never guess a location or improvise a convention. **An absent file is not an unresolvable `{HUB}`.** A missing `board.md` means ask once (below), not halt.
```

- [ ] **Step 2: Append the board fallback section**

Append to the end of `.agents/skills/using-awow/SKILL.md`:

```markdown
## A missing board pointer is a question, not a stop

If `{HUB}/context/tooling/board.md` is absent, infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. If it cannot be inferred, ask once which board they use and how to reach it, and hold the answer for the session. Do not halt, and do not ask again. Offer `/setup-awow` Step 1 to make it durable.

Do not guess a board from a GitLab, Bitbucket, or Azure DevOps remote — those map to several products; ask. If there is no remote, or `gh` is absent or unauthenticated, ask and do not offer the `gh` path.

This covers an absent pointer only. A fatal auth failure on a data source still stops the run — never synthesise from a half-snapshot.
```

- [ ] **Step 3: Append the `/update-context` reflex**

Append to the end of `.agents/skills/using-awow/SKILL.md`:

```markdown
## Catch the rules people say in passing

When someone states how the team works — not what to do next — that is a convention with nowhere to live yet. Test it: after doing exactly what was asked, does anything remain that would change your behaviour in an unrelated session next week, and can you write it as "when X, do Y" without naming this file or this ticket? If yes to both, and they asserted it rather than floated it, and it binds the team rather than describing the world (facts belong in the knowledge base) — note it in one line inside the reply you were already writing.

Do not interrupt to ask. At a completion edge — a commit, a PR, "that's it for today" — offer the batch once via `/update-context`. Once per session, never mid-task. Scoping words ("here", "for this one", "just this time") mean it is not a convention. If `/update-context` is not available in this repo, stay silent. If they decline with "stop asking", write `.awow/no-context-prompt` and stay silent for good.
```

- [ ] **Step 4: Verify the reflex is inert**

The paragraph gates on `/update-context` existing. Confirm it does not yet:

```bash
test -e .agents/commands/update-context.md && echo "PRESENT (unexpected in PR 1)" || echo "absent — reflex correctly inert"
```
Expected: `absent — reflex correctly inert`.

- [ ] **Step 5: Verify the hook still reads the file cleanly**

```bash
python tools/gather.py
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/session-start | grep -c "Error reading" || true
```
Expected: `0`. (The `dist/`-path bug this hook has is PR 4's Layer 1 fix; from the repo root it resolves correctly.)

- [ ] **Step 6: Verify build and lint**

Run: `python tools/gather.py --check && python tools/lint-paths.py && python3 tests/gather-tokens/test_tokens.py`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add .agents/skills/using-awow/SKILL.md .claude/ .github/ dist/
git commit -m "Make every using-awow amendment in one change: four-token resolution, the ask-once board rule, and the inert /update-context reflex."
```

---

### Task 6: Point machinery reads at `{AWOW_ROOT}`

**Files:**
- Modify (each, at its `context/` references): `.agents/commands/daily-digest.md`, `daily-routine.md`, `kb-mine.md`, `kb-synthesize.md`, `process-workitem.md`, `process-retro.md`, `process-transcript.md`, `artifact.md`, `design-system.md`, `coaching-review.md`, `weekly-digest.md`, `daily-checkin.md`, `refinement-prep.md`, `solution-design-flow.md`, `project-plan.md`, `my-work.md`

**Interfaces:**
- Consumes: Task 1's token, Task 3's shipped files, Task 4's precedence rule.
- Produces: no new symbols. After this task every reference to a *shipped* contract reads `{HUB}` first and `{AWOW_ROOT}` second; every reference to team data still reads `{HUB}` only.

**The rule to apply, mechanically:** for each `{HUB}/context/<rel>` reference in a command body, run `classify_context_path("<rel>")`. If `"payload"`, rewrite to the two-step form. If `"team-data"`, leave it exactly as it is.

- [ ] **Step 1: List every reference and its class**

```bash
python3 - <<'PY'
import re, sys
from pathlib import Path
sys.path.insert(0, "tools")
import gather
pat = re.compile(r"\{HUB\}/context/([A-Za-z0-9._/-]+)")
for f in sorted(Path(".agents/commands").rglob("*.md")):
    for n, line in enumerate(f.read_text().splitlines(), 1):
        for m in pat.finditer(line):
            print(f"{gather.classify_context_path(m.group(1)):10} {f}:{n}  {m.group(0)}")
PY
```

Expected: a table. Every `payload` row is a rewrite site; every `team-data` row is left alone. Keep this output — Step 3 verifies against it.

- [ ] **Step 2: Rewrite one file and confirm the shape**

In `.agents/commands/kb-mine.md`, the Phase 1 reference to the collection contract currently reads:

```markdown
Run the shared collection step,
[`{HUB}/context/tooling/activity-collection.md`](../../context/tooling/activity-collection.md):
```

Replace with:

```markdown
Run the shared collection step — read `{HUB}/context/tooling/activity-collection.md`,
falling back to `{AWOW_ROOT}/context/tooling/activity-collection.md` (a vendored copy
wins over the shipped one):
```

The markdown link is dropped deliberately: `../../context/...` is a repo-relative path that resolves to nothing in a plugin install, and it is the literal defect this PR exists to fix. Prose reference only.

- [ ] **Step 3: Apply the same rewrite to every `payload` row**

Work through Step 1's output. For each `payload` row, replace the bare `{HUB}/context/<rel>` reference with `{HUB}/context/<rel>`, falling back to `{AWOW_ROOT}/context/<rel>`, and drop any accompanying relative markdown link.

Do not touch `team-data` rows — `board.md`, `mission.md`, `members.md`, `conventions/`, `style/`, `architecture.md`, `glossary.md`.

Then re-run Step 1's script and confirm every remaining bare `{HUB}/context/…` reference classifies `team-data`:

```bash
# after the rewrites — expect zero 'payload' rows without a sibling {AWOW_ROOT}
python3 - <<'PY'
import re, sys
from pathlib import Path
sys.path.insert(0, "tools")
import gather
pat = re.compile(r"\{HUB\}/context/([A-Za-z0-9._/-]+)")
bad = []
for f in sorted(Path(".agents/commands").rglob("*.md")):
    text = f.read_text()
    for m in pat.finditer(text):
        rel = m.group(1)
        if gather.classify_context_path(rel) != "payload":
            continue
        if f"{{AWOW_ROOT}}/context/{rel}" not in text:
            bad.append(f"{f}: {rel} is payload but has no {{AWOW_ROOT}} fallback")
print("\n".join(bad) if bad else "All payload references carry a fallback.")
PY
```
Expected: `All payload references carry a fallback.`

- [ ] **Step 4: Verify the rendered payload resolves**

```bash
python tools/gather.py
grep -rl 'CLAUDE_PLUGIN_ROOT/context/' dist/commands/ | head
grep -c '{AWOW_ROOT}' dist/commands/*.md | grep -v ':0' || echo "no unsubstituted tokens"
```
Expected: several `dist/commands/*.md` matched by the first grep; `no unsubstituted tokens` from the second.

```bash
grep -rc 'CLAUDE_PLUGIN_ROOT' dist/agent-skills/kb-mine/SKILL.md
```
Expected: `0` — Codex and Pi cannot resolve it.

- [ ] **Step 5: Verify build, lint, and both new tests**

Run:
```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/gather-tokens/test_tokens.py \
  && python3 tests/payload-classification/test_classification.py \
  && bash tests/harness/run-harness-tests.sh all
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add .agents/commands/ .claude/ .github/ dist/
git commit -m "Point every shipped-contract reference at {HUB} first and {AWOW_ROOT} second, leaving team-data reads on {HUB} alone."
```

---

### Task 7: Generate the Copilot payload

**Files:**
- Modify: `tools/gather.py` (`plan_plugin`, and `SURFACE_ROOTS` at `:667-673` if a new root is needed)
- Create (generated): `dist/.github/plugin/plugin.json`, `dist/.github/prompts/*.prompt.md`

**Interfaces:**
- Consumes: Task 1's `render_agent_skills_body`, the channel filter `is_vendored_channel` at `gather.py:424`.
- Produces: `plan_copilot_payload() -> list[Stub]` — the `dist/.github/` tree. Makes `copilot plugin marketplace add CauchyIO/awow` resolve, which PR 4's README documents.

**Why generated and not globbed:** copying `.github/**` would ship `ci.yml` — which would then run inside `awow-dist` against a repo with no `.agents/` — plus 35 dead pointer stubs linking `../.agents/…`, plus the six `vendored`-channel prompts, bypassing the channel filter.

- [ ] **Step 1: Confirm the current failure**

```bash
cat .claude-plugin/marketplace.json | python3 -c "import json,sys; print(json.load(sys.stdin)['plugins'][0]['source'])"
ls dist/.github 2>&1
```
Expected: `./dist`, then `No such file or directory` — this is the break.

- [ ] **Step 2: Read the existing Copilot manifest to copy its shape**

```bash
cat .github/plugin/plugin.json
```

Keep this output; Step 3 reuses its keys verbatim so the generated manifest stays byte-compatible with what Copilot already expects.

- [ ] **Step 3: Add the planner**

Copilot CLI resolves `${CLAUDE_PLUGIN_ROOT}`, so this channel uses `plugin_command_copy` (which renders via `render_plugin_body`) — not `render_agent_skills_body`, which exists for Codex and Pi because they cannot.

In `tools/gather.py`, insert immediately before `def plan_plugin()`:

```python
def plan_copilot_payload() -> list[Stub]:
    """dist/.github/ — the Copilot slice of the payload. Generated from
    .agents/, not copied from .github/: a copy would ship ci.yml (which would
    run inside awow-dist against a repo with no .agents/), the pointer stubs
    (whose ../.agents/ links resolve to nothing in a payload), and the
    vendored-channel prompts the filter is meant to exclude.

    Uses render_plugin_body via plugin_command_copy: Copilot CLI resolves
    ${CLAUDE_PLUGIN_ROOT}. Only Codex and Pi need render_agent_skills_body."""
    manifest = json.loads((GITHUB_DIR / "plugin" / "plugin.json").read_text())
    plans = [
        Stub(
            DIST_DIR / ".github" / "plugin" / "plugin.json",
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        )
    ]
    for source in sorted((AGENTS_DIR / "commands").rglob("*.md")):
        if is_skipped(source):
            continue
        text = source.read_text()
        if is_vendored_channel(text):
            continue
        plans.append(
            plugin_command_copy(
                DIST_DIR / ".github" / "prompts" / f"{source.stem}.prompt.md",
                source,
                text,
            )
        )
    return plans
```

- [ ] **Step 4: Call it from `plan_plugin`**

In `plan_plugin`, immediately before `return plans`:

```python
    plans.extend(plan_copilot_payload())
```

- [ ] **Step 5: Build and verify the channel filter held**

```bash
python tools/gather.py
ls dist/.github/prompts/ | wc -l
for f in awow-add awow-reset awow-status test-awow test-setup-awow update-awow; do
  test -e "dist/.github/prompts/$f.prompt.md" && echo "LEAK: $f"
done
echo "filter check done"
test -e dist/.github/workflows/ci.yml && echo "LEAK: ci.yml" || echo "ci.yml correctly absent"
```
Expected: `18` prompts (the non-vendored commands plus `awowify`), no `LEAK:` lines, `ci.yml correctly absent`.

Note `update-awow` still ships here — it is `channel: bootstrap` until PR 2 changes it to `vendored`. That is expected in PR 1.

- [ ] **Step 6: Verify the `.prompt.md` extension**

```bash
ls dist/.github/prompts/ | grep -vc '\.prompt\.md$'
```
Expected: `0`. VS Code's Copilot Chat silently ignores plain `.md` in that directory.

- [ ] **Step 7: Verify full build**

Run:
```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/payload-classification/test_classification.py \
  && bash tests/harness/run-harness-tests.sh all
```
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add tools/gather.py dist/
git commit -m "Generate dist/.github/ from .agents/ so the documented Copilot install resolves, without shipping CI, pointer stubs, or vendored prompts."
```

---

### Task 8: Fix `/setup-awow`'s payload path drift

**Files:**
- Modify: `.agents/commands/setup-awow.md` (Step 8 and Step 9 payload paths; the three dangling references)

**Interfaces:**
- Consumes: Task 3's shipped `context/` tree.
- Produces: nothing consumed by later tasks. Closes the last PR 1 item.

- [ ] **Step 1: Find the drift**

```bash
grep -n 'dist/\|\.agents/skills\|\.agents/commands\|input/PROPOSAL\|superpowers-integration-plan\|claudetracing' .agents/commands/setup-awow.md
```

Expected: Step 8 and Step 9 reference payload paths, plus three dangling references — `input/PROPOSAL.md`, `proposals/superpowers-integration-plan.md`, and `../claudetracing`.

- [ ] **Step 2: Verify each dangling reference really dangles**

```bash
ls input/ ; test -e proposals/superpowers-integration-plan.md && echo present || echo "absent"; test -d ../claudetracing && echo present || echo "absent"
```
Expected: `input/` holds only `README.md`; the other two print `absent`.

- [ ] **Step 3: Correct the payload paths**

Step 8 enumerates available skills and Step 9 enumerates commands. In a plugin install these live at `{AWOW_ROOT}/skills/` and `{AWOW_ROOT}/commands/` — not under `.agents/`, which the payload does not carry. Rewrite both to read `{HUB}/.agents/<kind>/` when present (a vendored install) and `{AWOW_ROOT}/<kind>/` otherwise.

- [ ] **Step 4: Remove the three dangling references**

Delete the citations to `input/PROPOSAL.md`, `proposals/superpowers-integration-plan.md`, and `../claudetracing`. Each is a pointer to a file that has never existed on `main`; keep the surrounding instruction and drop only the citation.

- [ ] **Step 5: Verify**

```bash
grep -c 'input/PROPOSAL\|superpowers-integration-plan\|claudetracing' .agents/commands/setup-awow.md
```
Expected: `0`.

Run: `python tools/gather.py --check && python tools/lint-paths.py`
Expected: both pass.

- [ ] **Step 6: Commit**

```bash
git add .agents/commands/setup-awow.md .claude/ .github/ dist/
git commit -m "Point /setup-awow at the real payload paths and drop three citations to files that never existed on main."
```

---

### Task 9: Ship the work-item archetypes

**Files:**
- Modify: `tools/gather.py` (add `plan_workitem_archetypes`, call from `plan_plugin`)
- Modify: `.agents/commands/process-workitem.md:11`
- Modify: `tests/payload-classification/test_classification.py`

**Interfaces:**
- Consumes: `{AWOW_ROOT}` from Task 1; `Stub` and `copy_stub` from the existing module.
- Produces: `plan_workitem_archetypes() -> list[Stub]` — the six archetype files at `dist/commands/_workitem-archetypes/`.

**Why this task exists.** Spec §4.1.4 lists `.agents/commands/_workitem-archetypes/** → dist/commands/_workitem-archetypes/` in the ships block, but Task 3's `plan_context_payload` walks `CONTEXT_DIR` only, and Task 6's rewrite rule matches `{HUB}/context/<rel>` only — this path is neither. `gather.py:132` excludes the directory via `SKIP_DIR_PARTS`, and `is_skipped` at `:328` is applied by `plan_plugin`'s command loop, so nothing ships it. `process-workitem.md:11` states the consequence outright: *"(vendored installs; not yet shipped in the plugin payload)"*. `/process-workitem` is one of the day-one six, so it would ship with a dangling archetype path and fail §9's acceptance criterion.

The `SKIP_DIR_PARTS` exclusion stays — archetypes are handlers, not commands, and must not become picker entries. They ship as data alongside the commands instead.

- [ ] **Step 1: Write the failing assertion**

In `tests/payload-classification/test_classification.py`, add before the `for f in FAILURES:` loop:

```python
    # The work-item archetypes are handlers, not commands: excluded from the
    # picker by SKIP_DIR_PARTS, but /process-workitem reads them at runtime, so
    # they must ship as data.
    arch_src = gather.AGENTS_DIR / "commands" / "_workitem-archetypes"
    arch_dst = gather.DIST_DIR / "commands" / "_workitem-archetypes"
    want_arch = {p.name for p in arch_src.glob("*.md")}
    got_arch = {p.name for p in arch_dst.glob("*.md")} if arch_dst.is_dir() else set()
    for missing in sorted(want_arch - got_arch):
        FAILURES.append(f"archetype not shipped: {missing}")
    for extra in sorted(got_arch - want_arch):
        FAILURES.append(f"archetype shipped but not in source: {extra}")
    # They must NOT become picker entries.
    if (gather.DIST_DIR / "commands" / "bugfix.md").exists():
        FAILURES.append("archetype leaked into dist/commands/ as a top-level command")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/payload-classification/test_classification.py`
Expected: FAIL with six `archetype not shipped:` lines — `bugfix.md`, `feature.md`, `incident.md`, `README.md`, `refactor.md`, `spike.md`.

- [ ] **Step 3: Add the planner**

In `tools/gather.py`, insert immediately before `def plan_plugin()`:

```python
def plan_workitem_archetypes() -> list[Stub]:
    """The archetype handlers /process-workitem dispatches to. SKIP_DIR_PARTS
    keeps them out of the command surface — they are handlers, not commands, and
    must not appear in the picker — but the payload still needs them on disk, so
    they ship as data under dist/commands/_workitem-archetypes/."""
    src = AGENTS_DIR / "commands" / "_workitem-archetypes"
    if not src.is_dir():
        return []
    return [
        Stub(
            DIST_DIR / "commands" / "_workitem-archetypes" / f.name,
            render_plugin_body(f.read_text()),
            f.stat().st_mode & 0o777,
        )
        for f in sorted(src.glob("*.md"))
    ]
```

- [ ] **Step 4: Call it from `plan_plugin`**

In `plan_plugin`, immediately before `return plans`:

```python
    plans.extend(plan_workitem_archetypes())
```

- [ ] **Step 5: Run test to verify it passes**

```bash
python tools/gather.py
python3 tests/payload-classification/test_classification.py
```
Expected: `Payload classification OK.`

```bash
ls dist/commands/_workitem-archetypes/
```
Expected: `README.md  bugfix.md  feature.md  incident.md  refactor.md  spike.md`

- [ ] **Step 6: Tokenise the reference in `process-workitem.md`**

In `.agents/commands/process-workitem.md`, line 11 currently reads:

> The work-specific rules (what to validate, what to check at the end) live in the archetype handlers under `.agents/commands/_workitem-archetypes/` (vendored installs; not yet shipped in the plugin payload).

Replace that sentence with:

> The work-specific rules (what to validate, what to check at the end) live in the archetype handlers — read `{HUB}/.agents/commands/_workitem-archetypes/` if this repo has vendored them, otherwise `{AWOW_ROOT}/commands/_workitem-archetypes/`.

Note the paths are deliberately asymmetric: a vendored repo keeps them under `.agents/commands/`, while the payload flattens `.agents/` away and they land under `commands/`. Both are correct for their install.

- [ ] **Step 7: Verify the rendered reference resolves**

```bash
python tools/gather.py
grep -o '\${CLAUDE_PLUGIN_ROOT}/commands/_workitem-archetypes/' dist/commands/process-workitem.md
test -e dist/commands/_workitem-archetypes/bugfix.md && echo "target exists" || echo "BROKEN"
grep -c 'not yet shipped in the plugin payload' .agents/commands/process-workitem.md
```
Expected: the substituted path, then `target exists`, then `0`.

- [ ] **Step 8: Verify build and lint**

Run: `python tools/gather.py --check && python tools/lint-paths.py && python3 tests/payload-classification/test_classification.py`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add tools/gather.py .agents/commands/process-workitem.md tests/payload-classification/test_classification.py .claude/ .github/ dist/
git commit -m "Ship the work-item archetypes as payload data and point /process-workitem at them, without letting handlers become picker entries."
```

---

### Task 10: Stop the token docs from substituting themselves

**Files:**
- Modify: `tools/gather.py` (`render_plugin_body`, `render_agent_skills_body`)
- Modify: `.agents/skills/using-awow/SKILL.md`, `.agents/AGENTS.md` (prose mentions of token names)
- Modify: `tests/gather-tokens/test_tokens.py`

**Interfaces:**
- Consumes: Task 1's substitution tables.
- Produces: an escape form. `{{TOKEN}}` in a source body renders as the literal `{TOKEN}` on every channel, so a file can *name* a token without *using* it.

**The defect.** `using-awow/SKILL.md` documents the path tokens and is itself rendered through the substitution table, so its explanation is substituted away. Verified on the built payload:

```
source:  `{AWOW_ROOT}` is awow's own machinery: the repo root here, …
Codex:   `../..` is awow's own machinery: the repo root here, …
Claude:  `${CLAUDE_PLUGIN_ROOT}` is awow's own machinery: the repo root here, …
```

`../..` is not "the repo root here" — the sentence is now false. Both channels ship **zero** surviving occurrences of `{AWOW_TOOLS}` or `{AWOW_ROOT}` in the one file whose purpose is to teach them, and `hooks/session-start` injects that file into every session. Pre-existing for `{AWOW_TOOLS}` (base `939fefd` has the same corruption); Task 4 and Task 5 doubled it by adding a second token to the same prose.

- [ ] **Step 1: Write the failing test**

Append to `main()` in `tests/gather-tokens/test_tokens.py`, before the `for f in FAILURES:` loop:

```python
    # A file must be able to NAME a token without USING it. {{X}} escapes to {X}.
    check(
        "plugin: {{AWOW_ROOT}} escapes to a literal",
        plugin("the {{AWOW_ROOT}} token points at the payload"),
        "the {AWOW_ROOT} token points at the payload",
    )
    check(
        "agent-skills: {{AWOW_TOOLS}} escapes to a literal",
        skills("the {{AWOW_TOOLS}} token points at tools/"),
        "the {AWOW_TOOLS} token points at tools/",
    )
    # Escaping must not disable real substitution in the same string.
    check(
        "plugin: escaped and live tokens coexist",
        plugin("{{AWOW_ROOT}} resolves to {AWOW_ROOT}"),
        "{AWOW_ROOT} resolves to ${CLAUDE_PLUGIN_ROOT}",
    )
    # The always-on reflex text must survive intact on both channels.
    reflex = (REPO_ROOT / ".agents" / "skills" / "using-awow" / "SKILL.md").read_text()
    for name, render in (("plugin", plugin), ("agent-skills", skills)):
        out = render(reflex)
        for tok in ("{AWOW_ROOT}", "{AWOW_TOOLS}", "{HUB}", "{PROJECT}"):
            if tok not in out:
                FAILURES.append(
                    f"{name}: using-awow/SKILL.md ships with no literal {tok} — "
                    "the file that teaches the tokens must still name them"
                )
```

Add near the top of the file, after the `sys.path.insert`:

```python
REPO_ROOT = Path(__file__).resolve().parents[2]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/gather-tokens/test_tokens.py`
Expected: FAIL — three escape checks plus several `ships with no literal` lines across both channels.

- [ ] **Step 3: Implement the escape**

In `tools/gather.py`, replace `render_plugin_body` and `render_agent_skills_body` with:

```python
# A prompt body must be able to NAME a token without USING it — using-awow and
# AGENTS.md both document the token vocabulary and are themselves rendered.
# {{TOKEN}} is the escape: protected before substitution, unwrapped after.
_ESCAPED_TOKEN = re.compile(r"\{\{([A-Z_]+)\}\}")
_ESCAPE_SENTINEL = "\x00"


def _render(text: str, substitutions: list[tuple[str, str]]) -> str:
    text = _ESCAPED_TOKEN.sub(
        lambda m: f"{_ESCAPE_SENTINEL}{m.group(1)}{_ESCAPE_SENTINEL}", text
    )
    for token, replacement in substitutions:
        text = text.replace(token, replacement)
    return re.sub(
        rf"{_ESCAPE_SENTINEL}([A-Z_]+){_ESCAPE_SENTINEL}", r"{\1}", text
    )


def render_plugin_body(text: str) -> str:
    return _render(text, PLUGIN_TOKEN_SUBSTITUTIONS)


def render_agent_skills_body(text: str) -> str:
    return _render(text, AGENT_SKILLS_TOKEN_SUBSTITUTIONS)
```

Confirm `import re` is already present at the top of `gather.py` — it is, used by `parse_frontmatter`.

- [ ] **Step 4: Escape the prose mentions**

In `.agents/skills/using-awow/SKILL.md`, under `## Where the paths point`, change every token name that is being *described* rather than *used* to the double-brace form. The four token names in the opening sentence and the `{AWOW_ROOT}` in the sentence after it become `{{HUB}}`, `{{PROJECT}}`, `{{AWOW_TOOLS}}`, `{{AWOW_ROOT}}`.

Leave genuine uses alone — `{HUB}/context/tooling/board.md` in the board-reflex section is a real path the agent must resolve, and must keep substituting.

Apply the same distinction to the "Path tokens" section of `.agents/AGENTS.md`: the four bullet definitions and the resolution paragraph name the tokens, so they escape; any example path that the agent should follow does not.

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 tests/gather-tokens/test_tokens.py`
Expected: `Path-token substitution OK.`

- [ ] **Step 6: Verify the shipped reflex text is now coherent**

```bash
python3 tools/gather.py
grep -o '`{AWOW_ROOT}` is awow.s own machinery' dist/skills/using-awow/SKILL.md
grep -o '`{AWOW_ROOT}` is awow.s own machinery' dist/agent-skills/using-awow/SKILL.md
grep -c 'CLAUDE_PLUGIN_ROOT' dist/agent-skills/using-awow/SKILL.md
```
Expected: the literal sentence on both channels, then `0` — the agent-skills copy must contain no `${CLAUDE_PLUGIN_ROOT}`, which Codex and Pi cannot resolve.

- [ ] **Step 7: Verify build and full chain**

Run:
```bash
python3 tools/gather.py --check \
  && python3 tools/lint-paths.py \
  && python3 tests/gather-tokens/test_tokens.py \
  && python3 tests/payload-classification/test_classification.py \
  && bash tests/harness/run-harness-tests.sh all
```
Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add tools/gather.py .agents/skills/using-awow/SKILL.md .agents/AGENTS.md tests/gather-tokens/test_tokens.py .claude/ .github/ dist/
git commit -m "Add a {{TOKEN}} escape so the files documenting the path tokens stop substituting their own explanations away."
```

---

### Task 11: Full-suite verification

**Files:** none modified.

**Interfaces:**
- Consumes: everything above.
- Produces: the evidence that PR 1 is complete.

- [ ] **Step 1: Run every check CI runs, plus the two new ones**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/gather-tokens/test_tokens.py \
  && python3 tests/payload-classification/test_classification.py \
  && bash tests/harness/run-harness-tests.sh all \
  && python3 tests/awow-lock/test_awow_lock.py \
  && python3 tests/hooks/test_lifecycle_seam_check.py
```
Expected: every one passes.

`test_awow_lock.py` builds two throwaway git repos and never reads `tools/awow.lock.json`, so a failure there is a **real regression in `awow_lock.py`**, not a stale-lockfile symptom. Do not wave it through as PR 2's problem — stop and report. (The committed lockfile being stale is a separate matter, and it is PR 2 Task 10's.)

- [ ] **Step 2: Confirm no team data leaked into the payload**

```bash
git ls-files dist/ | grep -E 'context/(team|company|quarterly)/|context/tooling/(board|architecture)\.md|setup-progress' | wc -l
```
Expected: `0`.

- [ ] **Step 3: Confirm the payload is addressable end to end**

```bash
grep -o '\${CLAUDE_PLUGIN_ROOT}/context/[a-z/-]*\.md' dist/commands/kb-mine.md | head -3
test -e "dist/context/tooling/activity-collection.md" && echo "target exists" || echo "BROKEN: target missing"
```
Expected: at least one substituted path, then `target exists`. This is the whole point of PR 1 — a rendered reference and a real file at the other end.

- [ ] **Step 4: Report**

Summarise: files changed, tests added, the three CI steps now guarding this, and anything deferred. Do not open a PR — that needs explicit approval.

---

## Self-Review

**Spec coverage.** §4.1.3 fourth token → Task 1. §4.1.2 predicate + §9 CI enforcement → Task 2. §4.1.4 ship list → Task 3. §4.1.3 dependent doc changes → Tasks 4, 5. Machinery rewrite → Task 6. §4.1.4 generated Copilot payload → Task 7. §10 PR 1 `/setup-awow` drift → Task 8. §4.1.4 archetype ship mapping → Task 9. Token-doc self-substitution (found during execution, pre-existing on `main`) → Task 10. §4.2 board fallback prose → Task 5 (the command-body half is PR 2, as sequenced). §4.6 reflex paragraph → Task 5.

**Deliberately not here:** `setup/**` does not ship and `/awowify` stays broken (§4.1.4, out of scope). `lint-paths.py` is unchanged (verified, §4.1.3). The `hooks/session-start` path fix is PR 4 Layer 1 — Task 5 Step 5 confirms the hook works from the repo root, which is all PR 1 needs.

**Gap found while writing:** `context/tooling/harnesses/**` (5 files) is contract machinery that the spec's §4.1.4 list never mentioned. Task 2 classifies it `payload` and Task 3 ships it. This is the omission class the bidirectional check exists to catch, and it argues the check earns its keep.

**Type consistency.** `classify_context_path(rel: str) -> str` returns exactly `"payload"` / `"team-data"` / `"unclassified"`, used with those spellings in Tasks 2, 3, and 6. `plan_context_payload(dest_root: Path, render) -> list[Stub]` and `plan_copilot_payload() -> list[Stub]` both return `Stub`, matching `plan_plugin`'s existing list. `Stub` is the existing dataclass at `gather.py:137` with fields `target`, `content`, `mode`.

**Placeholder scan.** One caught and fixed: Task 7 Step 3 originally had the implementer write an `if False` expression and then delete it, on the reasoning that forcing a deletion would make the renderer choice conscious. That is a placeholder wearing a justification — the skill forbids it, and the fix was to state the decision and its reason in the docstring instead. No others remain: every code step carries complete code, every command step carries expected output.

**Task boundaries.** Eleven tasks, each ending in a commit a reviewer could reject independently. Tasks 1–3 are the mechanism and could in principle be one commit, but a reviewer can meaningfully approve the token while rejecting the manifest shape, so they stay split. Task 11 adds no code — it exists because the six-command verification run is the deliverable that proves the PR, and folding it into Task 10 would let it be skipped.
