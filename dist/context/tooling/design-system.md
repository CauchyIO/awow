---
mode: absent          # absent | in-repo | external
path: ""              # in-repo  → context/design-system/style-guide.html
                      # external → e.g. ~/repos/design/cauchy-style-guide-v2.html
templates_dir: ""     # in-repo  → context/design-system/templates/
                      # external → e.g. ~/repos/design/templates/
access: ""            # external only: "local-path" (read via filesystem) or "mcp" — private repos are usually local-path / gh CLI, not MCP
rule: "Always re-read the source file before generating an artifact. The source file is authoritative; the token summary below is a convenience cache and can drift."
---

# Design system — pointer

Single source of truth for **whether** this team has a design system and **where** it lives. Every command that produces an HTML artifact (`/artifact`, `/design-system`, `/solution-design-flow`'s presentation track, the digests) reads this file first.

- **`mode: absent`** — no design system. Artifact-producing commands proceed with plain defaults and do not enforce any styling. This is the shipped default.
- **`mode: in-repo`** — the design system lives under `context/design-system/` in this repo. Self-contained; no cross-repo path fragility.
- **`mode: external`** — the design system lives in another repo, referenced by absolute path. Set `access:` so the agent knows to read it from the filesystem (the common case for a private design repo where the board MCP returns 404) rather than over MCP.

To stand one up — or to point at an existing one — run `/design-system` (or `/awow-add design-system`). That flow rewrites this file's frontmatter and fills the token summary below.

## Token summary (cache — source file wins)

Populated by `/design-system` when a system is established. Until then, empty. Keep this short: accent, background, text ramp, fonts, spacing scale, and the load-bearing principles. It exists so the agent can sanity-check without opening the full style guide — but per the `rule:` above, the agent must re-read the source file before generating, because this cache can fall out of date.

_(none — `mode: absent`)_
