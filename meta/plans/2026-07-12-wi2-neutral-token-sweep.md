# WI-1 residue + WI-2 neutral-token sweep — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every prompt body in `.agents/` reference context and tools through harness-neutral tokens (`{HUB}`, `{PROJECT}`, `{AWOW_TOOLS}`), substituted or taught per distribution channel, with a CI drift guard so neither stale `dist/` nor bare paths can land again.

**Architecture:** `.agents/` stays the single source of truth. Prompt bodies carry three neutral tokens; the vendored channel *teaches* resolution in `.agents/AGENTS.md` (all three resolve to the repo root — behaviour identical to today), while the plugin emitter in `tools/gather.py` *substitutes* `{AWOW_TOOLS}` → `${CLAUDE_PLUGIN_ROOT}/tools` at build time and ships a resolution preamble for `{HUB}`/`{PROJECT}` (fully wired to the connector in WI-3/4). Commands that only make sense vendored (they operate on `.agents/` itself) are marked `channel: vendored` and drop out of the plugin payload. A path lint blocks bare `context/`|`tools/`|`proposals/` references in non-vendored bodies.

**Tech Stack:** Python 3 stdlib only (matches `gather.py`), GitHub Actions, bash.

**Base:** branch `feat/hub-spoke-design` (stacked on `origin/main`; WI-1's emitter + `dist/` + marketplace repoint already landed on main — verified `--check` clean 2026-07-12).

## Global Constraints

- Spec: `meta/proposals/hub-and-spoke-design.md` (accepted, MVP-validated 5/5).
- No new dependencies; tools are stdlib-only like `gather.py`.
- No external website links in committed files.
- `dist/` is wholly generated — never hand-edit; every change lands via `python tools/gather.py`.
- Every payload-visible change bumps `.claude-plugin/plugin.json` version (this PR: 0.4.0 → 0.5.0).
- Fail loud: no silent fallbacks anywhere; no `except Exception` with silent pass.
- Commit messages ≤ 2 sentences.

## Token glossary (locked here, used verbatim everywhere)

| Token | Meaning | Vendored resolution (taught) | Plugin resolution |
|---|---|---|---|
| `{HUB}` | shared team context root | repo root (`context/` is local) | connector → hub clone (taught by reflex; WI-3) |
| `{PROJECT}` | project context + drafts root | repo root | spoke repo root |
| `{AWOW_TOOLS}` | runtime tool scripts | `tools/` | `${CLAUDE_PLUGIN_ROOT}/tools` (build-time substitution) |

Classification rule (from spec §5): `context/**` → `{HUB}` except per-project files (`context/mission.md`, `context/board-scope.md`, `context/do-not-propose.md`, `context/architecture/**`) → `{PROJECT}`; `proposals/**` → `{PROJECT}`; `tools/<runtime allowlist>` → `{AWOW_TOOLS}`; `tools/<maintainer scripts>` stay literal but only inside `channel: vendored` files.

---

### Task 1: CI drift guard (WI-1 residue)

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: a `gather-check` job later tasks extend with the `lint-paths` step (Task 5 modifies this file).

- [ ] **Step 1: Write the workflow**

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:

jobs:
  gather-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Generated surfaces in sync (.claude/, .github/, dist/)
        run: python tools/gather.py --check
```

- [ ] **Step 2: Verify locally**

Run: `python tools/gather.py --check`
Expected: `All stubs in sync.` exit 0.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI running gather.py --check so stale generated surfaces (incl. dist/) cannot land."
```

### Task 2: Token convention + channel frontmatter, taught in `.agents/AGENTS.md`

**Files:**
- Modify: `.agents/AGENTS.md` (add one section after its path-conventions material; read the file first and place it where conventions live)

**Interfaces:**
- Produces: the section heading `## Path tokens` and the `channel:` frontmatter key, consumed verbatim by Tasks 3–5.

- [ ] **Step 1: Add the section**

```markdown
## Path tokens

Prompt bodies never hardcode where context or tools live. Three tokens, resolved per channel:

- `{HUB}` — shared team context root (team, company, knowledge base, retros, board config).
- `{PROJECT}` — this project's context and drafts (mission, board-scope, do-not-propose, proposals/).
- `{AWOW_TOOLS}` — awow's runtime tool scripts.

**In this repo (and any vendored install): `{HUB}` and `{PROJECT}` are the repo root, `{AWOW_TOOLS}` is `tools/`.** So `{HUB}/context/tooling/board.md` means `context/tooling/board.md` here. In a hub-connected spoke, the session reflex tells you where `{HUB}` resolves instead; if it is not resolvable, stop and say so — never guess a location or improvise conventions.

Command/skill frontmatter may carry `channel: vendored` — such files operate on the vendored install itself (gather, setup, update) and are excluded from the plugin payload.
```

- [ ] **Step 2: Regenerate stubs and commit**

```bash
python tools/gather.py
git add -A
git commit -m "Document the {HUB}/{PROJECT}/{AWOW_TOOLS} path tokens and the channel: frontmatter in .agents/AGENTS.md."
```

### Task 3: Classify and sweep all 253 references

**Files:**
- Modify: every file under `.agents/commands/` and `.agents/skills/` with a bare path reference (inventory: 253 matches of `(context|tools|proposals)/…`).

**Interfaces:**
- Consumes: token glossary + classification rule from the header (verbatim).
- Produces: zero bare references outside `channel: vendored` files — the exact invariant Task 5's lint enforces.

- [ ] **Step 1: Mark vendored-channel commands**

Add `channel: vendored` to frontmatter of the commands that operate on the vendored install itself: `setup-awow.md`, `awow-add.md`, `awow-reset.md`, `update-awow.md`, `test-setup-awow.md`, `awowify` (root `commands/awowify.md`), plus any file whose body must reference `tools/gather.py`/`.agents/` literally (decide per file while sweeping; when in doubt the reference should be a token, not the file vendored).

- [ ] **Step 2: Scripted rewrite, then hand-review**

Apply in order (first match wins), via `perl -pi` over `.agents/commands/*.md .agents/skills/**/*.md` **excluding** `channel: vendored` files:

| Pattern | Replacement |
|---|---|
| `proposals/` (word-start) | `{PROJECT}/proposals/` |
| `context/mission.md`, `context/board-scope.md`, `context/do-not-propose.md`, `context/architecture/` | `{PROJECT}/` + same |
| `context/` (word-start, all remaining) | `{HUB}/context/` |
| `tools/mlflow_reader.py`, `tools/session_timeline.py`, `tools/session_timeline_template.html`, `tools/hooks/` | `{AWOW_TOOLS}/` + basename path |
| remaining `tools/…` in non-vendored files | escalate: either the file becomes `channel: vendored` or the tool joins `PLUGIN_TOOL_PATHS` and the ref becomes `{AWOW_TOOLS}/…` — no third option |

Then read the full diff (`git diff`) file-by-file: fix double-substitutions (`{HUB}/{HUB}/`), prose that names paths as *examples of repo layout* (leave literal only inside `channel: vendored` files), and markdown link targets vs display text (sweep both).

- [ ] **Step 3: Regenerate and verify**

```bash
python tools/gather.py
python tools/gather.py --check   # expect: All stubs in sync.
grep -rnE '(^|[^{/A-Za-z])((context|proposals)/)' .agents/commands .agents/skills --include='*.md' | grep -v 'channel: vendored'  # expect: empty after excluding vendored files (manual pass until Task 5's lint exists)
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Sweep all bare context/tools/proposals references in .agents/ bodies to the {HUB}/{PROJECT}/{AWOW_TOOLS} tokens; mark install-operating commands channel: vendored."
```

### Task 4: Emitter renders tokens per surface

**Files:**
- Modify: `tools/gather.py` — `plugin_command_copy()` (line ~344), `plan_plugin()` (line ~366), module docstring.
- Modify: `.claude-plugin/plugin.json` — version 0.4.0 → 0.5.0.

**Interfaces:**
- Consumes: `channel` frontmatter key (Task 2), token spellings (header).
- Produces: `render_plugin_body(text: str) -> str` in `gather.py`; `dist/` free of `{AWOW_TOOLS}` and of `channel: vendored` files.

- [ ] **Step 1: Implement substitution + exclusion**

In `gather.py` add:

```python
PLUGIN_TOKEN_SUBSTITUTIONS = [
    ("{AWOW_TOOLS}", "${CLAUDE_PLUGIN_ROOT}/tools"),
]


def render_plugin_body(text: str) -> str:
    for token, replacement in PLUGIN_TOKEN_SUBSTITUTIONS:
        text = text.replace(token, replacement)
    return text
```

Apply `render_plugin_body` to command text inside `plugin_command_copy()` (both the `description`-injected and passthrough branches) and to skill bodies copied in `plan_plugin()` (the `copy_stub` path for skill `*.md` files and the declarative-skill wrapper). In `plan_plugin()`, skip any source whose frontmatter has `channel: vendored` (`parse_frontmatter(text)[0].get("channel") == "vendored"`). `{HUB}`/`{PROJECT}` ship as-is — the reflex teaches their resolution (WI-3).

- [ ] **Step 2: Rebuild, inspect, verify**

```bash
python tools/gather.py
grep -rL 'CLAUDE_PLUGIN_ROOT' dist/commands | head   # commands not using tools: fine
grep -rn '{AWOW_TOOLS}' dist && echo LEAK || echo CLEAN          # expect CLEAN
ls dist/commands | grep -E 'setup-awow|awow-add|update-awow' && echo LEAK || echo CLEAN  # expect CLEAN
python tools/gather.py --check                                     # expect in sync
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Render plugin payload bodies: substitute {AWOW_TOOLS} with \${CLAUDE_PLUGIN_ROOT}/tools and exclude channel: vendored commands from dist/. Bump plugin to 0.5.0."
```

### Task 5: Path lint

**Files:**
- Create: `tools/lint-paths.py`
- Modify: `.github/workflows/ci.yml` (append step to the `gather-check` job)

**Interfaces:**
- Consumes: `channel: vendored` frontmatter, token spellings.
- Produces: exit 1 with `file:line: bare path reference` lines on violation; CI step `Path-token lint`.

- [ ] **Step 1: Write the lint (stdlib only, same conventions as gather.py)**

```python
"""Fail if a non-vendored .agents/ prompt body references context/, tools/,
or proposals/ by bare path instead of {HUB}/{PROJECT}/{AWOW_TOOLS} tokens."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BARE = re.compile(r"(?<![{/\w`.])(context|tools|proposals)/")


