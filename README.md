# awow — agentic way of working, starter pack

A clone-and-go template for engineering teams adopting an agentic way of working.

> The agentic way of working is a method for running engineering teams in which agents maintain the plan — the board, the context, and the ceremonies — so people can spend their time on judgement, not coordination. Its aim is to make the plan as trustworthy and current as the code. This repo is the bootstrap for that method.

## Install

awow's scaffolding tools (`tools/gather.py`, `tools/bootstrap-claude-md.py`) are stdlib-only Python — there are no third-party packages to install — but they do need a Python 3.10+ interpreter. The recommended path uses [`uv`](https://docs.astral.sh/uv/) so you do not need a system-wide Python:

```bash
# macOS / Linux:
git clone <this-repo> && cd awow && ./setup/install.sh

# Windows (PowerShell):
git clone <this-repo>; cd awow; .\setup\install.ps1
```

The installer (`setup/install.sh` / `setup/install.ps1`) will:
1. Check that `uv` is on your PATH (and tell you how to install it if not).
2. Install Python 3.12 locally via `uv python install`.
3. Create a `.venv` in the repo root (already in `.gitignore`).
4. Run the initial pointer-stub gather so `.claude/` and `.github/` are populated.

After that, every subsequent gather is `uv run python tools/gather.py`. The `setup/` folder exists to make the connection to `/setup-awow` explicit: shell-level prerequisites live there; the agent-level wizard is `/setup-awow` once a session is open.

**Already have Python 3.10+?** Skip the installer: `python tools/gather.py` is all you need.

**No `uv` and no Python?** Install uv first (one line — see the script's error message for the official command). Everything else flows from there.

## Day one — five steps

1. **Install:** `git clone … && cd awow && ./install.sh` (see [Install](#install) above).
2. **Open an agent session** at the repo root. Claude Code (`claude` in the directory) or GitHub Copilot (open the folder in VS Code) — both are wired up at install time. The wizard auto-detects which one you are running in and asks if you also use the other.
3. **Run `/setup-awow`.** Step 0 walks you through the **board MCP** (Linear / Jira / Azure DevOps / GitHub Issues) and harness configuration — this is the only required step. The wizard surfaces the harness-specific install command for your board, with a link to the upstream docs. Subsequent steps (mission, conventions, members, knowledge base, neighbours, adoption plan) are *recommended-next* in any order.
4. **Review the proposals** under `proposals/setup/`, then let the wizard land them into their final paths.
5. **Pick a real story** and run `/refinement-prep` against it. The first ceremony is what proves the value.

The wizard is **incremental and resumable.** It reads `setup-progress.md` on every invocation and offers the next unfilled step.

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
setup/             First-time install scripts (prerequisite for /setup-awow)
tools/             Python scripts used during normal operation (gather, bootstrap, validate)
REFERENCES.md      Upstream registries (Anthropic Skills, awesome-copilot, MCP catalogues)
SETUP.md           Long-form walkthrough of /setup-awow
setup-progress.md  Wizard state — tracks what's been completed (resumable)
```

## One source of truth, two harness surfaces

Teams using both Claude Code and GitHub Copilot face the same trap: every instruction file, prompt, and skill ends up duplicated across `.claude/` and `.github/`, and the two drift. awow's answer is **pointer stubs**: author once under `.agents/`, and let `tools/gather.py` generate tiny redirect files in `.claude/` and `.github/` that the harness discovers natively.

- **Edit:** `.agents/CLAUDE.md`, `.agents/commands/<phase>/<name>.md`, `.agents/skills/<name>/SKILL.md`
- **Regenerate stubs:** `uv run python tools/gather.py` (or `python tools/gather.py` if you have a system Python). Use `--check` in CI to detect drift.
- **What the stubs contain:** the frontmatter the harness needs for discovery (description, name) plus a one-line body that says "read `.agents/...` and follow it". No substantive content. Nothing to drift.
- **File extensions matter for Copilot:** prompts under `.github/prompts/` must end in `.prompt.md` — VS Code's Copilot Chat silently ignores plain `.md` there. gather.py emits the right extension automatically; you only need to know this if you are debugging "my new command isn't showing up in Copilot".

`.claude/` and `.github/` are committed so a fresh clone is immediately recognisable to either harness. Because the stubs carry no substantive content, the source-of-truth promise holds: the only thing gather has to keep in sync is discovery metadata, and `--check` catches that automatically.

## Adopting & contributing back

A team that adopts awow takes a copy of the starter pack and grows their own context on top of it. The repo is therefore split — by path — into **starter-owned** content (the scaffolding, shared with every team) and **team-owned** content (your team's specifics, never shared back upstream).

| Path | Owner | Notes |
|---|---|---|
| `.agents/commands/`, `.agents/skills/` | Starter | Improvements here are the most valuable to send back upstream. |
| `context/tooling/`, `mcps/`, `tools/` | Starter | Board/harness references, MCP catalogue, scaffolding scripts. |
| `REFERENCES.md`, `SETUP.md`, `README.md` | Starter | Top-level docs. |
| `.agents/CLAUDE.md` | Starter → Team | The shipped file is a stub; `tools/bootstrap-claude-md.py` rewrites it with your team's content during `/setup-awow` Step 4. Treat as team-owned thereafter. |
| `context/team/`, `context/company/`, `context/knowledge-base/`, `context/quarterly/` | Team | Your mission, members, knowledge, goals. |
| `proposals/`, `setup-progress.md`, `adoption-plan.md`, `input/` | Team | Wizard state, drafts, your briefs and exports. |
| `.claude/`, `.github/` (pointer stubs) | Generated | Regenerated by `tools/gather.py`; don't hand-edit — changes here are lost on the next gather. |

**Recommended clone style: GitHub template, not fork.** Click *Use this template* so your repo starts with no upstream relationship. A fork would put `git pull` merges through `.agents/CLAUDE.md` and `context/team/`, which is exactly where you've diverged.

**Contributing improvements back to awow.** Today the path is manual: in a fresh clone of upstream awow, recreate your change against starter-owned files only, and open a PR. The split above makes this easy — anything outside the team-owned rows is fair game. If demand emerges, a `tools/propose-upstream.py` helper in a later release could diff starter-owned paths against the upstream tip and prep a PR branch automatically.

**Pulling later improvements from awow.** Also manual today: watch the awow upstream, and cherry-pick changes from starter-owned paths into your repo when they look worth picking up. Most teams will not need to do this often — the scaffolding is small and the team-owned surface is what grows.

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
