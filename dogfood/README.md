# dogfood/ — awow applied to itself

This folder is awow's own usage of the agentic way of working. The team operating against this folder is **Cauchyio**, maintainers of this starter pack. Read it as a worked example of what an adopter team's `context/` looks like once `/setup-awow` has run end-to-end.

## What lives here

```
dogfood/
├── setup-progress.md        # the wizard's state file for this dogfood run
├── context/
│   ├── team/                # mission, members, conventions, style — populated as the wizard progresses
│   ├── tooling/             # board.md and (eventually) other tooling pinned for this team
│   ├── knowledge-base/      # durable rationale for awow's own work
│   └── company/             # neighbouring teams, stakeholders
└── proposals/
    └── setup/               # the wizard's drafts before each artefact is landed
```

The shape mirrors the top-level `context/` and `proposals/` — that is the point. Everything you see populated here is what a real adopter team's repo would look like after the wizard runs.

## What this folder is **not**

- It is **not** the template surface. The template surface is the top-level `context/`, which ships stubs. Adopters cloning via "Use this template" inherit those stubs and run `/setup-awow` against them.
- It is **not** in scope of `/awow-reset`. That command resets the *template surface* between maintainer prompt-iteration runs; `dogfood/` is the awow team's actual lived state and is preserved.

## For adopters cloning the template

You can delete this folder. It exists only for awow's own maintainers. Nothing in the template references it; nothing breaks when it is gone.

If you keep it, treat it as read-only reference material: "what does a fully-populated awow team repo look like?"
