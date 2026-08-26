# Prompt taxonomy

One vocabulary, two directions: eight intent labels you prompt *with*, and the same eight that `/awow-usage-coach` reads your sessions back *through*.

> **TL;DR** — Every prompt is doing one of eight things: `investigate`, `plan`, `propose`,
> `implement`, `refine`, `verify`, `document`, `inform`. Name which one *before* you type and the
> prompt gets sharper now; `/awow-usage-coach` classifies your recorded sessions (*traces*) into
> the same eight, so the reflection later arrives in a language you already use. If you can't name
> the move, default to `investigate` — not knowing *is* the signal that you can't plan yet.

## The loop this closes

Forward, this is a prompting discipline you apply in the moment. Backward, it is the lens
`/awow-usage-coach` uses to report your sequence and edit patterns — self-coach mode for one
person, team-nudge across the team. If the two halves used different words the loop would not
close: you could not recognise yourself in the analysis.

## Why name the move at all

The intent name primes the agent's disposition (`verify` primes test-running, `propose` primes
drafting-not-applying) and forces you to commit to a posture instead of letting the session drift.

```
DRIFTING                              NAMED INTENT
can you look at the auth module       investigate: auth module — list every
and tell me what's going on           caller of verifyToken() and note any
maybe also suggest a fix?             that skip the expiry check.
                                      (then I'll plan the fix.)
```

## The eight intents

Eight labels plus an `other` bucket. They are vocabulary-agnostic — they work whether or not the
team uses any awow slash-commands.

| Intent | What you're doing | Opening that fits |
| --- | --- | --- |
| `investigate` | Gathering information; reading code; mapping the terrain. | *"find every place we call X / explain how Y is wired"* |
| `plan` | Sketching what you'd do, without committing to a change. | *"what would it take to add Y? list the steps"* |
| `propose` | Drafting the change to *review* before doing it — the awow staple. | *"draft a proposal in `proposals/Y.md`"* |
| `implement` | Making the change in the real files. | *"apply that proposal to `Y.ts`"* |
| `refine` | Iterating on something just made — tightening, polishing, narrowing. | *"tighten the error message; keep the API the same"* |
| `verify` | Checking it works — tests, types, the real app, a screenshot. | *"run the tests / open it and confirm Z renders"* |
| `document` | Recording the *why*, for the future reader (often you). | *"add a why-comment / write a `context/knowledge-base/` entry"* |
| `inform` | Telling the agent something — a status, decision, observation. | *"FYI Linear says X is in-progress; don't recreate the ticket"* |

The labels are deliberately coarse: posture, not procedure. One `implement` can edit twenty files;
one `investigate` can read fifty. The point is self-awareness about the move, not classification
accuracy.

## The rhythms that recur

Intent *sequences* — pairs and triples through a session — tell you more than any single label.

| Rhythm | What it tells you |
| --- | --- |
| `plan → propose → implement` | Healthy: the textbook awow rhythm. Cheap iteration in markdown, applied once it's right. |
| `implement → verify → refine` | Healthy: TDD-shaped, when the change actually ships. |
| `investigate → plan` | Healthy: read the terrain, then commit to a route. |
| `implement × 3+`, no `verify` | Nudge: execution without checks; correlates with `refine` later (rework). |
| `investigate × 3+` | Nudge: fine on unfamiliar code, expensive when the answer was already in `context/knowledge-base/`. |
| `inform`-heavy | Nudge: talking *to* the agent rather than directing it. Reactive when no `plan` anchors it. |
| `other > 30%` | Nudge: the taxonomy is under-capturing how you talk — the gap itself is the signal. |

## The small ritual

Open every session with a one-liner that names the intent:

```
plan: what would it take to add cancel-on-blur to the
search input — list the touch points, no code yet.

verify: run the auth tests and tell me which fail
on the new token-expiry branch.
```

The label is for *you* first (it forces clarity), the agent second (it adjusts posture), the coach
third (the loop closes).

## When "other" takes over

A large `other` share does not mean the taxonomy is broken — it means your style isn't the median
style it was tuned for, and that is signal too. The coach reports it honestly and quotes a handful
of those prompts, so you can decide whether to nudge your phrasing or accept it. The coach doesn't
over-classify: very short follow-ups and conversational acknowledgements genuinely don't fit, and
forcing them in would just make the report wrong.

## Sources of truth

- [`.agents/skills/awow-usage-coach/SKILL.md`](../.agents/skills/awow-usage-coach/SKILL.md) — the canonical intent definitions and the classification rules
- [`.agents/commands/daily-digest.md`](../.agents/commands/daily-digest.md) — the other consumer, for intent-tagged synthesis
- Companion guides: [trace analysis](guide-trace-analysis.md) — the export-then-assess pipeline the coach runs in; [session timeline](guide-session-timeline.md) — the visual read of the same sessions
