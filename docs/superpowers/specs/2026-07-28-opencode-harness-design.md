# awow on opencode — harness design

- **Date:** 2026-07-28
- **Status:** Draft (design spec — pre-implementation)
- **Board:** AWO-48
- **Related:** `context/tooling/harnesses/{codex,pi}.md`, `meta/proposals/pi-codex-harness-support.md`, `tools/gather.py`, `tools/sync-dist.sh`

## 1. Problem

opencode is a fifth harness awow does not yet support. Unlike the M365 Copilot port, no primitive is missing: opencode has a repo-root instruction file, native agent skills, and native slash commands. The question is only which of awow's existing surfaces it already reads, and what has to be emitted for the rest.

## 2. What already works — measured, not assumed

Probed against **opencode 1.15.2** with a purpose-built fixture (a git repo carrying the same skill name in `.opencode/`, `.claude/` and `.agents/`, a command in each of `.opencode/commands/` and `.claude/commands/`, and a repo-root `AGENTS.md`), read back through the headless server's `/skill`, `/command` and `/config` endpoints.

| awow surface | opencode behaviour | Work needed |
|---|---|---|
| repo-root `AGENTS.md` | read natively as the instruction file | none — already emitted |
| `.agents/skills/<n>/SKILL.md` | discovered natively | none |
| `.claude/skills/<n>/SKILL.md` | discovered via the Claude-compat layer | none |
| same skill in all three | **deduplicated by name**, precedence `.opencode/` > `.claude/` > `.agents/` | none |
| skills in the command palette | skills are **also** invokable as `/name` | none |
| `.claude/commands/*.md` | **not read** — upstream feature request only | — |
| `.opencode/commands/*.md` | read; body is the prompt template | **the whole gap** |

Two consequences. First, a vendored awow repo already steers opencode and already exposes all 20+ skills with zero install — the Codex/Pi work on `main` delivered that incidentally. Second, **slash commands are the only genuine gap.**

### 2.1 The `$ARGUMENTS` constraint

opencode derives a command's placeholder list *from the template body*, matching `/\$\d+/g` and testing for a literal `$ARGUMENTS` (confirmed in the 1.15.2 binary's `Command` service). A template containing neither receives **no arguments at all** — silently.

awow's existing stub body says "applying any arguments the user provided to this invocation", which is prose, not a placeholder. Reusing `gen_command_stub` unchanged would therefore produce commands that discard `/process-workitem AWO-48`. opencode needs its own generator. This is the single most important implementation detail in this spec.

### 2.2 Frontmatter

opencode reads `description`, `agent`, `model`, `subtask`. Only `description` is meaningful for a pointer stub — the rest stay unset so the user's own agent/model defaults apply. `template` must **not** appear in frontmatter for markdown commands; the body serves that role.

## 3. Design

The guiding invariant is unchanged: `.agents/` stays the single source of truth, and everything new is either a generated surface or a thin manifest. No substantive content is duplicated.

### 3.1 In-repo — `gather.py --surface opencode`

A new `OPENCODE_DIR = REPO_ROOT / ".opencode"`. `plan_commands()` gains a third target emitting `.opencode/commands/<name>.md`.

The existing loop pairs `(target_dir, ext)` against one shared generator (`tools/gather.py:484`); it becomes `(target_dir, ext, generator)` so opencode can use `gen_opencode_command_stub` while Claude and Copilot keep `gen_command_stub` byte-for-byte unchanged. The new generator emits `description`-only frontmatter and a body carrying a literal `$ARGUMENTS`.

These stay **pointer** stubs. `.agents/` is present in a vendored repo, so pointers resolve and no content is duplicated — the no-drift invariant that justifies the whole gather model. Full-content rendering is correct only for `dist/`, which ships where `.agents/` is absent.

`SURFACE_ROOTS` gains `"opencode": [OPENCODE_DIR]` and adds it to `"all"`. `"both"` keeps its literal Claude-plus-Copilot meaning; it is a named pair, not a synonym for "every in-repo surface". Orphan detection needs no change — the stubs carry the standard `GENERATED` marker.

**Deliberately not mirrored:** `plan_folder_readmes()` writes a `README.md` into each command directory, and every harness turns that file into a spurious `/README` command — observable today in Claude Code's own command list. Emitting one into `.opencode/commands/` would reproduce the bug on a new surface. The existing Claude/Copilot leak is real but out of scope here; it should get its own issue rather than be fixed inside a harness addition.

### 3.2 Distribution — `dist/.opencode/plugins/awow.js`

opencode plugins are JS/TS hook modules. No manifest field can register skills or commands, so the Codex `"skills": "./agent-skills/"` and Pi `pi.skills` approaches have no direct equivalent. The working pattern is the one superpowers already uses in production: a git-installable package whose `package.json` `main` points at a plugin module, which registers its skills directory through the `config` hook.

