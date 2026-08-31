# Microsoft 365 Copilot — harness reference

A declarative agent for non-technical users whose only surface onto awow is Microsoft 365 Copilot — no repo, no CLI. Pilot / experimental: this slice covers advisory grounding and one ported command whose output lands as a copy-paste draft in chat — not yet gated by an M365 confirmation card.

## What this harness is

Unlike Claude Code and Copilot, this harness has no local checkout to mirror into — the target user never has a repo. Instead, `gather.py` emits a Teams app package that Copilot loads as a **declarative agent**: inline instructions, conversation starters, and an action that fetches awow's markdown live from git on every call. There is no copy of `context/` anywhere in the package — git stays the sole source of truth, and the agent re-reads the exact file each time it needs one, the same "never answer from memory what you can fetch" contract the other harnesses run on.

The agent's identity, description, and index roots are configured in `context/tooling/m365/agent.md`. The design rationale — why a declarative agent, the two primitive swaps (runtime fetch instead of a mirrored copy, a git inbox write instead of inlined KB mechanics), and what's deferred to a later increment — lives in `docs/superpowers/specs/2026-07-15-m365-copilot-harness-design.md`.

## When `/setup-awow` infers M365 Copilot

It doesn't, yet. This harness is assigned by a tenant admin, not self-detected from repo contents — the target population by definition has no repo for `/setup-awow` to run in.

## What it provides

- **Instructions** — an inline system prompt assembled from `agent.md` plus a generated file-index manifest (fetchable paths + one-line descriptions), capped at 8,000 characters.
- **Conversation starters** — the declarative-agent equivalent of slash commands, capped at 12. This slice ships two: a general grounding starter ("What does awow say about how we work?") plus one ported command, `refinement-prep`.
- **A `fetchAwowContext` action** — an OpenAPI plugin that calls the GitHub contents API directly (public-repo direct fetch; a proxied endpoint for private anchors is a later increment).
- No board actions and no `commitAwowInbox` in this slice — see Slice limits below.

## Regenerating

```bash
uv run python tools/gather.py                  # the default build includes the package
uv run python tools/gather.py --surface m365   # only the package
```

Emits `dist/m365/appPackage/` (manifest, declarative agent, plugin + OpenAPI specs, icons) from `.agents/` + `context/`, the same generated-payload contract as `dist/`. Never hand-edit files under `dist/m365/` — they're overwritten on the next run. The plan sees every file git would commit, staged or not; only ignored files are left out.

Drift guard:

```bash
uv run python tools/gather.py --check
```

The default check covers the package, so CI and a pre-commit run catch a stale one without a separate step.

## Packaging

Teams needs a zip whose root contains `manifest.json` directly — not nested inside a folder:

```bash
cd dist/m365/appPackage && zip -r ../awow-m365.zip .
```

## Sideloading (pilot)

1. In Teams: **Apps → Manage your apps → Upload an app → Upload a custom app**, then pick `awow-m365.zip`.
2. If the tenant blocks custom-app upload, a tenant admin either enables it (Teams admin center → **Teams apps → Setup policies → Upload custom apps**) or uploads it org-wide themselves.
3. Once installed, the agent appears in M365 Copilot's agent list.
4. Step zero, in the first conversation: ask the agent to fetch a known file and confirm raw markdown text arrives — not a JSON or base64 envelope. That check is exactly what proves the fetch contract on the real runtime.

Requires an M365 Copilot seat — the single largest adoption gate for this population.

## First-use consent

The first `fetchAwowContext` call shows a consent card. This is expected — click through once, and it won't reappear for that user.

## Fetch smoke test

Before sideloading, confirm the fetch path works from any shell:

```bash
curl -sf https://raw.githubusercontent.com/CauchyIO/awow/main/.agents/commands/refinement-prep.md | head -5
```

Expected: the file's frontmatter prints. Unauthenticated raw fetches are throttled by GitHub — fine for a pilot. A later increment replaces this direct fetch with a proxied endpoint (design spec §4.1a) for private anchors.

## Slice limits (stated honestly)

- **Board actions aren't wired.** Drafts render in chat for the user to copy-paste into their board tool themselves — no `board.query`/`board.update` calls yet.
- **`commitAwowInbox` is deferred.** KB captures and proposal drafts don't yet land in the anchor's `kb-inbox/` from this surface.
- **Grounding beyond the file index relies on fetch, not RAG.** There's no Graph-connector discovery index in this slice — the agent finds files via the generated manifest and named fetches, not fuzzy search.

## Reference

- Design spec: `docs/superpowers/specs/2026-07-15-m365-copilot-harness-design.md`
- Harness config: `context/tooling/m365/agent.md`
