# PR 4 — Descriptions, the Hook Fix, LICENSE, and the README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the README the whole release exists for, and land the three things that have to be true before it can be written honestly: the SessionStart hook must resolve `using-awow` from the payload, every shipped command must advertise the situation it fires in, and the repo must carry the MIT licence its four manifests already declare.

**Architecture:** Three mechanical changes and one prose deliverable. (1) `hooks/session-start` tries the payload path `${PLUGIN_ROOT}/skills/using-awow/SKILL.md` before falling back to `.agents/`, with a harness check that invokes the `dist/` copy — the only invocation that exercises the plugin-install path. (2) `parse_frontmatter` is hardened to reject YAML block scalars before sixteen `description:` values are written into command frontmatter, because a block scalar would be stored as the literal string `>-` with `--check` green. (3) A new `autofire:` frontmatter field selects which commands are mirrored into `dist/skills/` so Claude Code can elect them from the situation instead of waiting to be typed. (4) `LICENSE`, the README rewrite from 1,869 words to ~660, and the docs sweep that keeps the rest of the repo from contradicting it.

**Tech Stack:** Python 3.12 stdlib only (no pytest, no third-party). Bash for the harness suite. `tools/gather.py` is the build; `.github/workflows/ci.yml` runs `gather.py --check`, `lint-paths.py`, and `tests/harness/run-harness-tests.sh all`.

**Spec:** `docs/superpowers/specs/2026-07-20-plugin-first-readme-design.md` §4.5, §5, §6, §7. This plan covers PR 4 of five.

## Global Constraints

- **PRs 1, 2, and 3 have landed.** `{AWOW_ROOT}` exists in both substitution tables; `PAYLOAD_CONTEXT_PATHS`, `TEAM_DATA_CONTEXT_PATHS`, `classify_context_path(rel) -> str`, and `unclassified_context_paths() -> list[str]` exist in `tools/gather.py`; `dist/context/` and `dist/.github/` ship; sixteen commands ship; `daily-routine` and `weekly-digest` are gone; telemetry is split out.
- **Do not edit `.agents/skills/using-awow/SKILL.md`.** PR 1 made all three amendments to it in one rewrite (four-token resolution, the ask-once board rule, the inert `/update-context` reflex). This PR reads that file through the hook and never writes it.
- **Python 3.12, stdlib only.** No pytest, no network. Tests are plain scripts run as `python3 tests/<dir>/test_<name>.py`, following `tests/awow-lock/test_awow_lock.py`. Every test module opens with a docstring ending in a `Run:` line.
- **Never edit generated files.** `.claude/`, the `.github/` pointer stubs, `dist/`, root `AGENTS.md`, `.claude/CLAUDE.md`, `.github/copilot-instructions.md` are `gather.py` output. Edit the source under `.agents/` (or `commands/`, or `tools/gather.py` itself for generated *text*) and re-run the gather.
- **After any `.agents/` edit, run `python tools/gather.py`** and commit the regenerated surfaces alongside the source change, or `--check` fails in CI.
- **Four channels exist, not two:** `vendored` (excluded from every payload), `telemetry` (added by PR 3 — builds into the `awow-telemetry` payload and is excluded from `dist/`, both its skills surface and its agent-skills surface), `bootstrap` (`setup-awow.md`, `update-awow.md` — these *do* ship), and the default, `both`. Never assume a binary. After PR 2, `update-awow` is `vendored`, so `setup-awow` is the only `bootstrap` file left. After PR 3 the field is read through one accessor, `declared_channel(text: str) -> str`, with `is_vendored_channel` and `is_telemetry_channel` as thin predicates over it — anything in this plan that asks "does this file ship in `dist/`?" means `declared_channel(text) not in {"vendored", "telemetry"}`.
- **Commit message style:** max 2 sentences.
- **Do not create PRs and do not push.** This plan produces commits on `feat/plugin-first-readme` only.

---

### Task 1: Layer 1 — fix the SessionStart hook

**Files:**
- Modify: `hooks/session-start:18-19` (the bootstrap read)
- Modify: `tests/harness/claude-code/wiring.sh` (append the regression check)

**Interfaces:**
- Consumes: nothing from earlier tasks. Depends on PR 1 having landed only in the sense that `dist/skills/using-awow/SKILL.md` already exists — it does today, and did before PR 1.
- Produces: no new symbols. A plugin-installed Claude session receives the real `using-awow` body instead of the literal string `Error reading using-awow skill`. Task 8 re-runs the check as part of full-suite verification.

**Why the `dist/skills/` copy and not `dist/agent-skills/`:** the two bodies differ by token substitution — `render_plugin_body` (`gather.py:402`) resolves `{AWOW_TOOLS}` to `${CLAUDE_PLUGIN_ROOT}/tools` and `{AWOW_ROOT}` to `${CLAUDE_PLUGIN_ROOT}`, while `render_agent_skills_body` (`gather.py:418`) resolves them to `../../tools` and `../..`. Injecting the agent-skills body into a Claude session gives it a tools path relative to a directory the session is not in.

- [ ] **Step 1: Reproduce the bug**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/dist" CLAUDE_PROJECT_DIR="$PWD" bash dist/hooks/session-start 2>&1 \
  | grep -o 'Error reading using-awow skill'
find dist/.agents -type f
```

Expected: the literal line `Error reading using-awow skill`, then a single path `dist/.agents/plugins/marketplace.json`. That one file is the whole of `dist/.agents/` — the hook is reading a directory that does not carry the skill.

- [ ] **Step 2: Add the regression check to the harness suite**

`tests/harness/claude-code/wiring.sh` currently defines `wiring()` with four assertions and a `gather --surface claude --check` guard. Replace the whole file with:

```bash
# tests/harness/claude-code/wiring.sh
wiring() {
  local r="$HARNESS_REPO_ROOT"
  file-exists "$r/.claude/CLAUDE.md"
  file-contains "$r/.claude/CLAUDE.md" 'GENERATED by tools/gather.py'
  file-exists "$r/.claude/commands/setup-awow.md"
  dir-exists "$r/.claude/skills"
  # the .claude surface must be in sync with .agents (drift guard)
  if ( cd "$r" && python3 tools/gather.py --surface claude --check >/dev/null 2>&1 ); then
    _record pass "gather --surface claude --check"
  else
    _record fail "gather --surface claude --check"
  fi

  # SessionStart injection, exercised as a plugin install. The hook derives
  # PLUGIN_ROOT from its own location (hooks/session-start:12-13), so only the
  # dist/ copy takes the payload path — running the repo-root copy passes even
  # when the payload is broken, which is why CI never caught this. `gather.py
  # --check` cannot catch it either: it proves dist/ matches its plan, not that
  # the plan is sufficient.
  file-exists "$r/dist/skills/using-awow/SKILL.md"
  local hook_out
  hook_out="$(mktemp)"
  ( cd "$r" && CLAUDE_PLUGIN_ROOT="$r/dist" CLAUDE_PROJECT_DIR="$r" \
      bash dist/hooks/session-start ) >"$hook_out" 2>&1
  file-not-contains "$hook_out" 'Error reading using-awow skill'
  # Positive assertion: the injected text is the skill body, not just an
  # absent error string. This H1 exists only in using-awow/SKILL.md.
  file-contains "$hook_out" 'You are working in an awow repo'
  rm -f "$hook_out"
}
```

- [ ] **Step 3: Run the harness suite to verify it fails**

Run: `bash tests/harness/run-harness-tests.sh claude-code`

Expected: the `claude-code/wiring` block prints a `CHECK fail file-not-contains …` line and a `CHECK fail file-contains … You are working in an awow repo` line, then:

```
────────
checks failed
```

and exit 1.

- [ ] **Step 4: Fix the hook**

In `hooks/session-start`, replace lines 18-19:

```bash
# Read the using-awow bootstrap from the plugin payload.
bootstrap_content=$(cat "${PLUGIN_ROOT}/.agents/skills/using-awow/SKILL.md" 2>&1 || echo "Error reading using-awow skill")
```

with:

```bash
# Read the using-awow bootstrap. Payload path first: a plugin install ships the
# skill at skills/using-awow/, and dist/.agents/ carries only marketplace.json —
# so the .agents-only read injected the literal error string into every
# plugin-installed session. The maintainer repo has no skills/ at its root and
# falls through to .agents/, which is why it always looked fine here.
#
# dist/skills/, never dist/agent-skills/: the two bodies differ by token
# substitution (render_plugin_body vs render_agent_skills_body), and the
# agent-skills body resolves {AWOW_TOOLS} to ../../tools — a path that means
# nothing to a Claude session.
bootstrap_content="Error reading using-awow skill"
for candidate in "${PLUGIN_ROOT}/skills/using-awow/SKILL.md" \
                 "${PLUGIN_ROOT}/.agents/skills/using-awow/SKILL.md"; do
    if [ -r "${candidate}" ]; then
        bootstrap_content=$(cat "${candidate}")
        break
    fi
done
```

The error string is kept as the initial value, so a genuinely missing skill still reports itself rather than injecting an empty reflex.

- [ ] **Step 5: Regenerate and verify the fix**

`dist/hooks/session-start` is a `copy_stub` of `hooks/session-start` (`gather.py:646-648`), so the payload copy only changes after a gather.

```bash
python tools/gather.py
bash tests/harness/run-harness-tests.sh all
```

Expected: the gather reports at least `dist/hooks/session-start` changed, then the harness driver ends with:

```
────────
all checks passed
```

- [ ] **Step 6: Verify the maintainer-repo path still resolves**

```bash
CLAUDE_PLUGIN_ROOT="$PWD" CLAUDE_PROJECT_DIR="$PWD" bash hooks/session-start 2>&1 \
  | grep -c 'Error reading using-awow skill'
