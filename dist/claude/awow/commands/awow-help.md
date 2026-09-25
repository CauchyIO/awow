---
description: "Use when the user asks what awow can do here, what a command does, what to run next, or has just installed the plugin and does not know where to start."
phase: kickoff
argument-hint: "[--commands | <command> | what you want to do]"
prerequisites: []
removes_pain: "the I-have-the-plugin-what-do-I-type problem"
---

# /awow-help — what awow can do here, and what to do next

You explain the commands available in this repo and suggest the one next step, from what the repo actually is right now. Read, then answer; never write, install, register or ask.

**The catalog is your only source of command names.** Read `${CLAUDE_PLUGIN_ROOT}/context/tooling/command-catalog.md` first: every command awow ships, one line each, and the plugin it ships in. Never name a command that is not in it, and never describe a command in words other than its catalog line plus what you observed.

## Arguments

- **None** — where this repo stands, any problem and its fix, the one next step, and the names of the commands here. Short.
- **`--commands`** — the full table: every command with its flags and its catalog line, grouped by plugin.
- **A command name** (`/awow-help process-workitem`) — that command only: its catalog line, whether it is installed here, what it will ask for and what it writes, and the invocation for this repo's state.
- **A need in plain words** (`/awow-help I have meeting notes`) — the one command for it, or the plugin that carries it when it is not installed, or "awow has no command for that" when it does not.

## 1. Read the state — read-only, no questions

Read these and nothing more. Write no file, make no board write, install nothing, authenticate nothing; a question you would need answered is a finding to report.

- **Installed.** Which catalogued commands appear in your skill listing. Every `awow-workflows` command absent means that plugin is not installed here; say so once, by name, and never present its commands as available.
- **Configured.** Whether this is a git repository; whether `{ANCHOR}/context/tooling/board.md` exists; whether the root `AGENTS.md` frontmatter carries `anchor:` and, if so, whether `$AWOW_ANCHOR` or `.awow/anchor.json` resolves it; which of the four `{ANCHOR}/context/team/conventions/REQUIRED/` files and `{ANCHOR}/context/team/mission.md` exist. Presence is what matters; do not lint content.
- **Board.** Only when `board.md` exists: settle the board with the `board-target` skill, run the one identity-bearing read `/setup-awow --check` uses, and count the items assigned to the current user. A surface that is not loaded, not authenticated or serving another workspace is a finding, not a prompt — report it and go on without board state.
- **This session.** Whether the user stated a rule about how the team works earlier in this conversation.

Ignore `setup-progress.md` and `{PROJECT}/proposals/setup/` when you find them: an earlier awow's state, never read as state.

## 2. Say where the repo stands, and what is wrong

One plain sentence: what you found and what is missing, in the user's words. *"This repo has a board (Linear, team PAY) and its conventions; the `awow-workflows` plugin is not installed."* Name absent conventions or profile as things the first command that needs them will offer, never as gaps to fix first. Never say the situation names or value names `/setup-awow` uses internally.

Then one `Problems:` line — `none`, or each problem with its fix in a few words: a board surface not loaded or serving another workspace, an anchor that does not resolve, a `board.md` naming a surface that is not here. The fix is a pointer (`run /setup-awow`, `run /mcp`), never something you do.

## 3. Name what is available

Without `--commands`: one line naming the `awow` commands here, one line saying whether `awow-workflows` is installed (and what it adds, in a few words, when it is not), and one line pointing at `/awow-help --commands`. No table.

With `--commands`: one table for the `awow` commands and one for `awow-workflows` when it is installed, each row the command with its flags and its catalog line as written. When `awow-workflows` is absent, show no table for it — one line after the first table: what the bundle adds and the exact install command for this harness, quoted from the catalog's `Installing awow-workflows` table — never a guessed or hedged one. Mark a command whose prerequisite this repo plainly lacks; never hide it.

## 4. Suggest exactly one next step

Pick the first that applies, and give the exact invocation for this repo:

1. Not a git repository → `git init` here, or `cd` to the repository you meant.
2. No `board.md` and no `anchor:` → `/setup-awow <board-url>`. Put the `--anchor <git-url>` route for a team that keeps its awow context in a shared repo in the status sentence, never on the **Next:** line — that line carries one invocation.
3. Configured, but this machine lacks the board surface or the anchor checkout → `/setup-awow`, which asks only for the missing piece.
4. The user stated a team rule this session → `/update-context`.
5. Board readable and items are assigned to the user → `/my-work`, or `/process-workitem <id>` naming the top item when there is one that clearly needs them.
6. Board readable, nothing assigned → `/process-workitem <id>` on an item they name, or the `workitem-write` skill to create one.
7. Board not readable → the one-line fix from `/setup-awow --check`, then `/setup-awow`.

With a command name as the argument, the next step is that command's invocation for this state, or the reason it cannot run yet.

## Output

Open with the `# awow in <repo name>` heading, always, on every harness. The next step is the answer: put the **Next:** line directly under the heading, before anything else. Without `--commands`:

```markdown
# awow in <repo name>

**Next:** `<one invocation>` — <why, one line>

<one sentence: where the repo stands>

**Problems:** none — or: <problem> → <fix>

Commands here: `/setup-awow`, `/process-workitem`, `/my-work`, `/update-context`, `/awow-help`.
`awow-workflows` is not installed — it adds <a few words>. Run `/awow-help --commands` for what each command does and its flags.
```

About ten lines. With `--commands`, the same head, then the tables:

```markdown
## Commands — `awow`
| Command | Use when |
| --- | --- |
| `/<name> <hint>` | <catalog line> |

## Commands — `awow-workflows` <(installed | not installed — what it adds; how to install)>
| ... | ... |
```

With a command name or a need as the argument, the answer to that takes the **Next** slot. Add no other table or list, and no preamble about awow's philosophy: the reflex already carries it.

## Boundaries

- **Read-only, always.** No file, no board write, no install, no `.awow/` link, no question.
- **Catalog names only.** A command that is not in the catalog does not exist, whatever you remember.
- **One next step, first.** Several options is the problem this command exists to solve; a count table or a second suggestion is a second option.
- **The plugin beside the command.** Every `awow-workflows` command you name is named with its plugin, so an absent one is never mistaken for a missing feature.
