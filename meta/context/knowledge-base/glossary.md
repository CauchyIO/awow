# Glossary

Domain terms specific to awow and the `meta/` workspace. Referenced from stories and prompts; not redefined per ticket.

## `agent`

The model + tools running in-session against this repo. Today: Claude Code (Opus 4.7) for the maintainer. Tomorrow potentially also GitHub Copilot or other harnesses. Distinct from "Claude" (the model alone) and "Claude Code" (the harness alone).

## `awow`

This repo. The agentic way of working *starter pack* — a clone-and-go template adopting teams use to bootstrap the methodology. Distinct from "the agentic way of working" (the methodology) and "Cauchy" (the team that maintains awow).

## `Cauchy`

The team that maintains awow. One member today (Casper, `@hetspookjee`).

## `meta (workspace)`

The `meta/` directory at the repo root (formerly `dogfood/`). The workspace where awow is applied to itself. Carries its own team context, board, conventions, and KB — not inherited by adopters who use "Use this template".

## `awow-test (label)`

The GitHub label `awow-test` applied to every issue generated during a test walkthrough (dogfooding awow against itself) on `CauchyIO/awow`. Bulk-closed by `/awow-reset`. See `meta/context/knowledge-base/patterns/awow-test-label-inflation-control.md`.

## `gather`

`tools/gather.py`. The mirror toolchain that reads `.agents/commands/*.md` and `.agents/skills/**/SKILL.md` and writes pointer stubs into `.claude/commands/`, `.claude/skills/`, `.github/prompts/`. Runs after every edit to `.agents/`.

## `harness`

The runtime environment the agent runs inside. Today: Claude Code or GitHub Copilot. The "harness surface" is the directory the harness discovers its commands and skills from (`.claude/`, `.github/`).

## `MCP`

Model Context Protocol. The protocol Claude Code and Copilot use to talk to external systems (boards, file stores, etc.) via local or remote MCP servers. For awow's own backlog, the MCP is deliberately skipped in favour of `gh` CLI; see `meta/context/knowledge-base/decisions/0001-gh-cli-vs-mcp.md`.

## `mirror`

The one-way copy from `.agents/` to `.claude/` and `.github/`, performed by `gather.py`. `.agents/` is the single source of truth; edits to the mirror surfaces are overwritten on the next gather.

## `pointer stub`

An auto-generated file under `.claude/commands/`, `.claude/skills/`, or `.github/prompts/` that contains a one-line reference to its `.agents/` source plus the gather-generated `<!-- GENERATED -->` warning. Lets the harness natively discover commands and skills without duplicating their content.

## `starter pack`

awow's deliverable form: a GitHub template repo. Adopters use the "Use this template" button (per project memory), not `git fork`. Distinct from a SaaS product.

## `worked example`

The `meta/` folder. Awow applied to itself — both as a real working substrate for the maintainer and as a reference an adopter can read to see "what does a fully-set-up awow team's context look like".

## `wizard`

`/setup-awow`. The incremental, resumable bootstrap command that walks adopters through the 10 steps (0–9) of configuring awow for their team.