```

Expected: `0`. From the repo root there is no `skills/` directory, so the loop falls through to `.agents/skills/using-awow/SKILL.md` and finds it. Both branches are now covered.

- [ ] **Step 7: Commit**

```bash
git add hooks/session-start tests/harness/claude-code/wiring.sh dist/
git commit -m "Read the using-awow bootstrap from the payload's skills/ before falling back to .agents/, so a plugin-installed session stops injecting the literal error string. Add a harness check that invokes dist/hooks/session-start, the only path that exercises a plugin install."
```

---

### Task 2: Reject block scalars in `parse_frontmatter`

**Files:**
- Modify: `tools/gather.py:145-171` (`parse_frontmatter`), plus five call sites that can name the offending file
- Create: `tests/command-frontmatter/test_frontmatter.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse_frontmatter(text: str, source: Path | None = None) -> tuple[dict[str, str], str]` — same return type as today, but raises `ValueError` on a YAML block-scalar indicator. The new second parameter is optional and keyword-compatible; existing single-argument calls keep working. Task 3 depends on this guard being in place *before* the descriptions land.

**Why a raise and not a skip:** silently skipping a block-scalar field puts the build back where it started — the description falls through to the H1 label and `--check` stays green. The failure has to be loud at build time, and it has to name the file, which is why the optional `source` parameter is added rather than a bare `ValueError`.

**Empirical basis:** `parse_frontmatter` is line-based. Its regex at `gather.py:160` is `^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$`, so `description: >-` yields `raw = ">-"`, which is neither empty nor `[`/`{`-prefixed and is therefore stored verbatim. Every stub, picker entry, and agent-skill trigger built from that field becomes the literal string `>-`. Verified against the code before writing this task.

- [ ] **Step 1: Confirm the defect by hand**

```bash
python3 -c "
import sys; sys.path.insert(0, 'tools')
import gather
print(repr(gather.parse_frontmatter('---\ndescription: >-\n  folded text\n---\n\n# Title\n')[0]))
"
```

Expected: `{'description': '>-'}`. That is the bug, in one line.

- [ ] **Step 2: Write the failing test**

Create `tests/command-frontmatter/test_frontmatter.py`:

```python
"""Regression test for the command frontmatter contract in tools/gather.py.

parse_frontmatter is line-based, so `description: >-` stores the literal
string '>-' — and every pointer stub, plugin picker entry, and agent-skill
trigger built from that field silently becomes ">-" while `gather.py --check`
stays green. At 30-45 words an implementer reaches for a block scalar by
reflex. Descriptions are single-line and double-quoted (design spec 4.5), and
the parser rejects block scalars rather than storing them.

Later tasks in this PR extend this module with the description and autofire
contracts; this revision covers the parser only.

Pure stdlib; no pytest, no network.

Run:  python3 tests/command-frontmatter/test_frontmatter.py
"""
import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

FAILURES = []

# Every YAML block-scalar shape: folded and literal, each with an optional
# indentation indicator and an optional chomping indicator.
BLOCK_SCALARS = [">", ">-", ">+", "|", "|-", "|+", ">2", "|2-", ">4+"]


def main() -> int:
    for indicator in BLOCK_SCALARS:
        doc = f"---\ndescription: {indicator}\n  folded text here\n---\n\n# Title\n"
        try:
            fields, _ = gather.parse_frontmatter(doc)
        except ValueError:
            continue
        FAILURES.append(
            f"parse_frontmatter accepted block scalar {indicator!r} and stored "
            f"description={fields.get('description')!r}"
        )

    # A single-line double-quoted description must still parse, unchanged.
    doc = '---\ndescription: "Use when the user asks for X."\nphase: seed\n---\n\n# Title\n'
    fields, body = gather.parse_frontmatter(doc)
    if fields.get("description") != "Use when the user asks for X.":
        FAILURES.append(
            f"single-line description mangled: {fields.get('description')!r}"
        )
    if fields.get("phase") != "seed":
        FAILURES.append(f"sibling field lost: {fields!r}")
    if body != "\n# Title\n":
        FAILURES.append(f"body mangled: {body!r}")

    # A bare `key:` introducing a list is not a block scalar and must survive
    # as the existing skip, not as a raise — every command uses this shape.
    doc = '---\nprerequisites:\n  - "Step 0 of /setup-awow complete"\n---\n\n# Title\n'
    try:
        fields, _ = gather.parse_frontmatter(doc)
        if "prerequisites" in fields:
            FAILURES.append(f"list key leaked into fields: {fields!r}")
    except ValueError as exc:
        FAILURES.append(f"list key wrongly rejected as a block scalar: {exc}")

    # The error must name the file, or a build failure sends the implementer
    # grepping 25 command files for a character they cannot see.
    doc = "---\ndescription: >-\n  folded\n---\n\n# Title\n"
    try:
        gather.parse_frontmatter(doc, REPO_ROOT / ".agents" / "commands" / "artifact.md")
    except ValueError as exc:
        if ".agents/commands/artifact.md" not in str(exc):
            FAILURES.append(f"error does not name the source file: {exc}")
    else:
        FAILURES.append("parse_frontmatter did not raise on a block scalar")

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Command frontmatter contract OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 tests/command-frontmatter/test_frontmatter.py`

Expected: FAIL with ten lines — one per entry in `BLOCK_SCALARS`, plus the final `parse_frontmatter did not raise on a block scalar`:

```
FAIL parse_frontmatter accepted block scalar '>' and stored description='>'
FAIL parse_frontmatter accepted block scalar '>-' and stored description='>-'
...
FAIL parse_frontmatter did not raise on a block scalar

10 failure(s).
```

- [ ] **Step 4: Harden the parser**

In `tools/gather.py`, replace lines 145-171 (from `_FM_DELIM = "---\n"` through the `return fields, body`) with:

```python
_FM_DELIM = "---\n"

# YAML block-scalar headers: folded (>) or literal (|), each with an optional
# indentation indicator and an optional chomping indicator.
_BLOCK_SCALAR = re.compile(r"^[|>][0-9]*[-+]?$")


def parse_frontmatter(
    text: str, source: Path | None = None
) -> tuple[dict[str, str], str]:
    """Return (scalar fields, body). Lists are ignored — we only need top-level
    strings like name, description, removes_pain.

    Block scalars are REJECTED, not ignored. This parser is line-based, so a
    `description: >-` would be stored as the literal two-character string '>-'
    and would propagate to every pointer stub, plugin picker entry, and
    agent-skill trigger built from it — with `--check` green the whole way,
    because the build faithfully mirrors the wrong value. Descriptions are
    single-line and double-quoted (design spec 4.5). Pass `source` so the
    failure names the file.
    """
    if not text.startswith(_FM_DELIM):
        return {}, text
    end = text.find("\n" + _FM_DELIM, len(_FM_DELIM))
    if end == -1:
        return {}, text
    fm_block = text[len(_FM_DELIM):end]
    body = text[end + len("\n" + _FM_DELIM):]
    fields: dict[str, str] = {}
    for line in fm_block.splitlines():
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$', line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if _BLOCK_SCALAR.match(raw):
            where = f"{source.relative_to(REPO_ROOT)}: " if source is not None else ""
            raise ValueError(
                f"{where}frontmatter field {key!r} uses the YAML block scalar "
                f"{raw!r}. tools/gather.py parses frontmatter line by line, so "
                f"the value would be stored as the literal string {raw!r} and "
                f"mirrored into every stub, picker entry, and skill trigger. "
                f"Write it as one double-quoted line instead."
            )
        if raw == "" or raw.startswith("[") or raw.startswith("{"):
            continue
        if (raw.startswith('"') and raw.endswith('"')) or (
            raw.startswith("'") and raw.endswith("'")
        ):
            raw = raw[1:-1]
        fields[key] = raw
    return fields, body
```

- [ ] **Step 5: Pass the source path at every call site that has one**

Five of the seven `parse_frontmatter` call sites hold a `Path` and can name the file. Make these five edits in `tools/gather.py`:

At `gen_command_stub` (currently line 218):
```python
    fields, body = parse_frontmatter(text, source)
```

At `plan_skills`, the directory branch (currently line 372):
```python
            fields, body = parse_frontmatter(text, skill_file)
```

At `plan_skills`, the single-file branch (currently line 378):
```python
            fields, body = parse_frontmatter(text, entry)
```

At `plugin_command_copy` (currently line 436):
```python
    fields, body = parse_frontmatter(text, source)
```

At `command_skill_stub` (currently line 502):
```python
    fields, body = parse_frontmatter(text, source)
```

Leave the two that hold no path unchanged: `is_vendored_channel` (line 427) and `skill_stubs` (line 480, which has `entry` but is reached only after `is_vendored_channel` has already parsed the same text — passing it there would produce a second, redundant message for the same file). `plan_commands` runs before `plan_plugin` in `main()`, and it routes every command file through `gen_command_stub`, so a bad command file is named on the first pass regardless.

- [ ] **Step 6: Run the test to verify it passes, and confirm nothing in the repo trips the guard**

```bash
python3 tests/command-frontmatter/test_frontmatter.py
python tools/gather.py --check
```

Expected: `Command frontmatter contract OK.` then `All stubs in sync.` No file under `.agents/` or `commands/` uses a block scalar today, so the guard is inert until Task 3 makes it load-bearing.

- [ ] **Step 7: Verify the guard fires on a real file, then revert**

```bash
python3 - <<'PY'
from pathlib import Path
p = Path(".agents/commands/artifact.md")
p.write_text(p.read_text().replace("phase: spread", "description: >-\n  probe\nphase: spread", 1))
PY
python tools/gather.py --check; echo "exit=$?"
git checkout .agents/commands/artifact.md
python tools/gather.py --check; echo "exit=$?"
```

Expected: the first `--check` ends in a traceback whose last line is

```
ValueError: .agents/commands/artifact.md: frontmatter field 'description' uses the YAML block scalar '>-'. tools/gather.py parses frontmatter line by line, so the value would be stored as the literal string '>-' and mirrored into every stub, picker entry, and skill trigger. Write it as one double-quoted line instead.
```

with `exit=1`. After the checkout, `All stubs in sync.` and `exit=0`.

- [ ] **Step 8: Wire the test into CI**

In `.github/workflows/ci.yml`, add a step to the `gather-check` job immediately after the `Path-token lint` step:

```yaml
      - name: Command frontmatter contract
        run: python3 tests/command-frontmatter/test_frontmatter.py
```

- [ ] **Step 9: Commit**

```bash
git add tools/gather.py tests/command-frontmatter/test_frontmatter.py .github/workflows/ci.yml
git commit -m "Reject YAML block scalars in parse_frontmatter instead of storing them as the literal string, and name the offending file. A folded description would otherwise reach every stub, picker entry, and skill trigger as \">-\" with --check green."
```

---

### Task 3: The sixteen descriptions

**Files:**
- Modify: `.agents/commands/{artifact,coaching-review,daily-checkin,daily-digest,design-system,kb-mine,kb-synthesize,my-work,process-retro,process-transcript,process-workitem,project-plan,refinement-prep,setup-awow,solution-design-flow}.md` (15 files)
- Modify: `commands/awowify.md` (1 file — `awowify` is not under `.agents/commands/`)
- Modify: `tests/command-frontmatter/test_frontmatter.py` (add the description contract)

**Interfaces:**
- Consumes: Task 2's hardened `parse_frontmatter`.
- Produces: an explicit `description:` field on all sixteen shipped commands. `command_description` (`gather.py:199-213`) prefers this field over the H1 fallback, and both `gen_command_stub` (`:219`) and `command_skill_stub` (`:504`) call it — so one edit per file propagates to four surfaces: `.claude/commands/*.md`, `.github/prompts/*.prompt.md`, `dist/commands/*.md`, and `dist/agent-skills/*/SKILL.md`. Task 4 adds a fifth (`dist/skills/*/SKILL.md`).

**Why `process-workitem`'s inner quotes changed:** §7 writes it as `or "let's pick up X"`. `parse_frontmatter` strips only the *outer* quote pair (`gather.py:166-170`) and never unescapes, while `gen_command_stub:224` and `command_skill_stub:505` wrap the value in double quotes with `"` → `\"`. A description containing a literal `"` therefore round-trips as `\"let's pick up X\"` — backslashes and all — into every stub. Typographic quotes (`“`/`”`) carry the same meaning and parse cleanly, so the description uses those. This is the only one of the sixteen affected; no other §7 value contains a double quote.

**Placement:** `description:` goes on the line immediately after the opening `---`, in every file, uniformly. `parse_frontmatter` is order-independent, so this is purely for readability — but a uniform rule makes the scripted insertion below correct by construction and makes a hand-edit that puts it elsewhere visibly inconsistent.

- [ ] **Step 1: Extend the test with the description contract**

In `tests/command-frontmatter/test_frontmatter.py`, add these two module-level constants immediately after `BLOCK_SCALARS`:

```python
# The sixteen shipped commands (design spec 7). awowify's source is the
# top-level commands/ dir; the other fifteen live under .agents/commands/.
SHIPPED = [
    "artifact", "awowify", "coaching-review", "daily-checkin", "daily-digest",
    "design-system", "kb-mine", "kb-synthesize", "my-work", "process-retro",
    "process-transcript", "process-workitem", "project-plan",
    "refinement-prep", "setup-awow", "solution-design-flow",
]


def source_for(name: str) -> Path:
    """The authoring file for a command. awowify is the one exception."""
    if name == "awowify":
        return REPO_ROOT / "commands" / f"{name}.md"
    return REPO_ROOT / ".agents" / "commands" / f"{name}.md"
```

Then add this block inside `main()`, immediately before the `for f in FAILURES:` loop:

```python
    # Every shipped command carries an explicit, single-line, situation-shaped
    # description. Without one, command_description falls back to the H1 — a
    # label ("gated pipeline for meeting transcripts"), not a trigger — and the
    # fallback is invisible in the built output.
    for name in SHIPPED:
        path = source_for(name)
        if not path.is_file():
            FAILURES.append(f"shipped command missing: {path.relative_to(REPO_ROOT)}")
            continue
        fields, _ = gather.parse_frontmatter(path.read_text(), path)
        desc = fields.get("description")
        if not desc:
            FAILURES.append(
                f"{name}: no explicit `description:` — gather would fall back "
                f"to the H1 label"
            )
            continue
        if '"' in desc or "\\" in desc:
            FAILURES.append(
                f"{name}: description contains a double quote or backslash. The "
                f"generated stubs wrap it in double quotes and parse_frontmatter "
                f"does not unescape, so it will not round-trip: {desc!r}"
            )
        if not desc.startswith("Use when"):
            FAILURES.append(
                f"{name}: a description names the situation the user is in — "
                f"start it “Use when”: {desc!r}"
            )
        if len(desc.split()) < 20:
            FAILURES.append(
                f"{name}: description is {len(desc.split())} words; a trigger "
                f"needs the concrete phrasings and artefacts that fire it "
                f"(target 30-45): {desc!r}"
            )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/command-frontmatter/test_frontmatter.py`

Expected: FAIL with sixteen lines of the form `FAIL <name>: no explicit \`description:\` — gather would fall back to the H1 label`, then `16 failure(s).`

- [ ] **Step 3: Write the descriptions**

Run this script from the repo root. It inserts one line after the opening `---` of each file, refuses to run twice, and refuses to touch a file whose frontmatter does not start where it expects.

```bash
python3 - <<'PY'
from pathlib import Path

DESCRIPTIONS = {
    "my-work": "Use when the user asks what they should work on, what is pending or waiting on them, or says they have lost track of the board and want to get oriented before starting a block of work.",
    "process-workitem": "Use when the user points at a board item — a ticket ID, issue link, or “let's pick up X” — and wants it carried from refinement through a planned code change to an opened PR.",
    "refinement-prep": "Use when the user has a feature brief, quarterly slidedeck, or board issue and wants it broken into right-sized stories before a refinement session, or asks to prep work for the next refinement.",
    "process-transcript": "Use when the user hands over a meeting transcript or recording notes (.vtt, .srt, pasted text), or asks to turn a meeting, standup, refinement, or stakeholder interview into board items.",
    "solution-design-flow": "Use when the user is weighing architectural or solution options, is about to lock a design decision, or points at a transcript of a design discussion — before the decision only exists in chat.",
    "artifact": "Use when the user asks for a deck, slides, a blog post, one-pager, or report as HTML or PDF — any styled document that should follow the team's house style instead of hand-written CSS.",
    "design-system": "Use when the user wants one house style for the HTML they generate — asks to stand up or adopt a design system, points at a site or brand to derive tokens from, or says every deck looks different.",
    "coaching-review": "Use when the user shares a transcript or recording of a coaching, pairing, mentoring, demo, or onboarding session and wants feedback on how the teaching went, not on what was decided.",
    "daily-digest": "Use when the user asks what the team shipped today or this week, wants a daily or weekly digest written up and raised as a PR, or says they have no idea what other people are working on.",
    "daily-checkin": "Use when the user recounts their day, points at a check-in note or voice memo, or wants the board to reflect today's work — end-of-day logging, standup prep, catching untracked work.",
    "project-plan": "Use when a design is locked and decomposed but nothing says what blocks what — the user asks for build order, sequencing, a delivery plan, or a critical path, or just finished /solution-design-flow.",
    "process-retro": "Use when the user points at or pastes a retrospective transcript or recording notes, or asks to turn a retro into named anti-patterns, owned actions, and diffs to their agent instructions.",
    "kb-mine": "Use when the user asks what's worth writing down from a day's work, wants to backfill knowledge-base candidates for a past day, or says hard-won insight is evaporating unrecorded.",
    "kb-synthesize": "Use when mined knowledge candidates are piling up unpromoted, or the user asks to drain the KB inbox, review staged candidates, or fold recent learnings into the durable knowledge base.",
    "setup-awow": "Use when a repo has awow files but no board wiring or team context yet, or the user asks how to get started with awow, connect their issue board, or resume an unfinished setup.",
    "awowify": "Use when the user wants awow's prompts vendored into this repo as editable, git-tracked files — adding awow to an existing codebase, or customising the commands rather than using them as shipped.",
}


def source_for(name):
    if name == "awowify":
        return Path("commands") / f"{name}.md"
    return Path(".agents/commands") / f"{name}.md"


for name, desc in sorted(DESCRIPTIONS.items()):
    path = source_for(name)
    text = path.read_text()
    assert text.startswith("---\n"), f"{path}: no frontmatter block at the top"
    assert "\ndescription:" not in text.split("\n---\n", 1)[0], f"{path}: already has a description"
    assert '"' not in desc and "\\" not in desc, f"{name}: description must not contain a double quote or backslash"
    path.write_text(f'---\ndescription: "{desc}"\n' + text[len("---\n"):])
    print(f"wrote description ({len(desc.split())} words) -> {path}")
PY
```

Expected: sixteen `wrote description (N words) -> <path>` lines, word counts between 30 and 40, no assertion errors.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/command-frontmatter/test_frontmatter.py`
Expected: `Command frontmatter contract OK.` and exit 0.

- [ ] **Step 5: Regenerate and confirm the descriptions reached all four surfaces**

```bash
python tools/gather.py
grep -h '^description:' .claude/commands/process-transcript.md \
                        .github/prompts/process-transcript.prompt.md \
                        dist/commands/process-transcript.md \
                        dist/agent-skills/process-transcript/SKILL.md
```

Expected: four identical lines, each reading

```
description: "Use when the user hands over a meeting transcript or recording notes (.vtt, .srt, pasted text), or asks to turn a meeting, standup, refinement, or stakeholder interview into board items."
```

- [ ] **Step 6: Confirm no `>-` leaked anywhere in the built output**

```bash
grep -rn 'description: ">-"\|description: ">"\|description: "|"' \
  .claude/ .github/prompts/ dist/ 2>/dev/null | wc -l
```

Expected: `0`. This is the failure mode Task 2 exists to prevent, asserted against the actual build rather than a synthetic document.

- [ ] **Step 7: Verify build and lint**

Run: `python tools/gather.py --check && python tools/lint-paths.py && bash tests/harness/run-harness-tests.sh all`
Expected: `All stubs in sync.`, the linter's pass line, and `all checks passed`.

- [ ] **Step 8: Commit**

```bash
git add .agents/commands/ commands/awowify.md tests/command-frontmatter/test_frontmatter.py .claude/ .github/ dist/
git commit -m "Give all sixteen shipped commands a situation-shaped description so they advertise the moment they fire in, not the mechanism they are. One field propagates to the picker, the Copilot prompts, and the Codex/Pi skill triggers."
```

---

### Task 4: `autofire` and the `dist/skills/` mirror

**Files:**
- Modify: `tools/gather.py` (add `is_autofire` after the channel predicates; extend the two command loops in `plan_plugin`) — anchored on literal text below, not line numbers, because PR 1 inserts ~75 lines above these points and PR 3 edits the same file
- Modify: `.agents/commands/{artifact,coaching-review,daily-checkin,process-retro,process-transcript,process-workitem,project-plan,refinement-prep,solution-design-flow}.md` (9 files)
- Modify: `.agents/AGENTS.md:26` (document the frontmatter contract)
- Modify: `tests/command-frontmatter/test_frontmatter.py` (add the autofire and mirror contracts)

**Interfaces:**
- Consumes: Task 3's `description:` fields (a mirrored skill with an H1-label description is worse than no mirror — the model elects on the description).
- Produces:
  - `is_autofire(text: str) -> bool` — `True` iff the frontmatter carries `autofire: true`. Mirrors the shape of `is_vendored_channel(text: str) -> bool`.
  - `dist/skills/<name>/SKILL.md` for each elected command, built by the existing `command_skill_stub(source, dest_root, render) -> Stub | None` at `gather.py:495` with `dest_root = DIST_DIR / "skills"` and the default `render_plugin_body`.

**Where the change actually goes.** §4.5 Layer 3 says "`gather.py:517` must also emit selected command mirrors into `dist/skills/`". Line 517 is inside `plan_agent_skills`, which owns `dist/agent-skills/` and already emits *every* command. `dist/skills/` is owned by `plan_plugin` (`:641-645`, currently skills only). The edit belongs in `plan_plugin`; the spec's line citation points at the wrong function. Recorded in the Self-Review.

**The frontmatter contract, reconciled.** After this task `artifact` exists three times, with three different frontmatters, and that is correct rather than a defect to be smoothed over:

| Rendering | Built by | Frontmatter | Consumer |
|---|---|---|---|
| `dist/commands/artifact.md` | `plugin_command_copy:430` | the authoring frontmatter verbatim — `description`, `autofire`, `phase`, `prerequisites`, `removes_pain`, `when-to-use` | the Claude Code `/` picker |
| `dist/skills/artifact/SKILL.md` | `command_skill_stub:495` | synthesised: `name` + `description` only | Claude Code skill election |
| `dist/agent-skills/artifact/SKILL.md` | `command_skill_stub:495` | synthesised: `name` + `description` only | Codex, Pi, Copilot skill election |

`autofire` survives into `dist/commands/` because that rendering is a full copy and `phase`/`prerequisites`/`removes_pain` already survive it — stripping one build-time key and not the others would be a new special case with no consumer asking for it. Both SKILL.md renderings drop it because they synthesise a two-field frontmatter from scratch and never carried authoring metadata. Step 5 writes this table into `.agents/AGENTS.md` so the next person adding a frontmatter key has a rule instead of three examples.

**The honest limitation, per §4.5.** `autofire` gates the Claude surface only. `plan_agent_skills` emits an agent-skill for *every* non-vendored command, so `my-work`, `daily-digest`, `kb-mine`, `kb-synthesize`, `setup-awow`, and `awowify` stay auto-fire candidates on Codex, Pi, and Copilot. The spec recommends accepting this rather than adding a suppression field, because suppression would make a command invisible to three of four harnesses' triggers. Accepted; no second field.

**`update-context` does not exist yet.** It arrives in PR 5. Selecting by frontmatter rather than a hardcoded list means an absent file contributes nothing and no code path special-cases it — that *is* the graceful handling. Step 1's test makes it explicit: `update-context` is the one name allowed to be absent, and if it ever appears it must carry `autofire: true`.

- [ ] **Step 1: Extend the test with the autofire and mirror contracts**

In `tests/command-frontmatter/test_frontmatter.py`, add these constants immediately after `SHIPPED`:

```python
# The autofire set (design spec 4.5 Layer 3). The rule, not the list: a command
# autofires unless a misfire is damage (consequential and hard to reverse) or
# noise (trigger too broad). Excluded on those grounds: my-work, daily-digest,
# kb-mine (too broad); setup-awow, awowify, design-system, kb-synthesize
# (consequential).
AUTOFIRE = [
    "artifact", "coaching-review", "daily-checkin", "process-retro",
    "process-transcript", "process-workitem", "project-plan",
    "refinement-prep", "solution-design-flow", "update-context",
]

# update-context ships in PR 5. Selecting by frontmatter rather than a
# hardcoded list is exactly what lets it be absent without a special case.
DEFERRED = {"update-context"}
```

Then add this block inside `main()`, immediately before the `for f in FAILURES:` loop:

```python
    # autofire is exactly the elected set — no drift in either direction.
    seen = set()
    for root in (REPO_ROOT / ".agents" / "commands", REPO_ROOT / "commands"):
        for path in sorted(root.glob("*.md")):
            if path.name in gather.SKIP_FILENAMES:
                continue
            if gather.is_autofire(path.read_text()):
                seen.add(path.stem)

    absent = {n for n in AUTOFIRE if not source_for(n).is_file()}
    if absent - DEFERRED:
        FAILURES.append(
            f"autofire names a command with no source file: {sorted(absent - DEFERRED)}"
        )
    want = {n for n in AUTOFIRE if n not in absent}
    for missing in sorted(want - seen):
        FAILURES.append(f"{missing}: elected for autofire but carries no `autofire: true`")
    for extra in sorted(seen - want):
        FAILURES.append(f"{extra}: carries `autofire: true` but is not in the elected set")

    # Each elected command is mirrored into dist/skills/, and nothing else is.
    # Without the mirror, autofire buys a better picker on Claude Code and
    # nothing more — the model cannot elect a slash command.
    for name in sorted(want):
        if not (gather.DIST_DIR / "skills" / name / "SKILL.md").is_file():
            FAILURES.append(f"{name}: autofire but no dist/skills/{name}/SKILL.md")
    for name in sorted(set(SHIPPED) - set(AUTOFIRE)):
        if (gather.DIST_DIR / "skills" / name / "SKILL.md").is_file():
            FAILURES.append(
                f"{name}: not elected for autofire but mirrored at "
                f"dist/skills/{name}/SKILL.md"
            )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/command-frontmatter/test_frontmatter.py`
Expected: FAIL with `AttributeError: module 'gather' has no attribute 'is_autofire'`.

- [ ] **Step 3: Add `is_autofire` to `gather.py`**

In `tools/gather.py`, insert immediately after the last of the channel predicates and immediately before `def plugin_command_copy(`. After PR 3 that predicate is `is_telemetry_channel`, so the insertion point is the line following:

```python
def is_telemetry_channel(text: str) -> bool:
    """channel: telemetry files build into dist-telemetry/ (the awow-telemetry
    plugin) and are excluded from dist/ — both its Claude skills surface and
    its Codex/Pi agent-skills surface."""
    return declared_channel(text) == "telemetry"
```

If PR 3's shape differs on landing, the anchor is still "after the last `def is_*_channel` and before `def plugin_command_copy`". Insert:

```python
def is_autofire(text: str) -> bool:
    """`autofire: true` mirrors a command into dist/skills/ on top of the /
    picker, so a Claude session can elect it from the situation the user is in
    rather than waiting to be typed. The selection rule (design spec 4.5
    Layer 3): a command autofires unless a misfire would be damage
    (consequential and hard to reverse) or noise (trigger too broad) — and
    noise is how the whole mechanism gets switched off.

    Claude-surface only. plan_agent_skills emits a skill for EVERY non-vendored
    command, so Codex, Pi, and Copilot see all of them regardless. That
    asymmetry is accepted: suppressing there would make a command invisible to
    three of the four harnesses' triggers.
    """
    return parse_frontmatter(text)[0].get("autofire") == "true"
```

- [ ] **Step 4: Emit the mirrors from `plan_plugin`**

In `tools/gather.py`, replace the two command loops in `plan_plugin`. PR 3 leaves them untouched (it moves skills only), so the old text is exactly:

```python
    commands_root = AGENTS_DIR / "commands"
    for source in sorted(commands_root.rglob("*.md")):
        if is_skipped(source):
            continue
        text = source.read_text()
        if is_vendored_channel(text):
            continue
        plans.append(plugin_command_copy(DIST_DIR / "commands" / source.name, source, text))
    if ROOT_COMMANDS_DIR.is_dir():
        for source in sorted(ROOT_COMMANDS_DIR.glob("*.md")):
            if source.name in SKIP_FILENAMES:
                continue
            text = source.read_text()
            if is_vendored_channel(text):
                continue
            plans.append(plugin_command_copy(DIST_DIR / "commands" / source.name, source, text))
```

It runs from the `commands_root = AGENTS_DIR / "commands"` assignment up to (not including) `    skills_root = AGENTS_DIR / "skills"`. Replace that block with:

```python
    commands_root = AGENTS_DIR / "commands"
    for source in sorted(commands_root.rglob("*.md")):
        if is_skipped(source):
            continue
        text = source.read_text()
        if is_vendored_channel(text):
            continue
        plans.append(plugin_command_copy(DIST_DIR / "commands" / source.name, source, text))
        if is_autofire(text):
            stub = command_skill_stub(source, DIST_DIR / "skills")
            if stub is not None:
                plans.append(stub)
    if ROOT_COMMANDS_DIR.is_dir():
        for source in sorted(ROOT_COMMANDS_DIR.glob("*.md")):
            if source.name in SKIP_FILENAMES:
                continue
            text = source.read_text()
            if is_vendored_channel(text):
                continue
            plans.append(plugin_command_copy(DIST_DIR / "commands" / source.name, source, text))
            if is_autofire(text):
                stub = command_skill_stub(source, DIST_DIR / "skills")
                if stub is not None:
                    plans.append(stub)
```

The `ROOT_COMMANDS_DIR` branch is a no-op today — `awowify` is explicit-invocation only — but the election rule lives in one place and applies to every command source, so a future root command is handled without a second decision.

`command_skill_stub` is called with its default `render=render_plugin_body`, which is what `dist/skills/` needs: `${CLAUDE_PLUGIN_ROOT}`-rooted tokens. `plan_agent_skills` keeps passing `render_agent_skills_body` for `dist/agent-skills/`.

- [ ] **Step 5: Mark the nine present commands**

Run this from the repo root:

```bash
python3 - <<'PY'
from pathlib import Path

AUTOFIRE = [
    "artifact", "coaching-review", "daily-checkin", "process-retro",
    "process-transcript", "process-workitem", "project-plan",
    "refinement-prep", "solution-design-flow",
]

for name in AUTOFIRE:
    path = Path(".agents/commands") / f"{name}.md"
    text = path.read_text()
    head = text.split("\n---\n", 1)[0]
    assert text.startswith("---\ndescription: "), f"{path}: description must be the first field (Task 3)"
    assert "\nautofire:" not in head, f"{path}: already marked"
    lines = text.split("\n")
    lines.insert(2, "autofire: true")
    path.write_text("\n".join(lines))
    print(f"autofire: true -> {path}")
PY
```

Expected: nine `autofire: true -> .agents/commands/<name>.md` lines. `update-context` is not in the list because its file does not exist; PR 5 writes the field when it writes the command.

- [ ] **Step 6: Build and verify the mirrors**

```bash
python tools/gather.py
ls dist/skills/
```

Expected: the four behavioural skills that survived PR 3's telemetry split — `architecture-aware-development`, `board-aware-development`, `user-story-template`, `using-awow` — plus the nine command mirrors: `artifact`, `coaching-review`, `daily-checkin`, `process-retro`, `process-transcript`, `process-workitem`, `project-plan`, `refinement-prep`, `solution-design-flow`. Thirteen entries, no name collisions — assumes PRs 1-3 landed and PR 5 has not. If PR 5 went first, `update-context` is a fourteenth; Task 8 Step 4 derives the number rather than asserting it, so both pass there.

```bash
python3 tests/command-frontmatter/test_frontmatter.py
```
Expected: `Command frontmatter contract OK.`

- [ ] **Step 7: Verify the mirror carries the plugin-channel tokens, not the agent-skills ones**

```bash
head -4 dist/skills/artifact/SKILL.md
grep -c 'CLAUDE_PLUGIN_ROOT' dist/skills/artifact/SKILL.md
grep -c 'CLAUDE_PLUGIN_ROOT' dist/agent-skills/artifact/SKILL.md
```

Expected: a four-line frontmatter of `---`, `name: artifact`, `description: "Use when the user asks for a deck, …"`, `---`; then a non-zero count for `dist/skills/` and `0` for `dist/agent-skills/`. The two renderings must differ exactly here — that difference is why Task 1's hook reads `dist/skills/`.

- [ ] **Step 8: Document the frontmatter contract**

In `.agents/AGENTS.md`, replace line 26 (the paragraph beginning `Command/skill frontmatter may carry a \`channel:\` field:`) with:

```markdown
Command and skill frontmatter carries three build-time fields. `channel:` — `vendored` files operate on the vendored install itself (gather, tests, adopter state) and are excluded from the plugin payload; `bootstrap` files ship in the payload but *create or update* the vendored tree (`/setup-awow`), so their literal repo paths are the deliverable and are exempt from the token lint. `description:` — one double-quoted line naming the situation the command fires in, never the mechanism it implements; it is the picker entry and the skill trigger on every harness. Never a YAML block scalar: the parser is line-based and would store `>-` verbatim. `autofire: true` — mirror this command into the Claude skill surface as well as the `/` picker, so the model can elect it from the situation. Omit it when a misfire would be damage (consequential and hard to reverse) or noise (a trigger broad enough to fire on ordinary conversation).

The three renderings of a command differ on purpose. `dist/commands/<name>.md` is a full copy and keeps the authoring frontmatter whole. `dist/skills/<name>/SKILL.md` and `dist/agent-skills/<name>/SKILL.md` synthesise a two-field frontmatter — `name` and `description` — over the body, and carry no authoring metadata. A new frontmatter key follows that rule: it survives the copy and it does not appear in either SKILL.md.
```

- [ ] **Step 9: Verify build, lint, and every test**

```bash
python tools/gather.py \
  && python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/command-frontmatter/test_frontmatter.py \
  && bash tests/harness/run-harness-tests.sh all
```
Expected: all pass. `.agents/AGENTS.md` is mirrored into `.claude/CLAUDE.md`, `.github/copilot-instructions.md`, `.github/AGENTS.md`, and root `AGENTS.md` — expect those in `git status`.

- [ ] **Step 10: Commit**

```bash
git add tools/gather.py .agents/ commands/ tests/command-frontmatter/test_frontmatter.py .claude/ .github/ AGENTS.md dist/
git commit -m "Add the autofire frontmatter field and mirror the nine elected commands into dist/skills/, so a Claude session can elect them from the situation rather than waiting to be typed. Document the three-rendering frontmatter contract in AGENTS.md."
```

---

### Task 5: `LICENSE`

**Files:**
- Create: `LICENSE`

**Interfaces:**
- Consumes: nothing.
- Produces: the file Task 6's README links to. Four manifests already declare MIT — `.claude-plugin/plugin.json:"license": "MIT"`, and the generated `dist/.codex-plugin/plugin.json`, `dist/package.json`, and `dist/.github/plugin/plugin.json` all inherit it via `src.get("license", "MIT")` at `gather.py:553`, `:590`, and PR 1's Copilot planner.

- [ ] **Step 1: Confirm it has never existed**

```bash
git log --all --oneline -- LICENSE | wc -l
test -e LICENSE && echo "present" || echo "absent"
```
Expected: `0`, then `absent`. The repo is public and four manifests claim MIT, which is the whole reason §6 lists this as a release blocker.

- [ ] **Step 2: Write it**

Create `LICENSE`:

```
MIT License

Copyright (c) 2026 Casper Lubbers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Verify it does not disturb the build**

```bash
python tools/gather.py --check
git ls-files --others --exclude-standard | grep -c '^LICENSE$'
```
Expected: `All stubs in sync.` then `1`. `LICENSE` sits at the repo root, which `find_orphans` only visits through `SURFACE_ROOTS`, so it is untouched by the gather.

- [ ] **Step 4: Commit**

```bash
git add LICENSE
git commit -m "Add the MIT licence the four plugin manifests have been declaring since v0.1."
```

---

### Task 6: The README

**Files:**
- Modify: `README.md` (full replacement — 1,869 words to 663)
- Modify: `.github/workflows/ci.yml` (add the word-count gate)

**Interfaces:**
- Consumes: Task 5's `LICENSE` (linked from the last section), Task 3's descriptions (the day-one six are described in the README's own voice, but the commands must actually advertise themselves for the "say what you want" claim on Copilot to hold), PR 1's generated `dist/.github/` (which is what makes the Copilot install block true), PR 2's trimmed command surface, PR 3's `awow-telemetry`.

**The README states no surface counts.** PR 5 adds a seventeenth command and never touches `README.md`, and §10 makes PR 5 independent of this PR — so any number written here is wrong under one of the two legal merge orders. Name what the thing does, not how many of them there are. The same reasoning is why Task 8's checks derive their counts instead of asserting them.
- Produces: no symbols. This is the deliverable the release exists for.

**Voice, lifted from §5.1 because the guides live in another repo:** practitioner energy, not vendor energy. Excited about the problem, not the tooling. Name the gap, then fill it. Lede under ten words. One idea per paragraph. Cut adverbs and hedges. Distinguish solid from rough inline, not in a footnote. Never open by restating the topic, never close by summarising. Max 1-2 bold elements. Real numbers, not a reflexive five or seven. Banned words: *ensures, enables, leverages, robust, seamless, cutting-edge, empower, simply, just, easily*. Framing is capability, not dependency. No Axios signposts (*"Why it matters:"*).

**Four things v1's inventory missed, all carried below:** the two install repos and why (`awow` vs `awow-dist`); `awow-telemetry` and that it is Claude-Code-only; prerequisites, because four of the six day-one commands read a board; and that Copilot has skills rather than slash commands.

**The deprecation note.** §5.3 says four commands vanish from the picker without naming them. Resolved here: `/daily-routine` and `/weekly-digest` (deleted, PR 2), `/update-awow` and `/project-manager` (`channel: vendored`, PR 2). `/test-setup-awow` is *not* one of the four — it was already `channel: vendored` and absent from `dist/commands/`, so deleting it changed the shipped count by zero (§4.4 says so explicitly).

- [ ] **Step 1: Record the baseline**

```bash
wc -w README.md
```
Expected: `1869 README.md`. This is the number §5.2 measures the target against, so the gate uses the same tool.

- [ ] **Step 2: Replace `README.md` in full**

Write exactly this, replacing the whole file:

````markdown
# awow — the Agentic Way of Working

Your agent keeps the board current. You keep the judgement.

Teams lose more time to coordination than to code. The board drifts from what people are actually doing, the decisions from the last design session sit in someone's chat history, and the retro produces actions nobody encodes anywhere. awow moves that upkeep into the agent session — the board update, the knowledge write, the transcript-to-tickets pass happen as a byproduct of the work rather than as a chore at the end of the week.

It installs as a plugin. No clone, no vendoring, no wizard before you get value.

## Install

### Claude Code

```
/plugin marketplace add CauchyIO/awow
/plugin install awow@awow
```

### GitHub Copilot CLI

```
copilot plugin marketplace add CauchyIO/awow
copilot plugin install awow
```

### Codex

```
codex plugin marketplace add https://github.com/CauchyIO/awow-dist
codex plugin add awow@awow
```

### Pi

```
pi install git:github.com/CauchyIO/awow-dist
```

Two repos, on purpose. `CauchyIO/awow` is the source, and Claude Code and Copilot resolve the built payload from a path inside it. Codex and Pi git-clone the plugin, so they need that payload published as its own repo — `CauchyIO/awow-dist`, generated from `awow` and never hand-edited.

A second plugin, `awow-telemetry@awow`, adds the session-trace skills: timelines, prompt-quality review, usage coaching. Claude Code only for now, because the publish topology gives Codex and Pi one plugin per repo.

## Then what

Six commands earn a line here. Each runs in a repo with no awow context at all:

- `/my-work` — regroups your board rows into *Needs you now / In flight / Waiting / Next up*.
- `/process-workitem` — a board item through refinement, a planned change, and an opened PR.
- `/refinement-prep` — a feature brief or a quarterly slidedeck broken into right-sized stories.
- `/process-transcript` — a meeting recording turned into board items, with attribution.
- `/solution-design-flow` — an architecture argument turned into a durable decision record. Never writes to the board.
- `/artifact` — a deck, one-pager, or report as styled HTML.

`/design-system` teaches `/artifact` your house style. `/coaching-review` reads a pairing or onboarding session and reports on how the teaching went, not on what was decided.

On Copilot these are **skills, not slash commands** — say what you want and the matching one fires.

## What changes in a session

The plugin installs a SessionStart hook, so every session opens with awow's operating reflex already loaded. Go to the board before starting anything with a discernible outcome; draft into `proposals/` before writing anywhere expensive; never make a silent state change. The agent carries the board-hygiene call itself instead of asking you whether to file a ticket.

## Prerequisites

- A board with hierarchy: Linear, Jira, Azure DevOps, or GitHub Issues. Four of the six commands above read it.
- A way to reach it — an authenticated `gh` for GitHub Issues, or the board's MCP server for the rest.
- One engineer who wants to try it.

## Going deeper

`/setup-awow` is optional. Run it when you want the agent working from your mission, your conventions, and your board's real state machine instead of a generic one. It writes those into `context/`, where every command reads them, and it is incremental and resumable — the board is the first step and the rest can wait.

Want the prompts as editable, git-tracked files in your own repo? Clone awow and run `setup/awowify.sh --target /path/to/your/repo`.

## Status

**v0.6.** Solid: the four installs, the command set, the session reflex, and the `dist/` build with its drift check in CI. Rough: `/awowify` runs from a clone, not as a plugin command, and `awow-telemetry` is Claude Code only.

Four commands left the picker this release. `/daily-routine` and `/weekly-digest` folded into `/daily-digest`, where the weekly window is now a parameter; `/update-awow` and `/project-manager` are vendored-install only. Plugin users update with `/plugin update awow`.

The visual tour is [`guides/index.html`](guides/index.html) — self-contained HTML, no agent session needed.

## License

MIT. See [`LICENSE`](LICENSE).
````

- [ ] **Step 3: Verify the word count**

```bash
wc -w README.md
```
Expected: `663 README.md` — under the 750 gate, at the ~700 target §5.2 sets.

- [ ] **Step 4: Verify every §5.3 deletion actually happened**

```bash
grep -c 'Use this template\|retro-reports\|starter-owned\|team-owned\|pointer stub\|input/' README.md
grep -c 'clone-and-go\|uv run\|install.sh' README.md
```

Expected: `0` from both. The first covers the ownership table (`:99-109`), the pointer-stub essay (`:84-93`), the *"Use this template"* recommendation (`:111`, against a repo with `is_template: false`), `retro-reports/` (`:67`, never existed), and the `input/` citation (`:139`, where `input/` holds one README). The second covers the clone-and-go lede and the `uv` bootstrap.

- [ ] **Step 5: Verify every §5.2 required item is present**

```bash
for s in 'CauchyIO/awow-dist' 'awow-telemetry' 'Prerequisites' 'skills, not slash commands' \
         '/plugin install awow@awow' 'copilot plugin install awow' 'codex plugin add awow@awow' \
         'pi install git:github.com/CauchyIO/awow-dist' 'LICENSE'; do
  grep -q -- "$s" README.md && echo "ok   $s" || echo "MISSING  $s"
done
```
Expected: nine `ok` lines, no `MISSING`.

- [ ] **Step 6: Verify the ban list**

```bash
grep -inE '\b(ensures?|enables?|leverages?|robust|seamless|cutting-edge|empowers?|simply|easily)\b' README.md
```
Expected: no output. (`just` is excluded from this regex on purpose — it appears in no draft line, and the word has non-hedging senses that would make a permanent gate noisy.)

- [ ] **Step 7: Add the word-count gate to CI**

In `.github/workflows/ci.yml`, add a step to the `gather-check` job after `Command frontmatter contract`:

```yaml
      - name: README size gate
        run: |
          words=$(wc -w < README.md)
          echo "README.md: $words words (gate: 750)"
          test "$words" -le 750
```

- [ ] **Step 8: Commit**

```bash
git add README.md .github/workflows/ci.yml
git commit -m "Rewrite the README plugin-first: four harness installs, the day-one six, and what a session actually does — 663 words, down from 1869. Gate it at 750 in CI so it cannot creep back."
```

---

### Task 7: The docs sweep

**Files:**
- Modify: `SETUP.md` (the lede, Step 0's framing, and the `input/PROPOSAL.md` citation at `:45`)
- Modify: `guides/index.html:638` (the culled `/cross-team-view`), `:543` (the card title)
- Modify: `guides/guide-setup-and-two-harnesses.html:6`, `:8`, `:114`, `:116` (the two-harnesses framing)
- Modify: `tools/gather.py` (the generated `dist/README.md` text, inside `plan_plugin`'s opening `plans = [...]` literal) — anchored on literal text in Step 5, not a line number, since Task 4 has already shifted this function within this same PR

**Interfaces:**
- Consumes: Task 6's README, which these files must stop contradicting.
- Produces: no symbols. Closes §5.3's wider sweep.

**Scope call.** §5.3 also flags `.agents/AGENTS.md` as "references deleted commands". Verified: it does not. The only affected line is `:26`, whose `bootstrap` example names `/update-awow` — a file PR 2 moved to `channel: vendored`. Task 4 Step 8 already rewrote that line and dropped the stale example, so there is nothing left here. Recorded in the Self-Review.

**What is deliberately not swept.** `guides/guide-standardise-reporting.html` is built end to end on `/weekly-digest` (live) and `/cross-team-view` (planned) — ten references across the file, including its own frontmatter comment at `:10` and a dedicated section at `:275`. PR 2 deleted `/weekly-digest`, which makes this guide materially wrong, but repairing it is a guide rewrite rather than a line edit and it is not in §5.3's list. It does not block the README, which links only `guides/index.html`. Flagged in the Self-Review as a follow-up rather than smuggled into this PR.

Deferring the repair does not defer disclosing it: the release notes must say that `guide-standardise-reporting.html` still describes `/weekly-digest`, a command this release deletes, so a reader who opens that guide is not silently misled while the rewrite waits. Task 8 Step 6 carries it into the report.

- [ ] **Step 1: Fix `SETUP.md`'s framing and its dangling citation**

Replace line 1 of `SETUP.md` (`# /setup-awow — long-form walkthrough`) and the blank line after it with:

```markdown
# /setup-awow — long-form walkthrough

`/setup-awow` is optional. Install the awow plugin and the commands work against your board with no setup at all — see the README. Run the wizard when you want the agent working from your mission, your conventions, and your board's real state machine rather than a generic one.

Step 0 below is the installer, and it applies to a clone or a vendored install only. A plugin install has no `.venv/` and no pointer stubs to generate; start at Step 1.
```

Then replace line 45:

```markdown
The single highest-leverage sentence the team writes. Per the blog (§3 of `input/PROPOSAL.md`'s anchor), a vague mission produces vague agent behaviour across every ceremony.
```

with:

```markdown
The single highest-leverage sentence the team writes. A vague mission produces vague agent behaviour across every ceremony, because every command that reads mission inherits it.
```

`input/PROPOSAL.md` has never been committed — `input/` holds one `README.md`.

- [ ] **Step 2: Verify the citation is gone and nothing else dangles**

```bash
grep -c 'input/PROPOSAL' SETUP.md
ls input/
```
Expected: `0`, then `README.md` alone.

- [ ] **Step 3: Drop the culled `/cross-team-view` from `guides/index.html`**

At `guides/index.html:638`, remove the trailing sentence of the card description. The line currently ends:

```html
services distil up, projects route down. Reads alongside the digests&rsquo; planned <code>/cross-team-view</code>.</p>
```

Change it to:

```html
services distil up, projects route down.</p>
```

`/cross-team-view` was culled from `main` before this release; the index is the entry point every reader hits first and must not advertise a command that does not exist.

- [ ] **Step 4: Retitle the setup guide**

The guide's second half is about the two *pointer-stub surfaces* (`.claude/` and `.github/`), which is still accurate and still two. What went stale is the implication that awow targets two harnesses when it now installs on four. Retitle in place — do not rename the file, which is linked from `guides/index.html:278`, `:283`, `:417`, `:542`, and `:545`.

In `guides/guide-setup-and-two-harnesses.html`:

Line 6:
```html
<title>Setup &amp; the pointer-stub model &mdash; what a new adopter hits first</title>
```

Line 8 (the comment banner):
```html
  AWOW GUIDE — setup and the pointer-stub model
```

Line 114:
```html
    <h1>Setup &amp; the pointer-stub model</h1>
```

Line 116, replace the first sentence of the standfirst so the whole paragraph reads:
```html
    <p style="font-size:0.85rem;color:var(--text-3);margin:8px 0 0;">Two halves. The wizard turns a clone or a vendored install into a configured repo, one approved step at a time &mdash; a plugin install needs none of it. The pointer-stub model lets Claude Code and GitHub Copilot share a single source of truth without drift. Board specifics live in the companion <code>guide-board-and-mcp.html</code>.</p>
```

And in `guides/index.html:543`, the card title:
```html
        <div class="c-top"><span class="c-title">Setup &amp; the pointer-stub model</span><span class="c-pill">New</span></div>
```

- [ ] **Step 5: Say what `dist/README.md` is**

`dist/README.md` is the payload's front page — the first thing a visitor to `CauchyIO/awow-dist` reads — and it currently calls the payload "the installable Claude Code plugin", which is three-quarters wrong now. It is generated text inside `plan_plugin`, so edit `tools/gather.py`, not the file.

In `tools/gather.py`, replace the whole `Stub(DIST_DIR / "README.md", …)` entry in `plan_plugin`'s opening `plans = [...]` literal. The old text is exactly:

```python
        Stub(
            DIST_DIR / "README.md",
            f"{GENERATED_MARKER} — DO NOT EDIT. -->\n\n"
            "# dist/ — built awow plugin payload\n\n"
            "This directory is the installable Claude Code plugin, built by "
            "`python tools/gather.py --surface plugin` from `.agents/` (plus "
            "`hooks/`, the legacy `commands/`, and a runtime slice of `tools/`). "
            "`.claude-plugin/marketplace.json` points installers here so the "
            "maintainer workspace (`meta/`, `context/`, guides, tests) never "
            "ships to adopters.\n\n"
            "Do not edit files in this directory — edit the source and re-run "
            "the gather. Any file here that the build did not plan is deleted "
            "on the next run.\n",
        ),
```

Replace it with:

```python
        Stub(
            DIST_DIR / "README.md",
            f"{GENERATED_MARKER} — DO NOT EDIT. -->\n\n"
            "# dist/ — the built awow payload\n\n"
            "awow is the Agentic Way of Working: board-first delivery "
            "workflows for coding agents. This directory is the built "
            "plugin, and it serves four harnesses from one tree — "
            "`commands/` and `skills/` for Claude Code, `agent-skills/` for "
            "Codex and Pi, `.github/` for GitHub Copilot, plus `hooks/`, a "
            "runtime slice of `tools/`, and the `context/` machinery the "
            "commands read.\n\n"
            "Install instructions live in the source repo's README: "
            "https://github.com/CauchyIO/awow\n\n"
            "Built by `python tools/gather.py --surface plugin` from "
            "`.agents/`, so the maintainer workspace (`meta/`, guides, "
            "tests, team context) never ships. Do not edit anything here — "
            "edit the source and re-run the gather. Any file the build did "
            "not plan is deleted on the next run.\n",
        ),
```

- [ ] **Step 6: Regenerate and verify**

```bash
python tools/gather.py
head -6 dist/README.md
grep -c 'installable Claude Code plugin' dist/README.md
```
Expected: the new heading `# dist/ — the built awow payload`, then `0`.

- [ ] **Step 7: Verify build, lint, and the harness suite**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && bash tests/harness/run-harness-tests.sh all
```
Expected: `All stubs in sync.`, the linter's pass line, and `all checks passed`.

- [ ] **Step 8: Commit**

```bash
git add SETUP.md guides/index.html guides/guide-setup-and-two-harnesses.html tools/gather.py dist/
git commit -m "Sweep the docs the new README contradicts: SETUP.md is framed as optional and loses its citation to a file that never existed, the guides drop the culled /cross-team-view and the two-harness framing, and dist/README.md says what the payload actually is."
```

---

### Task 8: Full-suite verification

**Files:** none modified.

**Interfaces:**
- Consumes: everything above.
- Produces: the evidence that PR 4 is complete.

- [ ] **Step 1: Run every check CI runs, plus the three test modules**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/gather-tokens/test_tokens.py \
  && python3 tests/payload-classification/test_classification.py \
  && python3 tests/command-frontmatter/test_frontmatter.py \
  && bash tests/harness/run-harness-tests.sh all \
  && python3 tests/awow-lock/test_awow_lock.py \
  && python3 tests/hooks/test_lifecycle_seam_check.py
```

Expected: every one passes — `All stubs in sync.`, the linter's pass line, `Path-token substitution OK.`, `Payload classification OK.`, `Command frontmatter contract OK.`, `all checks passed`, and the two remaining suites' own pass lines.

- [ ] **Step 2: Prove the hook fix end to end**

```bash
CLAUDE_PLUGIN_ROOT="$PWD/dist" CLAUDE_PROJECT_DIR="$PWD" bash dist/hooks/session-start \
  | grep -c 'Error reading using-awow skill'
CLAUDE_PLUGIN_ROOT="$PWD" CLAUDE_PROJECT_DIR="$PWD" bash hooks/session-start \
  | grep -c 'Error reading using-awow skill'
```
Expected: `0` from both — the payload path and the maintainer-repo fallback each resolve. Before this PR the first returned `1`.

- [ ] **Step 3: Prove the description propagation**

```bash
for f in dist/commands/*.md; do
  grep -q '^description: "Use when' "$f" || echo "NO TRIGGER DESCRIPTION: $f"
done
echo "description sweep done"
python3 - <<'PY'
import sys
sys.path.insert(0, "tools")
import gather

def ships(text):
    return gather.declared_channel(text) not in {"vendored", "telemetry"}

expected = set()
for src in sorted((gather.AGENTS_DIR / "commands").rglob("*.md")):
    if not gather.is_skipped(src) and ships(src.read_text()):
        expected.add(src.stem)
for src in sorted(gather.ROOT_COMMANDS_DIR.glob("*.md")):
    if src.name not in gather.SKIP_FILENAMES and ships(src.read_text()):
        expected.add(src.stem)

actual = {p.stem for p in (gather.DIST_DIR / "commands").glob("*.md")}
if expected == actual:
    print(f"commands OK ({len(actual)})")
else:
    print(f"commands MISMATCH missing={sorted(expected - actual)} extra={sorted(actual - expected)}")
    sys.exit(1)
PY
```

Expected: `description sweep done` with no `NO TRIGGER DESCRIPTION` lines, then `commands OK (16)`.

The count is derived from the authoring dirs rather than hardcoded, because it is only 16 if PR 5 has *not* landed — §10 makes PR 5 independent and lets it land either side of this one. With PR 5 in, `update-context` ships too and the same check prints `commands OK (17)`. Either is correct; a mismatch between `.agents/commands/` + `commands/` and `dist/commands/` is not.

- [ ] **Step 4: Prove the autofire mirror**

```bash
for n in artifact coaching-review daily-checkin process-retro process-transcript \
         process-workitem project-plan refinement-prep solution-design-flow; do
  test -f "dist/skills/$n/SKILL.md" || echo "MISSING MIRROR: $n"
done
for n in my-work daily-digest design-system kb-mine kb-synthesize setup-awow awowify; do
  test -e "dist/skills/$n" && echo "UNWANTED MIRROR: $n"
done
echo "mirror sweep done"
python3 - <<'PY'
import sys
sys.path.insert(0, "tools")
import gather

def ships(text):
    return gather.declared_channel(text) not in {"vendored", "telemetry"}

expected = set()
# the behavioural skills that survive PR 3's telemetry split
for entry in sorted((gather.AGENTS_DIR / "skills").iterdir()):
    if entry.name in gather.SKIP_FILENAMES:
        continue
    skill_md = entry / "SKILL.md" if entry.is_dir() else entry
    if skill_md.suffix != ".md" or not skill_md.is_file():
        continue
    if ships(skill_md.read_text()):
        expected.add(entry.name if entry.is_dir() else entry.stem)
# plus exactly one mirror per autofire command
sources = [(sorted((gather.AGENTS_DIR / "commands").rglob("*.md")), gather.is_skipped),
           (sorted(gather.ROOT_COMMANDS_DIR.glob("*.md")),
            lambda p: p.name in gather.SKIP_FILENAMES)]
for paths, skip in sources:
    for src in paths:
        if skip(src):
            continue
        text = src.read_text()
        if ships(text) and gather.is_autofire(text):
            expected.add(src.stem)

actual = {p.name for p in (gather.DIST_DIR / "skills").iterdir() if p.is_dir()}
if expected == actual:
    print(f"skills OK ({len(actual)})")
else:
    print(f"skills MISMATCH missing={sorted(expected - actual)} extra={sorted(actual - expected)}")
    sys.exit(1)
PY
```
Expected: `mirror sweep done` with no `MISSING` or `UNWANTED` lines, then `skills OK (13)` — the four surviving behavioural skills plus the nine mirrors.

Derived for the same reason as Step 3: 13 holds only while PR 5 is out. With `update-context` landed the same check prints `skills OK (14)`, and is equally correct. The two name loops above stay hardcoded on purpose — they assert *which* commands were elected, which is this PR's decision and must not drift. The total is the part that legitimately moves.

- [ ] **Step 5: Prove the release blockers are closed**

```bash
test -f LICENSE && head -3 LICENSE
wc -w README.md
grep -c 'Use this template' README.md
```
Expected: `MIT License`, a blank line, `Copyright (c) 2026 Casper Lubbers`; then `663 README.md`; then `0`.

- [ ] **Step 6: Report**

Summarise: files changed, the test module added, the two CI steps now guarding this, and the two items deliberately deferred (`guides/guide-standardise-reporting.html`, and `update-context`'s `autofire` marking which PR 5 owns). Name the first as a **release-note item**, not just a backlog one — it describes `/weekly-digest`, which this release deletes. Do not open a PR and do not push — both need explicit approval.

---

## Self-Review

**Spec coverage.** §4.5 Layer 1 (hook) → Task 1. §4.5 Layer 2 (descriptions) and its format constraint → Tasks 2 and 3. §4.5 Layer 3 (`autofire`, the `dist/skills/` mirror, the frontmatter reconciliation) → Task 4. §6 `LICENSE` → Task 5. §5.1/§5.2 README, and §5.3's README deletions → Task 6. §5.3's wider docs sweep → Task 7. §9's CI additions → the wiring steps in Tasks 2, 4, and 6, plus Task 8's full run. §7's sixteen descriptions → Task 3 Step 3, verbatim except the one quote change documented there.

**Three things the spec is wrong about, verified against the code.**

1. **§4.5 Layer 3's line citation is wrong.** It says "`gather.py:517` must also emit selected command mirrors into `dist/skills/`". Line 517 is the docstring of `plan_agent_skills`, which owns `dist/agent-skills/` and already emits every command. `dist/skills/` is owned by `plan_plugin` (`:641-645`). Following the citation literally would put the `dist/skills/` mirror inside the function that builds a different directory. Task 4 Step 4 edits `plan_plugin`'s two command loops instead, anchored on the literal old text rather than a line range — PR 1 and PR 3 both shift this file, and Task 4 shifts Task 7 within this PR.
2. **§5.3's claim that "`.agents/AGENTS.md` references deleted commands" is overstated to the point of being wrong.** `grep -n 'daily-routine\|weekly-digest\|test-setup-awow\|cross-team-view\|project-manager\|update-awow' .agents/AGENTS.md` returns exactly one hit: line 26, and it names `/update-awow` as an example of the `bootstrap` channel — a file PR 2 reclassifies as `vendored`, which is a stale *example*, not a reference to a deleted command. It is real and it is fixed (Task 4 Step 8), but an implementer hunting a list of deleted-command references would find nothing and conclude the sweep was already done.
3. **§5.3's sweep list omits the one guide the release actually breaks.** It names `guides/index.html:638` (one line) and `guide-setup-and-two-harnesses.html` (a title), but not `guides/guide-standardise-reporting.html`, which has ten references to `/weekly-digest` and `/cross-team-view` including its own frontmatter comment at `:10` and a dedicated section at `:275`. PR 2 deletes `/weekly-digest`, so this guide describes a live command that no longer exists. `guides/program-portfolio-view.html:653` names `/cross-team-view` too. Task 7 states this as an explicit deferral rather than silently expanding scope: it is a guide rewrite, not a line edit, and the README links only `guides/index.html`.

**Decisions the spec left open, resolved here.**

- **How `parse_frontmatter` "rejects" a block scalar** — it raises `ValueError`, and takes a new optional `source: Path | None = None` so the message names the file. Skipping the field would put the build straight back on the H1 fallback with `--check` green, which is the exact failure the guard exists to prevent. Five of the seven call sites hold a `Path` and pass it; the two that do not are documented in Task 2 Step 5.
- **`process-workitem`'s inner double quotes.** §7 writes `"let's pick up X"`. Written literally, `gen_command_stub:224` escapes it to `\"` and `parse_frontmatter:166-170` never unescapes, so the backslashes reach every stub. Resolved with typographic quotes (U+201C/U+201D) — same meaning, parses clean. It is the only one of the sixteen affected.
- **Whether `autofire` survives into `dist/commands/*.md`.** Yes. That rendering is a full copy and already carries `phase`, `prerequisites`, `removes_pain`, and `when-to-use`; stripping one build-time key and not the others is a special case with no consumer asking for it. Both SKILL.md renderings drop it because they synthesise their frontmatter from scratch. Task 4's table and the `.agents/AGENTS.md` paragraph make this a rule rather than three examples.
- **Where the frontmatter test lives** — `tests/command-frontmatter/`, a third new directory beside PR 1's `tests/gather-tokens/` and `tests/payload-classification/`, wired into `ci.yml` the same way. Built up across three tasks (parser, descriptions, autofire) so each task's failing test is its own.
- **How the README word count is measured** — `wc -w README.md`, matching the `1869` §5.2 quotes as the baseline. The gate is `test "$words" -le 750` in CI. Measured result: 663.
- **Which four commands "vanish from the picker."** §5.3 does not name them. Resolved: `/daily-routine`, `/weekly-digest`, `/update-awow`, `/project-manager`. `/test-setup-awow` is not one — §4.4 says deleting it changes the shipped count by zero because it was already `vendored`.
- **Whether to rename `guide-setup-and-two-harnesses.html`.** No. Five hrefs in `index.html` point at it and the filename is not visible to a reader mid-guide. Retitled in place; the body's actual subject (two pointer-stub surfaces) stays accurate.
- **What positive assertion the hook test makes.** `You are working in an awow repo` — the H1 of `using-awow/SKILL.md`, and a string the hook's own wrapper does not contain (the wrapper says "a repo governed by awow"). Asserting only the *absence* of the error string would pass against an empty injection.

**Type consistency.** `parse_frontmatter(text: str, source: Path | None = None) -> tuple[dict[str, str], str]` — the added parameter is optional and positional-compatible, so the two unchanged call sites keep working. `is_autofire(text: str) -> bool` mirrors `is_vendored_channel(text: str) -> bool` at `gather.py:424` exactly, including reading through `parse_frontmatter` without a source. `command_skill_stub(source: Path, dest_root: Path, render=render_plugin_body) -> Stub | None` is called unchanged with a new `dest_root`; its `None` return (vendored commands) is guarded at both new call sites even though `is_vendored_channel` has already filtered them — the signature permits `None` and the guard costs one line. `Stub` is the existing frozen dataclass at `gather.py:136-140` with fields `target: Path`, `content: str`, `mode: int | None`.

**Placeholder scan.** None remain. Every code step carries complete code; every command step states its literal expected output, including the exact 663-word count and the exact `ValueError` message text. The two surface counts are the exception: Task 8 Steps 3 and 4 derive `commands OK (16)` and `skills OK (13)` from `.agents/commands/` + `commands/` + `.agents/skills/` minus the `vendored` and `telemetry` channels, rather than hardcoding them, because §10 lets PR 5 land on either side of this one and would make them 17 and 14. Stating the number as expected output keeps it useful context; deriving the check keeps it true regardless of merge order. One near-miss caught while writing: Task 3 originally said "insert `description:` into each of the sixteen files" and left the mechanics to the implementer, which would have produced sixteen hand-edits with sixteen chances to fumble a typographic dash. Replaced with an explicit dictionary and an insertion script that asserts its own preconditions — the descriptions are then data, checked by the test rather than by inspection.

**Task boundaries.** Eight tasks, each ending in a commit a reviewer could reject independently. Tasks 2, 3, and 4 could be one commit — they are one feature — but a reviewer can meaningfully approve the parser guard while rejecting a description's wording, or approve the descriptions while rejecting the autofire election, so they stay split. Task 8 adds no code; it exists because the five-way verification run is what proves the PR, and folding it into Task 7 would let it be skipped.

**Merge gate, restated.** §10: PR 4 does not merge until PRs 1-3 are on `main`, and `awow-dist` syncs before or with PR 4, never after — the README sends Codex and Pi users to `CauchyIO/awow-dist`, and a stale payload there makes two of the four install blocks lies. PR 5 is independent; if it slips, `update-context` stays absent, Task 4's test tolerates it by design, and the reflex paragraph PR 1 landed stays inert.