awow's `dist/` already carries both pieces this needs — `package.json` (built for Pi) and `agent-skills/`. A new `plan_opencode_plugin()` emits the plugin module and extends the existing `dist/package.json` with `main` and `type: "module"`, leaving `pi.skills` untouched so one payload serves both harnesses.

The plugin does two things:

1. **Registers skills.** The `config` hook appends the package's own `agent-skills/` directory to `config.skills.paths`, resolved from `import.meta.url` — no symlinks, no user config edits.
2. **Injects the bootstrap.** It reads `agent-skills/using-awow/SKILL.md`, strips frontmatter, and injects it per session with an opencode tool mapping (`read`/`write`/`edit`/`bash`/`todowrite`, `task` for subagents, the native `skill` tool). This is the parity item: a global install lands in repos with no root `AGENTS.md`, so without it awow would be installed but dormant.

It reads the bootstrap from `agent-skills/` — the same directory it registers — so `{AWOW_ROOT}` and `{AWOW_TOOLS}` resolve through the `render_agent_skills_body` channel (`../..` and `../../tools`), exactly as they do for Pi. Reading from `dist/skills/` instead would mix token channels, which is the class of bug `hooks/session-start` documents.

A missing bootstrap **fails loud** — an unmistakable marker in the injected context plus stderr — matching the posture adopted after the 0.5.0 payload shipped a silent one-line error in place of the entire reflex.

**No change to `tools/sync-dist.sh`.** It mirrors `dist/` to the `CauchyIO/awow-dist` root, so `package.json`, `.opencode/plugins/` and `agent-skills/` all land where opencode expects. The install is:

```
opencode plugin awow@git+<awow-dist repo>
```

### 3.3 Docs, detection, tests

- `context/tooling/harnesses/opencode.md`, following the `codex.md` shape, plus a row in the harnesses README table.
- `/setup-awow` Step 1a gains `.opencode/` and `opencode.json` as corroborating signals (the primary signal remains which harness the model is running inside). Step 0's verification adds `.opencode/commands/setup-awow.md` alongside the Claude and Copilot probes.
- `gather.py --check` covers the new surface under the existing drift and orphan guards. A regression test asserts the emitted stub carries `$ARGUMENTS`, since that failure is silent at runtime and would otherwise only surface as "arguments mysteriously ignored".

## 4. Known limitation — flat declarative skills

Two skills are flat files rather than directories: `.agents/skills/agent-directive-voice.md` and `.agents/skills/user-story-template.md`. opencode's native `.agents/` discovery globs `skills/*/SKILL.md`, so it finds these only through the wrapped stubs under `.claude/skills/`.

A user who sets `OPENCODE_DISABLE_CLAUDE_CODE=1` or `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1` therefore loses exactly those two skills — the other nine are directory-shaped and resolve natively. This is narrow and has an obvious fix if it ever bites: emit `.opencode/skills/<name>/SKILL.md` for declarative skills only. Not built now, because it costs a third copy of those skills in-repo to serve a configuration nobody is known to run.

## 5. Non-goals

- **No `.opencode/agents/`.** awow has no subagent definitions to contribute; opencode's built-in agents are the user's own choice.
- **No opencode-specific command bodies.** Prompts stay harness-neutral in `.agents/`; only the wrapper differs.
- **No npm-registry publish.** The git-install path works today and needs no new account or release pipeline.
- **Not fixing the `/README` command leak** (§3.1) — flagged, separately tracked.

## 6. Work items

| # | Item | Depends on |
|---|---|---|
| WI-1 | `gen_opencode_command_stub` + `.opencode/commands/` target in `plan_commands`; `SURFACE_ROOTS` entry | — |
| WI-2 | `plan_opencode_plugin()` — plugin module + `dist/package.json` `main`/`type` | WI-1 |
| WI-3 | `context/tooling/harnesses/opencode.md` + README table row | — |
| WI-4 | `/setup-awow` Step 0 verification + Step 1a detection signals | WI-1 |
| WI-5 | Regression tests: surface drift, `$ARGUMENTS` presence, payload parity | WI-1, WI-2 |

WI-1 and WI-3 are independent and can land together; WI-2 is the only item touching the published payload and should be verified against a real `opencode plugin` install before the sync-dist PR.

## 7. Open items

1. **Plugin API stability.** The `config` hook and `skills.paths` are verified present in 1.15.2 and used by superpowers, but neither is covered by a documented compatibility guarantee. Pin the observed shape in the harness doc so a future break is diagnosable.
2. **Install-path confirmation.** `opencode plugin <name>@git+<url>` is confirmed working for superpowers, whose package sits at its repo root. awow-dist has the same shape, but the first real install should be verified end-to-end before the harness doc calls it supported.
3. **External links.** Following the repo's no-external-links rule, opencode documentation URLs go in `REFERENCES.md` (or are dropped) rather than into `opencode.md` without sign-off.
