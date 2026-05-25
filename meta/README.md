# meta/ — awow's own awow-on-awow workspace

This folder is the **real workspace where awow's maintainers run awow on awow**. It is not a demonstration or a mock-up: the mission, board config, conventions, and proposals here are awow's actual ones. When a maintainer runs an awow command against the project itself, it runs against this surface (`--root meta/`).

It exists because awow's own development can't live at the top level: the top-level `context/` ships to adopters as empty stubs (the template surface), so awow's real content has to live somewhere else. That somewhere is here.

## What lives here

```
meta/
├── setup-progress.md        # the wizard's state file for this workspace
├── context/
│   ├── team/                # awow's mission, members, conventions, style
│   ├── tooling/             # board.md and other tooling pinned for awow
│   ├── knowledge-base/      # durable rationale for awow's own work
│   └── company/             # neighbouring teams, stakeholders
└── proposals/               # real awow design proposals — drafts en route to GitHub issues
```

The shape mirrors the top-level `context/` and `proposals/` — that is the point. This is what a real adopter team's repo looks like after the wizard runs, because it *is* one.

## How it relates to the rest of the repo

- **Not the template surface.** The template is the top-level `context/`, which ships stubs. Adopters cloning via "Use this template" inherit those stubs and run `/setup-awow` against them.
- **Not the execution source of truth.** awow's work *executes* on the GitHub board (`CauchyIO/awow` issues, PRs, project). The proposals here are markdown drafts that become issues; once filed, the issue + PR are the record. This workspace holds the *context surface and proposal drafts*, not the live backlog.
- **Not Cauchy's client work.** Cauchy's client engagements run on Linear (`Cauchyio` workspace). This is awow product work only.
- **Not the regression fixtures.** The `/setup-awow` test corpus lives under `tests/setup-awow/fixtures/` as self-contained snapshots of a clean installation. Those fixtures are frozen and standalone — they are *not* derived from this workspace, so this surface is free to evolve without touching the suite.
- **Not in scope of `/awow-reset`.** That command resets the *template surface* between maintainer prompt-iteration runs; this workspace is preserved.

## For adopters cloning the template

You can delete this folder. It exists only for awow's own maintainers, holds nothing you need, and nothing in the template references it — nothing breaks when it is gone.

If you keep it, treat it as read-only reference material: "what does a fully-populated awow team repo look like?"
