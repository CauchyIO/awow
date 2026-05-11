# awow — agentic way of working, starter pack

A clone-and-go template for engineering teams adopting an agentic way of working.

> The agentic way of working is a method for running engineering teams in which agents maintain the plan — the board, the context, and the ceremonies — so people can spend their time on judgement, not coordination. Its aim is to make the plan as trustworthy and current as the code. This repo is the bootstrap for that method.

## Day one — five steps

1. **Clone this repo** into the place you want your team's context to live.
2. **Open an agent session** at the repo root (Claude Code or GitHub Copilot — both supported).
3. **Run `/setup-awow`.** The wizard asks for your board URL and a few short questions. It produces `context/tooling/board.md` and writes drafts of everything else under `proposals/`.
4. **Review the proposals**, then let the wizard land them.
5. **Pick a real story** and run `/refinement-prep` against it. The first ceremony is what proves the value.

The wizard is **incremental and resumable.** Only Step 0 — board configuration — is required to make the repo usable. Mission, conventions, members, knowledge base, neighbours, and the adoption plan are all *recommended-next* steps, in any order. Re-running `/setup-awow` picks up from `setup-progress.md` and offers the next thing to fill in.

## What's in this repo

```
.agents/           Source of truth for agent instructions — edit here
  commands/        Slash commands (seed / spread / standardise + archetypes)
  skills/          "What good looks like" markdown the agent reads at session start
.claude/           Pointer stubs for Claude Code — generated, redirect to .agents/
.github/           Pointer stubs for GitHub Copilot (copilot-instructions.md
                   + AGENTS.md + prompts/ + skills/) — generated, redirect to .agents/
context/           Everything the agent needs to know about this team
  team/            Mission, members, style guide, conventions
  knowledge-base/  Durable reference — what stories link to but don't repeat
  company/         Stakeholders, neighbouring teams, RACI
  tooling/         Board and harness reference docs
input/             Slidedecks, briefs, exports, design history — agent reads
transcripts/       Meeting transcripts — ephemeral, gitignored
proposals/         Agent drafts everything here first; humans review before land
mcps/              Approved MCP catalogue + intake template
tools/             Bootstrap and validation scripts
REFERENCES.md      Upstream registries (Anthropic Skills, awesome-copilot, MCP catalogues)
SETUP.md           Long-form walkthrough of /setup-awow
setup-progress.md  Wizard state — tracks what's been completed (resumable)
```

## One source of truth, two harness surfaces

Teams using both Claude Code and GitHub Copilot face the same trap: every instruction file, prompt, and skill ends up duplicated across `.claude/` and `.github/`, and the two drift. awow's answer is **pointer stubs**: author once under `.agents/`, and let `tools/gather.py` generate tiny redirect files in `.claude/` and `.github/` that the harness discovers natively.

- **Edit:** `.agents/CLAUDE.md`, `.agents/commands/<phase>/<name>.md`, `.agents/skills/<name>/SKILL.md`
- **Regenerate stubs:** `python tools/gather.py` (or `--check` in CI to detect drift)
- **What the stubs contain:** the frontmatter the harness needs for discovery (description, name) plus a one-line body that says "read `.agents/...` and follow it". No substantive content. Nothing to drift.

`.claude/` and `.github/` are committed so a fresh clone is immediately recognisable to either harness. Because the stubs carry no substantive content, the source-of-truth promise holds: the only thing gather has to keep in sync is discovery metadata, and `--check` catches that automatically.

## Status

v0.1 — skeleton. The structure and the pointer-stub toolchain are in place. The wizard and seed-command implementations are next.

The full design proposal lives in `input/PROPOSAL.md`. Linear-research additions in `input/ADDITIONS_FROM_LINEAR.md`. Peer-research synthesis in `input/research/synthesis.md`.

## Prerequisites

- A board with hierarchy: Linear, Azure DevOps, Jira, or GitHub Issues.
- An LLM coding agent available locally: Claude Code or GitHub Copilot.
- One engineer who wants to try this.

If those three are not true, the procurement conversation comes before the adoption conversation. See `input/PROPOSAL.md` §9.

## License

TBD. Pick before the first public release. MIT or Apache 2.0 are both consistent with the starter-pack remit.
