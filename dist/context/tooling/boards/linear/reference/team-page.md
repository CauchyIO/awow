# Linear — team page conventions reference

Every Linear team has a **team page** (Settings → Teams → `<team>`) and a description field on it. Most teams leave it empty. The agentic operating model treats it as a real context source.

## What a team page should contain

The team page is a context surface the agent reads at session start. It should answer, in this order:

1. **Mission** — one sentence; the same sentence that lives in `context/team/mission.md`.
2. **Members** — name, role, area of focus. The agent reads this to know who to @mention for a review.
3. **On-call rotation** — who's on this week, if applicable. The agent reads this to know who to ping for an urgent issue.
4. **Links** — to the team's `CLAUDE.md`-equivalent repo, to dashboards, to the runbook index.

Each item should be a line or two. Pages longer than half a screen are read less often.

## The Project description equivalent

Linear Projects have their own description fields. The convention:

- **Goal** — the customer change this Project delivers.
- **Time horizon** — quarter or cycle range.
- **Lead** — single named person.
- **Acceptance** — what makes the Project done (different from any individual Issue's acceptance criteria).

The agent reads the Project description before scoping any new Issue under that Project.

## Wizard responsibilities

**Mode A (from reference).** Linear's MCP does not (as of this writing) expose write access to the team page description. So:

1. Surface the checklist above.
2. Produce a draft team-page description from the user's answers to Steps 2–4 (`mission.md`, `members.md`).
3. Tell the user to **paste it into Linear Settings → Teams → `<team>` → Description** themselves. Record `team-page: pending-manual-paste` in `board.md` until the user confirms it is in.

**Mode B (assess current).**

1. Use the MCP (`mcp__linear-server__get_team`) to read the existing team description.
2. Surface what is there. If empty or weak, run Mode A's draft step.
3. If populated, capture a summary in `board.md` and note any gaps against the four-item checklist.

## What lands in `board.md`

```
## Team page conventions

Team page URL: <https://linear.app/<org>/settings/teams/<team>>
Description status: <populated | pending-manual-paste | empty>
Contents (or expected contents): mission, members, on-call, links.

Divergence from reference: <none | list>.
```
