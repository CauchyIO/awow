---
name: board-target
description: "Use before any board read or write, or whenever a command names the board, to settle which awow installation and which board you are acting on — including when board.md is missing or names several boards."
---

# board-target — which installation, which board

Every board read and every board write starts here. Resolve the target once, record it, and reuse it for the rest of the session; a command that reads the board stops after this skill, a command that writes continues into `workitem-write`.

**Never cross the repo boundary, and never use another repo's board.** A silent wrong-board write is the failure this skill exists to prevent.

`{ANCHOR}` and `{PROJECT}` resolve to the repo root only when CWD sits inside exactly one scaffolded repo. When it does not — sibling repos under one working root, a nested checkout, a monorepo with several context trees, or a `board.md` that declares more than one board — resolve in two stages. In an anchored repo the anchor pointer wins; these rules are the vendored and plugin fallback. An *installation root* is a directory `<dir>` for which `<dir>/context/tooling/board.md` exists, alongside the rest of `<dir>/context/`.

## 1. The installation

1. Walk upward from CWD, directory by directory, stopping hard at the first `.git` root. The nearest `<dir>` on that path with a `<dir>/context/tooling/board.md` is the installation root; `{ANCHOR}` and `{PROJECT}` resolve there.
2. In an unscaffolded repo below or beside a scaffolded one, say "this repo has no awow context — run `/setup-awow` here, or cd to the repo that has one." Never name, suggest, or use another repo's board.
3. Upward walk empty, but CWD is inside a git repo? Probe shallowly downward for `*/context/tooling/board.md` (up to three directory levels, git-tracked files only). Exactly one hit — use it, stating which in one line. Several — resolve with the section-2 ladder, run over installations. None — unscaffolded, as rule 2.
4. CWD not inside any git repo (a workspace root over sibling repos)? Enumerate the immediate child directories that are git repos containing an installation. Exactly one — use it, stating which in one line. Several — the section-2 ladder, run over installations. The chosen installation supplies *all* context for the invocation; sibling repos' boards and conventions never mix in.

## 2. The board

A single-board `board.md` is the board; done — no ladder. An index-form `board.md` (a `## Boards` list: name, scope globs, one-liner, each entry linking a sibling `board-<name>.md` that holds the full board spec) resolves top-down; the first rung producing exactly one winner takes it:

1. **Explicit reference** — a ticket id whose prefix belongs to one board, or a board named outright in the user's prompt. Resolves this invocation only; it never silently re-pins the session.
2. **Scope match** — the index entries' scope globs against CWD and the files the work touches. Zero matches or overlapping matches: fall through.
3. **Session pin** — the answer already recorded this session (section 4).
4. **Anchored board scope** — in an anchored repo, the board named by `{PROJECT}/context/board-scope.md` frontmatter. Repo-bound work resolves here; fall through only when the invocation is explicitly about another board's business.
5. **Invoker default** — the `default_board` in `{PROJECT}/.awow/profile.json`. Skip a value naming a board absent from the index; re-confirm instead of guessing.
6. **Picker** — ask "Which board is this for?" once; the answer becomes the session pin; offer once to record it as the invoker default in `profile.json`.

**The resolved board is the only board for this invocation.** Read, cite, and write that board alone; an item on another board in the index is not this invocation's business unless the user names it. An index entry whose `board-<name>.md` does not exist is a hard error naming the missing file — never fall back to another board. When `board.md` declares a board-team filter for a shared board, scope reads to the filter.

## 3. An absent `board.md` is a question, not a stop

Infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess from a GitLab, Bitbucket, or Azure DevOps remote; those map to several products, so ask. With no remote, or with `gh` absent or unauthenticated, ask once which board they use and how to reach it, and do not offer the `gh` path. A board URL the user gave to another command earlier in this session is a candidate, not an answer: name it in the one question ("Use <url>?"). Offer `/setup-awow <board-url>` to make the answer durable; never write `{ANCHOR}/context/tooling/board.md` yourself.

## 4. Record once, announce once

Record every answer from sections 1–3 — installation and board, one line each — in `.awow/board-session.md` with a `session:` line, and read it rather than asking twice. Ignore and overwrite an entry whose `session:` does not match the current session. When rung 1, 2, 4, or 5 resolves silently, announce `targeting board: <name>` in one line before the first board write.

## 5. The invoker and the anchored scope

`{PROJECT}/.awow/profile.json` is machine-local, gitignored state naming who invokes here: `{"board_identity": {"<tool>": "<handle>"}, "hats": ["product"|"engineering"], "default_board": "<index name>", "confirmed": "YYYY-MM-DD"}`. `/setup-awow` orientation writes it; the rung-6 picker offers once to update it. Read it wherever "me" or a default board is needed; never commit it and never copy its contents into committed files.

An anchored repo's `{PROJECT}/context/board-scope.md` carries frontmatter `board:` (the anchor index name), `team:` (the board team items land on), optional `project:` and `subpath:`. With a single-board anchor the file is optional; absence means the anchor's board.
