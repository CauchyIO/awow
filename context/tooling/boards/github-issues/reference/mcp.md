# GitHub Issues — MCP (and `gh` CLI alternative) reference

Two supported read/write surfaces. Pick one. The operating model only requires that *some* surface gives the agent read+write access to Issues, Projects, and Pull Requests.

## Option 1 — GitHub MCP server (full-feature, PAT-managed)

**Source docs:** The official GitHub MCP server at [github.com/github/github-mcp-server](https://github.com/github/github-mcp-server). Repo README has current install steps.

Read-write semantics required.

### Install — Claude Code

GitHub's MCP can run as a remote HTTP server or locally:

```bash
claude mcp add --transport http github-server https://api.githubcopilot.com/mcp/
```

Auth uses a GitHub PAT (or OAuth via the remote server). Confirm against the repo README before running.

### Install — Copilot

`.vscode/mcp.json`:

```json
{
  "servers": {
    "github-server": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

Confirm against the github-mcp-server repo README.

### Verify

1. List issues from a known repo to verify read access.
2. A no-op write on a scratch issue (set a label that's already set) to verify write access.
3. Record the verification status in `context/tooling/board.md`.

## Option 2 — `gh` CLI (lighter; reuse existing GitHub auth)

If the user already has `gh` installed and authenticated for the org/repo, the agent can shell out to it via the harness's Bash tool. This is what awow's own `meta/` workspace uses — see `meta/context/tooling/board.md` for a worked example.

Trade-offs:

- ✅ No additional PAT to manage; reuses `gh auth`.
- ✅ Works in any harness with shell access (Claude Code, Copilot, Cursor).
- ⚠️ Slower than an in-process MCP; each call is a subprocess.
- ⚠️ No push notifications or streaming — strictly request/response.
- ⚠️ The agent has to know which `gh` invocations are available; commands have to be drafted in the `/process-workitem` prompt explicitly.

### Setup

```bash
# Verify gh is installed and authenticated
gh auth status

# Required scopes for the agentic operating model:
gh auth refresh -s repo,project,read:org
```

Scopes covered: `repo` (Issues + PRs), `project` (Projects v2), `read:org` (team membership). `workflow` is optional, only needed if the agent triggers Actions.

### Verify

1. `gh repo view <owner>/<repo>` — read access.
2. `gh project list --owner <owner>` — Projects v2 read access.
3. A no-op write on a scratch issue (`gh issue edit <num> --add-label <existing-label>`) — write access.
4. Record `surface: gh-cli` in `context/tooling/board.md`.

### When the wizard picks this option

If the user expresses friction at the MCP install step ("I don't want another PAT" / "I'm not on Copilot licence" / "I'd prefer not to install another local service"), offer the `gh` CLI surface as the alternative. Record the choice as `surface: gh-cli` in `board.md`; downstream commands check this and use `gh` calls instead of MCP tool invocations.

## Branch naming

GitHub does not auto-generate branch names from Issues (the in-app "Create a branch" button does, but it is opt-in). Convention:

`{user}/{issue-number}-{slug}` — e.g. `casper/908-board-config-assistant`

For repos using Linear-style numbering, prefix with the repo identifier: `casper/awow-908-...`.
