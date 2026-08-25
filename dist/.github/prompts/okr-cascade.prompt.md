---
description: "Use when a department's quarterly OKR cascade needs attention — starting the quarter's objectives, refining key results, translating objectives into team PI-plan proposals, or reviewing drift and KR movement partway through the quarter."
phase: spread
layer: department
prerequisites:
  - "{HUB}/context/department/ stood up and at least one team joined (`/setup-department`)"
  - "an OKR doc for the current quarter at `{HUB}/context/department/okrs-<quarter>.md`"
removes_pain: "the quarter's OKR cascade drifting out of sync with team reality because nothing forces regular reconciliation"
when-to-use: "The department's standing quarter machinery: Articulate, Refine, Translate, or Review. Review is the recurring strategic review — grading KR movement against board reality."
when-not-to-use: "Forming the strategy in the first place — vision to bets to a draft KR set is /strategy-flow. Working one locked bet in a live board session — that is the bet-refinement-coach skill."
---

# /okr-cascade — run the quarter's OKR cascade

You drive the department's OKR cascade through four stages — **Articulate, Refine, Translate, Review** — entered at whatever stage the quarter actually stands at, not necessarily in order. `/setup-department` is the lifecycle entry point: run once for identity, briefly again per joining team. This command is the rhythm — invoke it whenever the cascade needs attention, every time the quarter needs a check, a refinement, a translation, or a review.

---

## Ground (every entry, regardless of stage)

Run this section on every invocation before entering any stage below.

1. **Read the indirection.** Read `{HUB}/context/tooling/department.md`. Resolve `teams_root`, `read_scope`, `decisions_dir`, and `stale_after_days` from its frontmatter for every later step — never from the inline literals written in this file.
2. **Run the check.** Run `python ${CLAUDE_PLUGIN_ROOT}/tools/cascade_check.py --json` from the repo root. Parse the JSON body: `quarter`, `findings` (list of `{class, team, detail}`), `drift` (list of `{team, pinned, remote}`), `pin_age_days` (map of team → integer days).
3. **Exit 2 stops you cold.** No JSON is emitted on exit 2 — only a `CascadeConfigError` message on stderr. Show that message verbatim and stop before touching any stage.
   - **Already carries its own fix** — show it and stop, nothing more to add: missing `{HUB}/context/tooling/department.md` (the message itself says "— run `/setup-department` first"); no `origin` remote configured (the message names the exact `git remote add` command).
   - **`{HUB}/context/tooling/department.md` present but malformed** — a missing required field, or a non-integer `stale_after_days` — show the error verbatim and name the exact line to fix: add the missing field (one of `teams_root`, `read_scope`, `decisions_dir`, `stale_after_days`) with a value, or replace the `stale_after_days` value with a plain integer.
   - **Everything else, name the fix yourself:** missing or malformed `teams.md` → run `/setup-department`'s join loop or fix the `| Team | Path | Lead |` table by hand; no `{HUB}/context/department/okrs-<quarter>.md` found → run `/setup-department` Step 4 to scaffold the current quarter's doc.
