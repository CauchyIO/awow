# Activity collection — the shared day-snapshot step

The single upstream step that gathers a day's activity **once**, so every lens that
reads a day — the `/daily-digest` synthesis, a future KB-mining extraction — works
off one snapshot instead of re-querying the board and code surfaces per lens.

This file is a **contract, not a command.** Users invoke lenses (`/daily-digest`),
not the collector. A lens opens by running this step; a routine that runs several
lenses collects once and the rest reuse the snapshot.

Collection is **read-only** and **board-agnostic**: it reads *which* board, code
surface, and chat surface to query from `context/`, so it behaves identically for
any adopter (Linear / Azure DevOps / Jira / GitHub Issues) with no provider-specific
logic here.

---

## Inputs (all from `context/`, never hardcoded)

| Input | Read from | Used for |
|---|---|---|
| Board surface | `context/tooling/board.md` (Tool & wiring, state machine, hierarchy) | Which board tool + MCP/CLI surface to query, and how to read its states/fields. |
| Code-hosting surface | `context/tooling/board.md` (Tool & wiring) + the repo's git remote | Which code host + repos to pull commits/PRs/reviews from. |
| Chat surface (optional) | `config/chat-to-project.yaml` if present | Channel messages, mapped to projects. |
| Private-team exclusion | the private-team rule in `context/team/conventions/REQUIRED/labels.md` | What must never reach a shared output (applied here, once). |

If `context/tooling/board.md` does not exist, collection cannot run — stop and tell
the user to run `/setup-awow` Step 1 first.

---

## What it collects — the superset (deep by default)

Collect the deep view once, so the snapshot serves both a shallow lens (digest) and
a deep lens (mining). A lens takes only what it needs.

### A. Board activity (target day)

Every issue touched on the day, via the board surface in `board.md`. For each:
identifier, title, current state, project/area, and the **activity**
(who touched it, state transitions, issues created) **and** the **deep content**
(description, full comment bodies, the readable state-history timeline).

Sanity-check empty results. A team-filtered query returning zero issues on a day you
know was active means the query is wrong (mistyped team, stale credentials) —
investigate before treating empty as truth.

### B. Code activity (target day)

Every repo with activity via the code-hosting surface. For each: commits (with
messages), PRs opened/merged/reviewed, contributors, **and** — for the deep lens —
the PR body, review bodies, and the unified diff (bounded; see *Diff cap*). Map code
activity to board issues where derivable (linked branches, issue IDs in commit
messages / PR descriptions).

### C. Chat / channel messages (target day, optional)

Only if `config/chat-to-project.yaml` is wired. Channel messages mapped to projects.
**Always exclude meeting transcripts** — they carry personal data and are handled
separately by `/process-transcript`.

### Diff cap

The diff is the one expensive field. Cap it per PR (default ~6000 chars, truncate
with a marker). A digest lens ignores diffs entirely; a mining lens reads the capped
diff. The cap lives here so peak snapshot size is bounded on a pathological day.

---

## The private-team gate — applied once, here

Apply the private-team exclusion (`context/team/conventions/REQUIRED/labels.md`)
**at collection**, before anything is written to the snapshot. Data from a private
surface (e.g. a leadership-only board) does not flow into shared outputs. Free-text
fields — comments, commit messages, PR titles — can *mention* a private identifier
even when the item itself is shared; scrub those too. Because the gate runs once
here, no downstream lens can leak private data, and there is one implementation to
keep correct.

(If a lens needs private data for a private-only rendering — e.g. the digest's
per-person takeaways for someone with access — it pulls that internally and excludes
it from shared rendering; that is the lens's concern, not the shared snapshot's.)

---

## Output — the day snapshot

Write a normalised, board-agnostic snapshot to `activity/YYYY-MM-DD.json`. The shape
is provider-independent so lenses never branch on which board produced it:

```json
{
  "date": "YYYY-MM-DD",
  "sources": {
    "board": { "status": "ok|error", "scope": "…", "items": [ /* see below */ ] },
    "code":  { "status": "ok|error", "scope": "…", "items": [ … ] },
    "chat":  { "status": "ok|absent|error", "scope": "…", "items": [ … ] }
  }
}
```

Each item is a normalised record with a shallow surface every lens can read plus a
`payload` carrying the deep content:

```json
{
  "kind": "board.issue | code.pr | code.commit | chat.message",
  "ref": "<TEAM>-123 | <repo>#45 | <sha> | <channel-ts>",
  "actor": "<who>",
  "title": "<short subject>",
  "activity": ["2026-07-01: In Progress → In Review", "comment by …", "merged"],
  "payload": { "description": "…", "comments": ["…"], "diff": "…(capped)" }
}
```

- **Shallow projection** (digest): read `kind / ref / actor / title / activity`.
  Never load `payload.diff` into synthesis context.
- **Deep projection** (mining): read `payload` for the full text/diff.

Snapshots are ephemeral working state — treat `activity/` as scratch (gitignored).
The durable records are the lens outputs (the digest file, the KB candidates).

---

## Reuse check

Before collecting, check for `activity/YYYY-MM-DD.json`. If it exists, reuse it
(a peer lens already collected the day). Only re-collect if the user explicitly asks
to refresh. This is what lets a routine run digest + mining while querying the board
and code surfaces exactly once.

---

## Failure semantics — isolate per source, report honestly

- **Per-source isolation.** One dead source must not block the others. Collect each
  source independently; on failure, log it with full context and record
  `status: "error"` for that source — never silently swallow, never invent data.
- **Fatal vs. partial.** A hard auth failure (the surface returns 401/403) or a
  crash is fatal — stop, surface the error, do not write a half-snapshot the lenses
  would trust. A source that returned partial/empty but did not hard-fail is a
  non-fatal degradation — record its `status` and proceed; the lens reflects it in
  its Data Sources section.
- **Chat is best-effort.** All channels failing is a banner in the consuming lens,
  not a collection failure.

---

## How lenses use this

A lens's data-collection phase becomes: *"Run the activity-collection step (or reuse
today's snapshot per the reuse check). Then project the view I need."* The lens owns
its projection depth and its output; collection owns the one query pass, the
snapshot schema, and the private-team gate.
