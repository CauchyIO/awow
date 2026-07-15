# awow marketplace distribution

How awow reaches users on each harness. Two tiers: **self-hosted** (live now, no gatekeeper) and **official** (review-gated application to the vendor).

## Tier 1 — self-hosted marketplaces (LIVE, verified)

Nothing gates this; it works the moment the repos are public.

| Harness | Install | Source repo |
|---|---|---|
| Claude Code | `/plugin marketplace add CauchyIO/awow` → `/plugin install awow@awow` | `CauchyIO/awow` (root `.claude-plugin/marketplace.json` → `./dist`) |
| Codex | `codex plugin marketplace add https://github.com/CauchyIO/awow-dist` → `codex plugin add awow@awow` | `CauchyIO/awow-dist` |
| Pi | `pi install git:github.com/CauchyIO/awow-dist` | `CauchyIO/awow-dist` |

`CauchyIO/awow-dist` (public) holds the built `dist/` payload at its root — the Codex marketplace + Pi git-install source. Publish updates with `tools/sync-dist.sh --apply` (PR-based) after `dist/` changes on `main`. Claude Code installs from the source repo directly, so it needs no separate dist repo.

Verified 2026-07-14 against codex 0.144.1 (`installed, enabled 0.5.0`) and pi 0.80.6.

## Tier 2 — official marketplaces (application, review-gated)

Neither is a GitHub PR (the superpowers→openai-codex-plugins fork model is a community/legacy path, not the official one). Both are submission forms reviewed by the vendor.

### Codex — OpenAI Platform portal

- **Where:** `https://platform.openai.com/plugins` (web form, not a PR).
- **Submission type:** **Skills only** — awow ships skills, no MCP server of its own, so the MCP-app requirements (production MCP URL, domain verification, CSP, tool annotations) do **not** apply.
- **Prerequisites (only the org owner can clear):**
  - A **verified developer or business identity** for CauchyIO in the OpenAI Platform.
  - An org role with **Apps Management write access**.
- **Process:** submit → skills scanned for policy/security → OpenAI review → approve → publish from the portal → appears in the universal directory.

### Claude Code — Anthropic directory

- **Where:** the plugin directory submission form — **`clau.de/plugin-directory-submission`** (or in-app: `claude.ai/admin-settings/directory/submissions/plugins/new`, needs a Team/Enterprise org + directory-management access; or Console `platform.claude.com/plugins/submit`).
- **Important:** the fully-official `claude-plugins-official` directory is **curated by Anthropic with no public application process** — you cannot apply into it directly. The form enters the **`claude-community`** review pipeline. Passing basic automated screening lists the plugin; passing a stricter review earns the **"Anthropic Verified"** badge. That badge (not a claude-plugins-official listing) is the achievable quality signal.
- **Process:** submit at the short link → automated screening → community listing → optional stricter review → Verified badge.

## Application kit (drafted — reusable across both portals)

- **Name:** awow — Agentic Way of Working
- **Category:** Developer Tools
- **Short description:** Board-first delivery workflows for coding agents.
- **Long description:** Bring the Agentic Way of Working to any repo, new or existing. awow adds the files a coding agent needs to follow your issue board (Linear, Jira, GitHub Issues, Azure DevOps) and your team's conventions — without overwriting what's already there — then walks you through configuring it. It carries board hygiene, planning, and landing so the developer doesn't have to.
- **Starter prompts:**
  - "Set up awow in this repo"
  - "What does the board say I need to work on?"
  - "Take work item CAU-123 from refinement to a PR"
  - "Aggregate today's activity into a team digest"
- **Positive test cases (5):**
  1. "Set up awow in a fresh repo with a Linear board" → runs `/setup-awow`.
  2. "What do I need to act on?" → `/my-work` reads the board.
  3. "Process this meeting transcript into board updates" → `/process-transcript`.
  4. "Give me a daily digest of the team's activity" → `/daily-digest`.
  5. "Take this refined item to a PR" → `/process-workitem`.
- **Negative test cases (3):**
  1. "Delete every issue on the board" → awow does not perform destructive board ops on a bare request.
  2. "Commit these production credentials into the repo" → refuses.
  3. "Merge straight to main" → awow's conventions require review/approval; it does not.
- **License:** MIT (`LICENSE` at repo root).
- **Release notes (v0.5.0):** Codex + Pi packaging (hub-and-spoke WI-5) — commands-as-skills surface, Codex plugin manifest, Pi package, self-hosted marketplace.

## Blockers — only the org owner (casper) can clear these

1. **OpenAI verified business identity** for CauchyIO + Apps Management write access (Codex portal).
2. **Logo asset** — a square icon for both listings (not in the repo yet).
3. **Privacy policy URL + Terms URL** — both portals collect these; awow has none hosted. (Adding external links to the project needs explicit sign-off per repo policy.)
4. **Anthropic directory submission** — locate + fill the current plugin-directory form.

## Manifest enrichments (done)

The canonical `.claude-plugin/plugin.json` now carries `license: "MIT"`, `homepage`, and `repository` (`https://github.com/CauchyIO/awow`); `gather.py` passes them through to the Codex manifest and Pi package. So `dist/.codex-plugin/plugin.json` and `dist/package.json` now expose `name`, `version`, `description`, `author`, `license`, `homepage`, `repository`, plus `interface{displayName, shortDescription, category}` (codex). Version stays lockstepped and `--check`-guarded.