4. **Exit 0 or 1, read on regardless.** Present `findings` as a compact table (`class | team | detail`) — empty is worth stating plainly ("no findings"), not skipping. Note `drift` separately if non-empty: a drift entry can exist without a `pin-stale` finding, since drift fires on any pinned/remote mismatch while `pin-stale` only fires past `stale_after_days`.
5. **Read the department's own docs.** Read `{HUB}/context/department/definition.md`, `{HUB}/context/department/teams.md`, the current `okrs-<quarter>.md`, and any prior files under `<decisions_dir>/`. This is your working knowledge for every stage below.
6. **Load the coach.** Load `department-coach` — Refine and Review lean on its battery and discipline directly; Articulate and Translate lean on it lighter.
7. **Recommend a stage.** Every finding class the script can emit routes to exactly one bolded recommendation; check in this order and stop at the first match:
   - `registered-missing`, `backlink-missing`, or `backlink-mismatch` present → recommend **`/setup-department`**, not a cascade stage. A team's join is itself broken (missing checkout, missing backlink, or a backlink pointing at the wrong parent) — fix that first via its join loop or a backlink PR before any objective, KR, or mapping work means anything. Exception: if a `registered-missing` finding's detail names a git/network failure (e.g. mentions `ls-remote` or an unreachable remote) rather than a missing checkout, the join itself may be fine — recommend fixing connectivity and re-running the check instead of `/setup-department`.
   - `unregistered-present` present → recommend **`/setup-department`**. A directory under `teams_root` with no registry row is a setup gap, not a cascade-stage problem — register it as a team or remove it.
   - No objectives yet, or the doc still holds template placeholders → recommend **Articulate**.
   - Objectives exist but their KRs are missing, placeholder, or never ran the coach's battery → recommend **Refine**.
   - `serves-nothing`, `orphaned-objective`, or `serves-unknown` present → recommend **Translate**. (`serves-unknown` means a team's `Serves:` target is dead — re-propose the mapping or fix the ID.)
   - None of the above, and it is simply time to check standing — drift, `pin-stale`, or time elapsed since the last review → recommend **Review**.

   State your recommendation in bold, name the other stages as options, and wait for the user's stage choice (or explicit confirmation of your recommendation) before proceeding. Never present a bare menu with no bolded recommendation.

---

## Articulate

The humans name the objectives. You challenge and structure — you never author an objective yourself.

1. Ask the humans to state each candidate objective in their own words.
2. Apply the coach's **outcome-not-output** test to each one. Push back on anything that names an activity rather than a result; do not write it down until it names an outcome.
3. Structure each accepted objective into the pinned grammar: `## O<n> — <objective>`, numbered after the highest existing `O<n>` in the doc. Never renumber an existing objective.
4. Show the resulting section of `okrs-<quarter>.md` and get explicit approval before writing. The gate is the grammar plus the approval — both are required, neither alone is enough.
5. On approval, write the file and commit the change. This is the department's own doc in its own repo; no cross-repo PR is needed here.

---

## Refine

Each objective's key results go through the coach's full battery before they count as ratified.

1. For every objective still missing a ratified KR, propose candidate KRs and run each one through department-coach's battery — outcome-not-output, baseline, target-plus-date, controllability, falsifiability, vanity-metric — in order, one KR at a time.
2. Resolve the first failing test with one of the coach's four standard moves before moving to the next test on that KR. Never carry a failing KR forward unresolved.
3. Follow the coach's session discipline throughout: one decision at a time, 2–4 lines of context per option, your recommendation **bolded**, the human decides.
4. Close each KR with the committed-vs-aspirational split, named explicitly.
5. **Log every ratification in the same turn** to `<decisions_dir>/<date>-refine.md` — never batch logging to the end of the session. Log a human override exactly as `OVERRIDE: <item> passed without <thing>, by your call.` — never paraphrase it.
6. Once a batch of KRs is ratified, write them into `okrs-<quarter>.md` in the pinned grammar (`- O<n>.KR<n>: <baseline> → <target> by <date>`), show the diff, get approval, and commit.
7. **Gate.** Refine is done only when all three hold for every KR in scope: it passed the battery or carries a logged override, it carries its committed-or-aspirational label, and the ratified set is written to the quarter doc and approved. None of the three alone closes the stage.

---

## Translate

The department only *proposes* the objective→team mapping. A team accepts by merging the `Serves:` header into its own quarterly doc — you never write into a team repo except by PR, and every PR needs explicit approval before it exists.

1. Ask which PI is being planned (e.g. `2026-PI-4`), mirroring `/setup-department`'s quarter ask. If `{HUB}/context/department/pi-plan-<PI>.md` does not exist for that PI, copy `{HUB}/context/department/templates/pi-plan.md` to that path and update its heading to name the actual PI; if it exists, read it.
2. For each objective flagged by `serves-nothing` or `orphaned-objective` (or any objective the user wants remapped), propose which team or teams should serve it. Fill the proposal table's `Proposed teams` column; leave `Accepted (Serves: merged)` blank until a team's PR actually merges — that column is never fabricated ahead of the real merge.
3. Show the proposal table, get approval, then write and commit the department's own PI-plan doc.
4. For each accepted team, offer to prepare its acceptance PR: draft the `Serves: O<n>` header addition to that team's `<teams_root>/<team>/context/quarterly/*.md`, show the diff, and get explicit approval before creating anything. On approval: in the `<teams_root>/<team>` submodule checkout, branch (e.g. `awow/serves-<objective>`), commit the header addition, push the branch to the team repo's remote, and run `gh pr create` against that repo's default branch.
5. Tell the user plainly: the mapping is not accepted until each team's PR merges. Re-run this command's Ground step afterward — a merged `Serves:` header clears the matching `serves-nothing` / `orphaned-objective` finding.

---

## Review

Run partway through the quarter to check standing — graded on **KR movement, never on plan compliance**.

1. Run the check (this stage's own baseline read, distinct from Ground's earlier run this turn).
2. Run `git submodule update --remote` — working tree only, no gitlink commit yet. This pulls each team's latest quarterly-doc content into the local checkout so the next check reads current KR movement, not a stale snapshot.
3. Re-run the check against the freshly updated working trees. Present `drift`, `findings`, and KR movement read from each team's quarterly doc under `read_scope` — actual progress against each KR's baseline and target, not whether the team followed the stated plan to get there.
4. For each KR, reach one of four decisions — each produces its own artifact, never just a verdict in prose:
   - **Double-down.** Shift more of a team's next-cycle capacity toward the objective. Record the shift in the decisions log and carry it into the next PI proposal.
   - **Park.** The objective stays in `okrs-<quarter>.md` but is marked not-actively-served this quarter. Log it; leave every team's `Serves:` header exactly as it is.
   - **Reallocate.** Move a proposed team from one objective to another. Add a new proposal row at Translate; the team accepts by PR as usual — this is never a direct edit to a team's `Serves:` header.
   - **Re-bet.** Retire or rewrite the objective or its KRs. Follow with a Refine round on whatever gets rewritten before it counts as ratified again.

   Reach each decision following the coach's session discipline: one decision at a time, bolded recommendation, human decides. **Log every decision in the same turn** to `<decisions_dir>/<date>-review.md`; log overrides verbatim exactly as `OVERRIDE: <item> passed without <thing>, by your call.`
5. **State the tripwire plainly.** A `pin-stale` finding means the reconciliation mechanism itself failed to run on schedule — re-scope the mechanism (shorten the interval, fix what's blocking the check from running), never paper over it by re-running the check and moving on as if nothing happened.
6. Close by offering **one bump PR**: a single PR against this repo that commits the now-current submodule gitlinks, ratifying the checked state. On decline, run `git submodule update --checkout` immediately — the working tree never stays half-updated relative to what is actually committed.

---

## Behavioral boundaries

- **Ground runs every time.** No stage below runs without the check, the config-error guard, and the docs read first.
- **Exit 2 is a hard stop.** Never guess past a `CascadeConfigError` — show it verbatim and fix the named cause before retrying.
- **Never author an objective.** Articulate structures and challenges; the humans supply the words.
- **Never skip the battery.** A KR reaches `okrs-<quarter>.md` only after every test in the battery has been asked and resolved.
- **Propose, never write, into a team repo.** Translate's acceptance is a merged `Serves:` header on the team's side, produced only through an explicitly approved PR.
- **Grade movement, not compliance.** Review judges whether the number moved toward its target, never whether the team executed the plan as written.
- **Never leave the tree half-updated.** Review's closing move is binary: the bump PR lands, or `git submodule update --checkout` reverts the working tree — no third state.
- **Log in the same turn, every time.** Refine and Review ratifications and overrides are logged before the next decision starts, not batched to the end.