def channel(text: str) -> str:
    m = re.search(r"^channel:\s*(\S+)", text[:2000], re.M)
    return m.group(1) if m else "both"


def main() -> int:
    bad: list[str] = []
    for root in ((REPO_ROOT / ".agents" / "commands"), (REPO_ROOT / ".agents" / "skills")):
        for path in sorted(root.rglob("*.md")):
            text = path.read_text()
            if channel(text) == "vendored":
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if BARE.search(line):
                    bad.append(f"{path.relative_to(REPO_ROOT)}:{n}: bare path reference: {line.strip()}")
    for b in bad:
        print(b)
    if bad:
        print(f"\n{len(bad)} bare path reference(s). Use {{HUB}}/{{PROJECT}}/{{AWOW_TOOLS}} "
              f"(see .agents/AGENTS.md 'Path tokens') or mark the file channel: vendored.",
              file=sys.stderr)
        return 1
    print("Path tokens clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Note the backtick in the negative lookbehind: inline code spans that *display* a literal path for humans (`` `python tools/gather.py` `` in vendored-facing prose) still fail unless the file is vendored-channel — that is intended; tune only with evidence from Step 2.

- [ ] **Step 2: Run against the swept tree**

Run: `python tools/lint-paths.py`
Expected: `Path tokens clean.` exit 0. If violations print, they are Task 3 escapes — fix them in `.agents/`, re-run `python tools/gather.py`, re-run lint.

- [ ] **Step 3: Wire into CI** — append to `.github/workflows/ci.yml` job steps:

```yaml
      - name: Path-token lint
        run: python tools/lint-paths.py
```

- [ ] **Step 4: Commit**

```bash
git add tools/lint-paths.py .github/workflows/ci.yml
git commit -m "Add tools/lint-paths.py blocking bare context/tools/proposals refs in non-vendored prompt bodies, wired into CI."
```

### Task 6: End-to-end re-validation with the MVP fixture method

**Files:** none committed (session-scratch fixture; formalised as `setup-fixture.sh` in WI-8).

- [ ] **Step 1: Install the real payload from the working tree**

```bash
claude plugin marketplace add <worktree-path>   # marketplace.json points at ./dist
claude plugin install awow@awow
```

- [ ] **Step 2: Re-run the MVP T1/T3 shape against a real swept command**

In a scratch spoke (AGENTS.md connector + context/board-scope.md, as in the validated MVP): run `claude -p "/awow:my-work" --model haiku` twice — with a fixture `AWOW_HUB` and without. Expected: with hub → command reads `{HUB}`-swept paths from the fixture hub (it will narrate resolution; pre-WI-3 the AGENTS.md stub carries the teaching); without → loud stop, no improvisation.

- [ ] **Step 3: Clean up and record**

`claude plugin uninstall awow@awow && claude plugin marketplace remove awow`. Append results as a checklist note to the PR description (not the spec — §8.1 stays the MVP record).

### Task 7: PR

- [ ] **Step 1:** Push `feat/hub-spoke-design`; open **PR 1** (spec + this plan + Tasks 1–6) against `main` — after explicit maintainer approval to push/PR, per repo rules. PR body: link spec §4/§5, the token glossary, inventory count (253), and Task 6 evidence.
