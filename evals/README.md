# Running these evals — and yours: the night eval protocol

This directory contains awow's skill eval suite and its portable git submission
protocol. This repo's Actions use the small eval API; a team that prefers no API
can submit the same pinned suite by tag and receive results by branch as described
below. No credentials are stored in the repo.

## The whole pattern

**1. Write an eval set** — one directory per scenario:

```
evals/scenarios/<scenario>/
  persona.md          # who the simulated user is, and their standing rules
  opening.md          # the first user message
  fixture/            # the workspace tree the session starts in
  observe-writes.txt  # which paths the flow MAY touch (violations are scored)
```

plus one rubric per scenario in a shared directory the judge reads:

```
evals/rubrics/<scenario>.md   # how the judge grades that flow's outcome
```

**2. Write a request** — `eval-request.yaml` at the repo root, flat keys only:

```yaml
contract: eval/v1
environment: night-standard@1
suite: evals
scenarios: [setup-awow-walkthrough]
tiers: [worker]
reps: 1
budget_tokens_total: 400000
```

Routes are capability tiers (`bulk` | `worker` | `flagship`) or one of the
service's fixed model-seat aliases, never provider model ids. The environment
owns what each route resolves to.

**3. Submit — push a tag.** This is the entire submission:

```
git tag eval-request/my-first-run
git push origin eval-request/my-first-run
```

Do it from your terminal, from CI on merge, from cron at midnight, from a
release script — *any trigger you already have works, because the submission
primitive is a git tag.* The tagged commit pins the request and every asset it
names; the service only ever executes pinned SHAs.

**4. Receive — a branch comes back.** The service pushes `night/eval-<id>` to
your repo: `result.json` (per scenario × tier × rep: outcome scores, process
scores, judge identity) and `summary.md` for humans. Invalid requests come back
the same way, as a rejection with the reason. Transcripts stay service-side;
results carry scores and quoted evidence only.

## What the service enforces (so you don't have to)

Requests are clamped, never trusted: tier and budget ceilings from your
registration, pinned refs only, every named asset must exist at the tagged SHA.
Runs execute in sandboxed agent sessions with fixed wall/turn/size caps. One
malformed request refuses loudly without affecting anything else.

## Want your repo to run against our service?

Submitting wakes the evaluator; it reads **registered repos only** — a tag on
an unregistered repo is simply invisible. Registration is: your repo name, your suite path, a tier
ceiling, and a run budget (credits). Cauchy operates the service and maintains
this protocol — open an issue on this repo to ask about registration.

## This repo's own triggers

See `.github/workflows/evals.yml` — a maintainer button plus an automatic
gate run on PRs that touch the flows or the eval set. It delegates submission,
polling, scoring, and the native step summary to `.github/actions/eval-run`.

The PR workflow reports changes per skill. `.github/workflows/evals-weekly.yml`
is the secondary model-support view and runs only the six Pi seats marked
`weekly` in `model-seats.json`.

Maintainers run the complete twelve-seat snapshot locally, roughly biweekly:

```sh
python3 evals/campaign.py run --evaluator-root /path/to/overnight/harness --model-resolution /path/to/model-resolution.json --profile snapshot --out /tmp/awow-evals
```

After reviewing `campaign.json` and explicitly choosing qualifying roles, publish
only the clean README table:

```sh
python3 evals/campaign.py publish /tmp/awow-evals/campaign.json --performance-baseline <seat-id> --automated-seat <seat-id> --readme README.md
```

That command edits only the snapshot markers; it does not commit, push, or run
models.
