# Neighbouring teams (1° separation)

Teams whose work intersects awow's. Each owns its own summary; the entries below are placeholders until each neighbour writes their own.

## Cauchy consulting

The rest of Cauchy. First real internal adopters of awow.

- **Mission:** run client engagements; use the agentic way of working where it fits.
- **Members we work with:** the consulting engineers active on the current engagement.
- **Shared dependencies:** awow's prompts, skills, commands. Cauchy's internal Linear workspace for client work, separate from awow's own `awow` project on GitHub. See `meta/context/tooling/board.md` for the rationale.
- **Cadence:** unknown until the consulting team confirms.
- **Owner of this summary:** placeholder. Hand to the consulting team to own.

## Platform suppliers

Vendor relationships, not peer teams. Their release cadences trigger awow updates; the agent should know about them at session start.

- **Anthropic.** Claude Code (the harness) and the Claude models. awow updates `claude-api`, prompt voice, and tooling-reference docs in response to releases.
- **GitHub.** Repo host, GitHub Projects, `gh` CLI, GitHub Copilot. awow's GitHub Issues / Projects reference (`context/tooling/boards/github-issues/`) tracks the surface area.

## Future neighbours

- **Adopter engineering teams.** Once external teams adopt awow ("Use this template" + `/setup-awow`), each is a downstream neighbour. None named yet.

---

> Each neighbouring team owns its own summary. If a section is stale, ask the neighbour to update it.
