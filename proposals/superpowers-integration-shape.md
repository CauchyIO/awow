# Proposal — issue for the awow board: superpowers integration

**Status:** Draft — ready to file as a GitHub issue once the acceptance criteria are confirmed.

Draft of a GitHub issue against `CauchyIO/awow`. Filed after Casper approves the body verbatim. Only the section marked **Issue body (verbatim)** is what gets pasted into the board. No ADR file in this repo — the issue + the PR that implements it are the record.

---

## Look-first check (done)

- `gh issue list -R CauchyIO/awow --search "superpowers" --state all` → no matches.
- `gh issue list -R CauchyIO/awow --search "integration" --state all` → no matches.
- The `awow` project (#3 on CauchyIO) is the single durable backlog.

Clean to file a new issue.

---

## Surface — project

File on the `awow` project (#3 on CauchyIO), the single durable backlog. Inflation control is **label-based, not project-based**: ephemeral walkthrough issues carry the `dogfood` label and are bulk-closed by `/awow-reset`; this is durable product work, so it takes **no `dogfood` label** and survives resets.

(Superseded decision: an earlier draft proposed creating a *second* project to separate durable backlog from a `Dogfood` scratch project. That project was instead renamed `awow` (#3), so the single-project + `dogfood`-label model stands — see `meta/context/knowledge-base/patterns/dogfood-label-inflation-control.md`.)

---

## Labels

- `type:feature` — the outcome is a real capability (adopters can use `obra/superpowers` via awow).
- `area:skills`.
- No `dogfood` label (durable backlog, not walkthrough ephemera).

---

## Branch on file

`casper/issue-{number}-superpowers-integration`, per `conventions/REQUIRED/branches.md`.

---

## Issue title

`Implement integration with obra/superpowers skills`

(Pattern: `Implement {thing}` — net-new capability, per `conventions/REQUIRED/issue-titles.md`.)

---

## Issue body (verbatim — what gets pasted into `gh issue create`)

```
Adopters running awow alongside obra/superpowers currently get two front-of-loop methodologies competing (board-first vs. brainstorm-first), and Copilot users get nothing because superpowers ships as a Claude-only plugin.

## Acceptance criteria

- [ ] Integration shape chosen between A (plugin-install + a CLAUDE.md glue paragraph that sequences board-first ahead of superpowers' loop, Claude Code only) and B (vendoring superpowers skills under `.agents/skills/superpowers/` so they mirror to both `.claude/skills/` and `.github/skills/`).
- [ ] Shape implemented in the chosen surface, with at least one superpowers skill exercised end-to-end (e.g. `writing-plans` lands a draft under `proposals/` rather than ad-hoc).
- [ ] Four collision points addressed in the implementation or the PR description: front-of-loop methodology, install vector, namespace, per-skill behaviour deltas (`writing-plans`, `finishing-a-development-branch`, `requesting-code-review`, `receiving-code-review`).
- [ ] If shape B is chosen, `tools/gather.py` handles the nested skill namespace and `--check` passes in CI.

## Reference

- Upstream repo coordinate: `obra/superpowers`.
- Decision precedent for `gh` vs MCP surface: `meta/context/knowledge-base/decisions/0001-gh-cli-vs-mcp.md`.
```

(No em-dashes. One-sentence intent + AC + reference per `output-discipline.md` Rule 1. No external URLs per the global "no external website links" rule. The decision rationale lives in the PR description and the diff, not in a markdown ADR.)

---

## Proposal notes (not on the board)

### Why one issue, not split

If shape A is chosen, the change touches `.agents/CLAUDE.md` alone — one surface, one issue. If shape B is chosen, it crosses `.agents/skills/` and `tools/gather.py`, which `issue-titles.md` calls "almost always too big" and recommends splitting. So: keep this as one issue while the shape is undecided; if B wins, this issue produces the decision in a PR description and a follow-up issue carries the gather change.

### Why no ADR file

Per the convention this conversation surfaced: real awow product decisions live as GitHub issues + PRs. `meta/context/knowledge-base/decisions/` is illustrative content for the demo, not the source of truth for product memory. Capturing the rationale in the PR description keeps it next to the diff and avoids polluting the demo layer.

### Open questions before filing

1. **Anything missing from the acceptance criteria** — e.g. an explicit voice-rules audit of superpowers' SKILL.md files, an in-repo example skill chosen for the end-to-end exercise.

Once settled:

```bash
# 1. Agent files the issue (after Casper approves the body above):
gh issue create -R CauchyIO/awow \
  --title "Implement integration with obra/superpowers skills" \
  --label "type:feature,area:skills" \
  --body-file <(sed -n '/^```$/,/^```$/p' meta/proposals/superpowers-integration-shape.md | sed '1d;$d')

# 2. Agent adds the issue to the awow project (#3):
gh project item-add 3 --owner CauchyIO --url <issue-url>
```
