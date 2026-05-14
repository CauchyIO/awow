# setup/ — first-time installation

Prerequisite for the `/setup-awow` agent command. Run **before** opening any agent session.

| Platform | Command (from the repo root) |
|---|---|
| macOS / Linux | `./setup/install.sh` |
| Windows (PowerShell) | `.\setup\install.ps1` |

Both scripts do the same thing:

1. Verify `uv` is installed (or tell you how to install it).
2. Install Python 3.12 locally via `uv python install`.
3. Create a `.venv` in the repo root (already in `.gitignore`).
4. Run `tools/gather.py` once to populate `.claude/` and `.github/` pointer stubs.

awow's tools are stdlib-only, so there is no requirements file and no third-party packages get installed.

Once the installer has run, open an agent session at the repo root (Claude Code: `claude`; GitHub Copilot: open the folder in VS Code) and invoke `/setup-awow` — that's where the board MCP, mission, conventions, and the rest get configured.
