# Proposal — issue for the awow board: session-board correlation

**Status:** Landed — shipped as the `session-correlation` skill (`.agents/skills/session-correlation/`), the session-footer rule in `output-discipline.md`, and `tools/session_footer_hook.py`. The draft below is kept as a record. The "park until the awow project exists" surface note is moot: the `awow` project (#3) exists, and the work shipped via skill + convention rather than a tracked board issue.

Draft of a GitHub issue against `CauchyIO/awow`. Filed after Casper approves (i) the project surface, (ii) the body verbatim, (iii) the footer format. Only the section marked **Issue body (verbatim)** is what gets pasted into the board.

---

## Look-first check (done)

- `gh issue list -R CauchyIO/awow --search "session" --state all` — none.
- `gh issue list -R CauchyIO/awow --search "correlation" --state all` — none.
- No existing issue covers the gap; ready to file.

---

## Surface

Same as the superpowers proposal: this issue is real awow product backlog, so it goes on the to-be-created `awow` project (not on Dogfood, not labelled `dogfood`). Park until that project exists.

---

## Labels

- `type:documentation` — the deliverable is a convention written into existing markdown files.
- `area:context` — the rule lands in `context/team/conventions/REQUIRED/` and `context/team/style/`.
- No `dogfood` label.

---

## Branch on file

`casper/issue-{number}-session-board-correlation`.

---

## Issue title

`Define session-board correlation convention`

(Pattern: `Define {thing}` — convention, policy, or standard, per `conventions/REQUIRED/issue-titles.md`.)

---

## Issue body (verbatim — what gets pasted into `gh issue create`)

```
Agent-originated board entries currently have no link back to the trace that produced them, so downstream skills (awow-usage-coach, daily-digest, weekly-digest) cannot join board content to session data. The existing conditional mention in /process-workitem Step 7 is too narrow (PR open only) and too soft (only "if the team has wired up that integrity link").

## Acceptance criteria

- [ ] `context/team/conventions/REQUIRED/output-discipline.md` (template) and `dogfood/context/team/conventions/REQUIRED/output-discipline.md` gain a Rule 4: every agent-originated issue create, issue comment, PR create, and PR comment includes a session footer in the body. Trivial metadata changes (label, state, project-add) are exempt.
- [ ] `context/team/style/board-output.md` (template) and `dogfood/context/team/style/board-output.md` gain a Format section stating the footer shape: `_session: <id> · commit: <sha-if-applicable>_` (italic, single line, machine-parseable).
- [ ] Exemption boundary stated in both files: the footer is required when the content records a decision or finding, or runs ≥ 2 sentences; one-liner status comments are exempt.
- [ ] `.agents/commands/seed/process-workitem.md` Step 7 is slimmed to reference the canonical rule rather than restating it conditionally.
- [ ] The rule is phrased harness-agnostically ("your harness's session ID") so Claude Code and Copilot both satisfy it.
- [ ] `tools/gather.py` re-run so the rule appears in the harness-side mirrors.

## Reference

- Existing conditional mention: `.agents/commands/seed/process-workitem.md` Step 7.
- Trace-side source of the IDs: `dogfood/.agents/CLAUDE.md` Tracing section (Stop hook writes to MLflow).
- Downstream skills that consume session IDs: `.agents/skills/awow-usage-coach/`, `.agents/skills/prompt-skill-analysis/`.
```

(No em-dashes. No external URLs. Intent + AC + reference only.)

---

## Proposal notes (not on the board)

### Why one issue, not split

This touches `.agents/commands/` (process-workitem) and `context/team/` (both template and dogfood mirror). The `issue-titles.md` split rule names `.agents/commands/`, `.agents/skills/`, `tools/`, and `context/tooling/boards/`; `context/team/` is not in that list, and the four file edits all express *one* outcome: the convention exists and is enforced. So: one issue.

### Why no ADR file

Same rationale as the superpowers proposal: real awow product decisions live as issue + PR; the diff and the PR description are the record. `dogfood/context/knowledge-base/decisions/` is illustrative content for the demo layer, not the source of truth for product memory.

### What this issue intentionally does **not** include

- **Implementing the accessor.** Whether the agent can read its own session ID at runtime is a separate problem — Claude Code exposes the transcript path to hooks reliably, but exposing it to the agent itself (so the agent can write `_session: <id>_` into a `gh issue create --body`) is not currently set up. This issue lands the *rule*; a follow-up issue handles the accessor.
- **Auto-appending via a Stop hook.** The cleanest mechanical version is a hook that walks issues/PRs the agent created in the session and appends the footer at session end. Lower friction than asking the agent to remember, but moves work from convention to harness config. Separate issue — file alongside the accessor follow-up.

### Follow-up issue (file together, depends on this one)

Title: `Implement session-ID accessor and Stop-hook auto-append for board entries`.

Body: one-sentence intent, AC covering (i) the agent reads its session ID at runtime, (ii) the Stop hook auto-appends the footer to any board entries the agent created mid-session, (iii) the accessor is documented in `dogfood/.agents/CLAUDE.md` Tracing section. Block this on the convention issue so the rule is in place before the mechanism is wired.

### Open questions before filing

1. **Confirm footer format.** `_session: <id> · commit: <sha>_` vs. `_session: <id>_` (commit SHA only when the comment is a PR-open notification) vs. `<!-- session: <id> -->` (HTML comment, invisible in rendered view). Recommendation: italic visible footer, with commit SHA only when a SHA is meaningful (i.e. the entry is a PR description or post-merge comment, not an issue body).
2. **Confirm exemption boundary.** ≥ 2 sentences OR records a decision/finding → footer required; otherwise exempt. Alternative: footer required on *all* agent-originated board writes, no exemptions. Recommendation: exempt the trivial cases — over-tagging makes the footer noise.
3. **Should the convention also cover the PR description**, or just the AC's listed write types? Recommendation: yes, PR descriptions are explicitly listed in the AC.
4. **Should this issue block the superpowers one?** No — they're orthogonal. The superpowers issue can file without the session footer; once this lands, future board entries (including comments on the superpowers issue itself) start including it.

Once these are settled:

```bash
gh issue create -R CauchyIO/awow \
  --title "Define session-board correlation convention" \
  --label "type:documentation,area:context" \
  --body-file <(sed -n '/^```$/,/^```$/p' proposals/session-board-correlation.md | sed '1d;$d')

gh project item-add <awow-project-number> --owner CauchyIO --url <issue-url>
```
