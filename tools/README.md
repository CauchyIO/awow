# tools/

Python and shell scripts that build, check, and release awow. Most run in CI or the release workflow; the agent needs none of them to function day-to-day.

## Build and publish

| Script | Purpose | When it runs |
|---|---|---|
| `gather.py` | Build `.agents/` into one self-contained plugin per harness, under `dist/<harness>/<plugin>/` | After edits to `.agents/`; `--check` runs in CI |
| `gather_m365.py` | Render `.agents/` + `context/` into an M365 Copilot declarative-agent package | Via `python tools/gather.py --surface m365` |
| `sync-dist.sh` | Mirror the committed `dist/` into `CauchyIO/awow-dist` and open a sync PR there | Release workflow; by hand with `--apply` |
| `check-dist-published.py` | Fail when the published `awow-dist` payload is behind this checkout | CI, on pushes to `main` |
| `release-notes.py` | Draft a release's `CHANGELOG.md` section from merged PR titles; `--verify` checks it is present | Bump PR (`--changelog`); CI (`--verify`); release workflow |

## Checks

| Script | Purpose | When it runs |
|---|---|---|
| `lint-paths.py` | Fail if a shipped prompt uses a bare `context/`, `tools/` or `proposals/` path instead of a path token | CI |
| `lint-links.py` | Fail if a tracked Markdown file links to a relative path that does not exist | CI |
| `validate-evals.py` | Statically validate the eval suites under `tests/` — layout, checks scripts, rubrics | Before a `/test-awow` run, or after editing a suite |
| `cascade_check.py` | Read-only cascade sweep of a department repo: team registry, `Serves:` linkage, pin freshness | Via `/okr-cascade`; ships in the payload |

## Session analysis

| Script | Purpose | When it runs |
|---|---|---|
| `session_timeline.py` | Build an interactive timeline + meta-analysis of a project's Claude Code sessions from `~/.claude/projects/` logs (no tracing needed) | Via `project-timeline`; see `guides/guide-session-timeline.md` |
| `mlflow_reader.py` | The one reader for an `mlflow-export` directory; `session_timeline.py` and `awow-usage-coach` import it | Imported, not run directly |

`session_timeline.py` ships with `session_timeline_template.html`, the self-contained view it fills.

## Skeletons

These document their intended shape and are not implemented yet:

| Script | Purpose | Becomes real when |
|---|---|---|
| `validate-context.py` | Lint `context/` for staleness and missing required files | Staleness becomes a real signal for a team |
| `distribute.py` | Push core `AGENTS.md` updates into sibling repos | A team runs awow across more than one repo |
| `bootstrap-claude-md.py` | Generate a team `AGENTS.md` from the stub | Not planned: `/setup-awow` writes a short `AGENTS.md` pointer instead |

## Git hooks

`hooks/pre-push` blocks a push whose content matches a pattern in `hooks/leak-patterns.txt` — material derived from private session traces that does not belong in this public repo. Install it with `cp tools/hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push`.

## Convention

Each script is invokable as `python tools/<name>.py` with optional `--check` for dry-run mode where applicable.
