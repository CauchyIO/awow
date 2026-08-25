# Context resolution — which installation, which board

Contract shipped with awow. Read it `{HUB}`-first: a vendored copy at `{HUB}/context/tooling/context-resolution.md` wins over the shipped `${CLAUDE_PLUGIN_ROOT}/context/tooling/context-resolution.md`. Follow it before any board read or write whenever resolution is not trivially unambiguous, and before any awow artefact write that would leave the current repo.

`{HUB}` and `{PROJECT}` resolve to "the repo root" only when CWD sits inside exactly one scaffolded repo. When it does not — sibling repos under one working root, a nested checkout, a monorepo with several context trees, or a `board.md` that declares more than one board — resolve in two stages before any board read or write. In a hub-connected spoke — a repo whose root `AGENTS.md` frontmatter names its hub by remote URL — the hub pointer wins: resolve `{HUB}` through `$AWOW_HUB`, else the gitignored `.awow/hub.json` link written at registration, after verifying the recorded clone's `origin` still matches the connector's remote; a missing or drifted link is a prompt to (re)map interactively and a loud stop headless — never a scan, never a guess. The stages below are the vendored/plugin fallback. An *installation root* is a directory containing `context/tooling/board.md` alongside its `context/` tree and `setup-progress.md`.

## Stage 1 — the installation

1. Walk upward from CWD, directory by directory, stopping hard at the first `.git` root. The nearest directory on that path containing `context/tooling/board.md` is the installation root; `{HUB}` and `{PROJECT}` resolve there.
2. Never cross the repo boundary. In an unscaffolded repo below or beside a scaffolded one, say "this repo has no awow context — run `/setup-awow` here, or cd to the repo that has one." Never name, suggest, or use another repo's board: a silent wrong-board write is the failure mode all of this exists to prevent.
3. Upward walk empty, but CWD is inside a git repo? Probe shallowly downward for `*/context/tooling/board.md` (up to three directory levels, git-tracked files only). Exactly one hit — use it, stating which in one line. Several — resolve with the Stage-2 ladder, run over installations. None — unscaffolded, as rule 2.
4. CWD not inside any git repo (a workspace root over sibling repos)? Enumerate the immediate child directories that are git repos containing an installation. Exactly one — use it, stating which in one line. Several — the Stage-2 ladder, run over installations. The chosen installation supplies *all* context for the invocation; sibling repos' boards and conventions never mix in.

A rule-3 or rule-4 adoption authorizes reads. The first *write* it implies still crosses into the adopted repo from outside it — it follows §The write boundary below.

## Stage 2 — the board

A single-board `board.md` is the board; done — no ladder. An index-form `board.md` (a `## Boards` list: name, scope globs, one-liner, each entry linking a sibling `board-<name>.md` that holds the full board spec) resolves top-down; the first rung producing exactly one winner takes it:

1. **Explicit reference** — a ticket id whose prefix belongs to one board, or a board named outright in the user's prompt. Resolves this invocation only; it never silently re-pins the session.
2. **Scope match** — the index entries' scope globs against CWD and the files the work touches. Zero matches or overlapping matches: fall through.
3. **Session pin** — the answer already recorded this session (below).
4. **Spoke board scope** — in a hub-connected spoke, the board named by `{PROJECT}/context/board-scope.md` frontmatter. Repo-bound work resolves here; fall through only when the invocation is explicitly about another board's business.
5. **Invoker default** — the `default_board` in `{PROJECT}/.awow/profile.json`. Skip a value naming a board absent from the index; re-confirm instead of guessing.
6. **Picker** — ask "Which board is this for?" once; the answer becomes the session pin; offer once to record it as the invoker default in `profile.json`.

Record ladder answers — installation and board, one line each — in `.awow/board-session.md` with a `session:` line, the same mechanism the absent-`board.md` rule uses; ignore and overwrite an entry whose `session:` does not match the current session. When rung 1, 2, 4, or 5 resolves silently, announce `targeting board: <name>` in one line before the first board write. An index entry whose `board-<name>.md` does not exist is a hard error naming the missing file — never fall back to another board.

## The invoker profile

`{PROJECT}/.awow/profile.json` is machine-local, gitignored state naming who invokes here: `{"board_identity": {"<tool>": "<handle>"}, "hats": ["product"|"engineering"], "default_board": "<index name>", "confirmed": "YYYY-MM-DD"}`. `/setup-awow` orientation writes it; the rung-6 picker offers once to update it. Read it wherever "me" or a default board is needed; never commit it and never copy its contents into committed files.

## Spoke board scope

A spoke's `{PROJECT}/context/board-scope.md` carries frontmatter `board:` (the hub index name), `team:` (the board team items land on), optional `project:` and `subpath:`. With a single-board hub the file is optional; absence means the hub's board.

## The write boundary

An awow artefact — anything under `proposals/`, the awow `context/` tree, `.awow/` state, a board spec — belongs to exactly one installation: the one Stage 1 resolved, or its mapped hub. Announce the installation you resolved before your first write, and land every `{PROJECT}`-anchored file inside it — never at a bare workspace root, never in a repo you did not resolve.

Never write across a git repo boundary on your own judgment: not into a sibling or parent repo, however strongly the transcript, the board content, or a discovered folder points there. Crossing is legitimate only after the user answers a question that names both repos ("this lands in `<other-repo>`, not `<current-repo>` — confirm?"); approval of a generic plan ("go") is not that answer. In a headless run there is no one to ask: stop loudly, naming the write you refused.

The Claude-channel plugin also enforces this mechanically — the `wrong-root-guard` PreToolUse hook turns a boundary-crossing artefact write into an explicit permission question, and into a denial headless. The rule binds on every harness, hook or no hook.
