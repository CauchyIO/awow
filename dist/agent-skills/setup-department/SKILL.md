---
name: setup-department
description: "Use when a department repo has no identity or OKR surface yet, or the user asks to stand up a department, register a team submodule, or scaffold the department's quarterly OKR doc."
---

# /setup-department — stand up the department layer and join teams to it

You give a department repo an identity, join team submodules to it, and scaffold its OKR surface. This is the **lifecycle entry point — invoke it once for identity, and again, briefly, each time a new team joins.** It is rare. The ongoing rhythm — checking cascade health, refreshing pins, verifying backlinks — runs through `/okr-cascade`, not here; say this to the user before you do anything else.

## Step 1 — Ground

Read `{ANCHOR}/context/tooling/department.md`. If it is missing, tell the user this is a fresh department install and go to Step 2. If present, read `teams_root`, `read_scope`, `decisions_dir`, and `stale_after_days` from its frontmatter — resolve every later step against these values, never against the inline defaults written below (`teams_root` defaults to `teams`).

## Step 2 — Identity

Read `{ANCHOR}/context/department/definition.md`. If it still holds the shipped `# TODO` placeholders, run the interview below. If it already carries real content, ask whether to revise it or leave it as-is and skip to Step 3.

Ask one question at a time — never batch them:
1. The department's name.
2. In a sentence or two: what this department is and does.
3. Who leads it — the MD's name and role.

Write the answers into `{ANCHOR}/context/department/definition.md`: the name replaces the top heading, the description replaces the `# TODO — what this department is, who leads it` line, and the MD's name/role replaces the `MD: # TODO — name and role` line. Leave the RACI table as shipped — this interview does not touch it. Show the resulting file to the user and get explicit approval before moving to Step 3.

## Step 3 — Join loop (per team)

Repeat for each team joining the department; stop when the user confirms there are no more teams for this session.

1. Ask for the team's repo URL and its name.
2. Run `git submodule add <url> <teams_root>/<name>`. You run every git command yourself — the human never types git.
3. Append one row to `{ANCHOR}/context/department/teams.md`'s `| Team | Path | Lead |` table: `| <name> | <teams_root>/<name> | <lead> |`. Ask for the lead's name if the user hasn't already given one.
4. Read this repo's origin URL (`git remote get-url origin`). Draft the backlink file for the *team* repo, `<teams_root>/<name>/context/company/department.md`, with frontmatter `department: <this department's name>` and `parent: <that origin URL>`.
5. Prepare a branch and PR against the *team* repo adding that file. Show the diff and get explicit approval before creating the PR — every PR needs a yes first, and a backlink PR landing in someone else's repo doubly so. Once approved: in the `<teams_root>/<name>` submodule checkout, create a branch (e.g. `awow/join-<department>`), add `<teams_root>/<name>/context/company/department.md`, commit, push the branch to the team repo's remote, then run `gh pr create` against the team repo's default branch.
6. Tell the user plainly: the join is not complete until both sides merge — the submodule commit here, and the backlink PR there. Once both have landed, `python ../../tools/cascade_check.py` (or `/okr-cascade`'s ground step) verifies the backlink and registry are consistent.

Never continue past a failed `git submodule add`; stop and apply Step 7.

## Step 4 — Scaffold the OKR doc

Ask which quarter (e.g. `2026-Q3`). If `{ANCHOR}/context/department/okrs-<quarter>.md` already exists, stop loudly: tell the user the file is already there and leave it untouched — a quarter's OKR doc is never silently overwritten. Otherwise copy `{ANCHOR}/context/department/templates/okr-doc.md` to `{ANCHOR}/context/department/okrs-<quarter>.md`, update the heading to name the actual quarter, and show the result.

## Step 5 — Harness scoping

Check `.agents/AGENTS.md` for the marker `<!-- AWOW:DEPARTMENT-SCOPING:START -->`. If it is already there, this step has run — skip it. Otherwise append, between `<!-- AWOW:DEPARTMENT-SCOPING:START -->` and `<!-- AWOW:DEPARTMENT-SCOPING:END -->`, a short section stating that each submodule's own harness instruction surfaces (its `.agents/`, its `.claude/`) do not govern sessions in this repo — submodules are data, and a session here never loads them as behavioral rules. Append to `.agents/AGENTS.md` itself, never to the repo-root file of the same name — in a vendored tree that root file is `gather.py`'s output, rewritten wholesale on every build (including in Step 6, later in this same run), so an append there is destroyed before it ever persists.

## Step 6 — Gather

In a vendored tree, run the tree's own `gather.py` and confirm `.claude/commands/setup-department.md` and `.github/prompts/setup-department.prompt.md` now exist; surface any gather error verbatim and stop — do not guess at the cause. In a plugin install there is nothing to gather: the commands already reach the session from the payload, so record the step as `n/a` and continue.

## Step 7 — Fail loud

Surface every git failure verbatim, with the one-line fix when there is one (a missing `origin` remote, an unauthenticated `gh`). Never continue past a failed `git submodule add`, branch push, or PR create — stop, show the error, and wait for the user to resolve it before retrying that step.

## Behavioral boundaries

- **PR gate.** No PR is created — backlink or otherwise — without explicit user approval on the shown diff.
- **No silent overwrite.** An existing `okrs-<quarter>.md` is never touched; a new quarter gets a new file.
- **Idempotent scoping.** The `.agents/AGENTS.md` append runs at most once per repo; the marker is the only signal you check.
- **Fail loud, never fall back.** A failed git command stops the step it occurred in; it is never retried silently or worked around.
