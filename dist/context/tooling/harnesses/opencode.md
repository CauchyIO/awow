# opencode — harness reference

The opencode coding agent. It reads `AGENTS.md` from the repo root and discovers `.agents/skills/` natively, so a vendored awow repo is **mostly legible to it with no install step** — only slash commands have to be emitted.

## When `/setup-awow` infers opencode

A `.opencode/` directory or an `opencode.json` at the repo root, or the user explicitly chooses opencode. As always the primary signal is which harness the model is running inside; these are corroborating.

## What it provides

- Reads a repo-root `AGENTS.md` natively as its instruction file — the cross-vendor standard, the same keystone Codex and Pi use
- **Native agent skills**, discovered from `.opencode/skills/`, `.claude/skills/` **and `.agents/skills/`**. awow's source-of-truth directory is itself a native opencode location, so awow's skills need no emitted surface at all.
- A native `skill` tool; skills are additionally invokable as `/name`
- **Native slash commands** from `.opencode/commands/` — the one surface awow must emit
- Plugins: JS/TS hook modules, installed from a git URL or npm

## How `.agents/` reaches opencode

- `.agents/AGENTS.md` → repo-root `AGENTS.md` — the pointer stub `tools/gather.py` already emits. This steers opencode today; no install required.
- `.agents/skills/<name>/SKILL.md` → discovered **in place**. `.claude/skills/` covers the two declarative skills that are flat files rather than directories.
- `.agents/commands/<name>.md` → `.opencode/commands/<name>.md`, emitted by `gather.py --surface opencode`.

The single source of truth is `.agents/`. Edits to generated surfaces are overwritten on the next `gather.py` run.

## Discovery precedence (verified, opencode 1.15.2)

Skills are **deduplicated by name**, with `.opencode/` > `.claude/` > `.agents/`. A name present in several locations resolves once, so the three surfaces coexist without cluttering the skill list.

`.claude/commands/` is **not** read — the Claude-compat layer covers skills and `CLAUDE.md`, not commands. That asymmetry is the entire reason a command surface has to be emitted.

## The `$ARGUMENTS` rule

opencode builds a command's placeholder list **from the template body**, matching `$1`/`$2`/… and testing for a literal `$ARGUMENTS`. A command template containing neither **receives no arguments at all, silently** — `/process-workitem AWO-48` would run with nothing.

Every emitted stub therefore carries a literal `$ARGUMENTS`, and `tests/harness/opencode/` asserts it per file. Prose such as "apply any arguments the user provided" is not a placeholder. This is why opencode has its own stub generator rather than sharing Claude's.

Frontmatter: `description` only. opencode also reads `agent`, `model` and `subtask`; leaving them unset keeps the user's own defaults. A `template` key must never appear — for a markdown command the body *is* the template.

## Plugin notes

opencode plugins are JS hook modules; **no manifest field can register skills or commands**, so the Codex `"skills"` and Pi `pi.skills` approaches have no equivalent. Registration happens at runtime instead:

- `dist/.opencode/plugins/awow.js` is emitted by `gather.py`. Its `config` hook appends the payload's `agent-skills/` to `config.skills.paths`; its `experimental.chat.messages.transform` hook injects the `using-awow` reflex plus an opencode tool mapping into the first user message.
- The bootstrap is what makes a *global* install useful: it lands in repos with no repo-root `AGENTS.md`, where nothing would otherwise tell the agent awow exists. A missing bootstrap fails loud, in the injected context and on stderr.
- `dist/package.json` is shared with Pi. opencode reads `main` and requires `type: "module"`; Pi reads `pi.skills`. The keys are disjoint, and one package.json at the payload root is the only option since both harnesses expect it there.

Install path: `opencode plugin awow@git+<awow-dist repo>`. `tools/sync-dist.sh` needs no change — it mirrors `dist/` to the marketplace repo root, which is exactly the package layout opencode expects.

## Known limitation

`.agents/skills/agent-directive-voice.md` and `.agents/skills/user-story-template.md` are flat files, not directories. opencode's native `.agents/` discovery globs `skills/*/SKILL.md`, so it finds these two only through the wrapped stubs under `.claude/skills/`. A user who sets `OPENCODE_DISABLE_CLAUDE_CODE=1` loses exactly those two; the other nine are directory-shaped and resolve natively.

## Status

Shipping under AWO-48: the `.opencode/commands/` surface, the `dist/` plugin module, `/setup-awow` detection, and wiring plus live regression tests under `tests/harness/opencode/`.

## Reference

- Design: [`2026-07-28-opencode-harness-design.md`](../../../docs/superpowers/specs/2026-07-28-opencode-harness-design.md)
