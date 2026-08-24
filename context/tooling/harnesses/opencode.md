# opencode — harness reference

The opencode coding agent. It reads `AGENTS.md` from the repo root and discovers `.agents/skills/` natively, so the awow repo is **legible to it with no install step**; awow's flows reach it as skills through the plugin.

## When `/setup-awow` infers opencode

A `.opencode/` directory or an `opencode.json` at the repo root, or the user explicitly chooses opencode. As always the primary signal is which harness the model is running inside; these are corroborating.

## What it provides

- Reads a repo-root `AGENTS.md` natively as its instruction file — the cross-vendor standard, the same keystone Codex and Pi use
- **Native agent skills**, discovered from `.opencode/skills/`, `.claude/skills/` **and `.agents/skills/`**. awow's source-of-truth directory is itself a native opencode location.
- A native `skill` tool; skills are additionally invokable as `/name`
- **Native slash commands** from `.opencode/commands/` — awow emits none; its flows are skills
- Plugins: JS/TS hook modules, installed from a git URL or npm

## How `.agents/` reaches opencode

- Repo-root `AGENTS.md` — hand-authored (in the awow repo it points at `.agents/AGENTS.md`; an adopter's is its own bootstrapped file or spoke connector). This steers opencode today; no install required.
- Every command and skill → the plugin's `agent-skills/` surface, registered at runtime by the plugin's `config` hook (see Plugin notes). In the awow repo the directory-shaped skills under `.agents/skills/` are also discovered in place.

The single source of truth is `.agents/`. Edits to the generated payload are overwritten on the next `gather.py` run.

## Discovery precedence (verified, opencode 1.15.2)

Skills are **deduplicated by name**, with `.opencode/` > `.claude/` > `.agents/`. A name present in several locations resolves once, so a natively discovered skill and its plugin-registered copy coexist without cluttering the skill list.

`.claude/commands/` is **not** read — the Claude-compat layer covers skills and `CLAUDE.md`, not commands. awow therefore ships no command templates for opencode at all; a flow is invoked as `/name` through the skill it registers.

## The `$ARGUMENTS` rule

opencode builds a command's placeholder list **from the template body**, matching `$1`/`$2`/… and testing for a literal `$ARGUMENTS`; a template carrying neither receives no arguments, silently. awow no longer emits command templates, so this only matters for a team's own `.opencode/commands/`.

## Plugin notes

opencode plugins are JS hook modules; **no manifest field can register skills or commands**, so the Codex `"skills"` and Pi `pi.skills` approaches have no equivalent. Registration happens at runtime instead:

- `dist/.opencode/plugins/awow.js` is emitted by `gather.py`. Its `config` hook appends the payload's `agent-skills/` to `config.skills.paths`; its `experimental.chat.messages.transform` hook injects the `using-awow` reflex plus an opencode tool mapping into the first user message.
- The bootstrap is what makes a *global* install useful: it lands in repos with no repo-root `AGENTS.md`, where nothing would otherwise tell the agent awow exists. A missing bootstrap fails loud, in the injected context and on stderr.
- `dist/package.json` is shared with Pi. opencode reads `main` and requires `type: "module"`; Pi reads `pi.skills`. The keys are disjoint, and one package.json at the payload root is the only option since both harnesses expect it there.

Install path: `opencode plugin awow@git+<awow-dist repo>`. `tools/sync-dist.sh` needs no change — it mirrors `dist/` to the marketplace repo root, which is exactly the package layout opencode expects.

## Known limitation

`.agents/skills/agent-directive-voice.md` and `.agents/skills/user-story-template.md` are flat files, not directories. opencode's native `.agents/` discovery globs `skills/*/SKILL.md`, so in the awow repo it finds these two only through the plugin's `agent-skills/` registration, which renders every skill as `<name>/SKILL.md`. Without the plugin installed those two are invisible; the directory-shaped skills resolve natively.

## Status

Shipping under AWO-48: the `dist/` plugin module, `/setup-awow` detection, and wiring plus live regression tests under `tests/harness/opencode/`. The in-repo `.opencode/commands/` surface was retired under AWO-257.

## Reference

- Design: [`2026-07-28-opencode-harness-design.md`](../../../docs/superpowers/specs/2026-07-28-opencode-harness-design.md)
