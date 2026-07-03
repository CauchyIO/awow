#!/usr/bin/env bash
#
# awow installer — sets up Python via uv, syncs the project .venv, and runs
# the initial pointer-stub gather so .claude/ and .github/ are populated.
#
# This is the prerequisite for the /setup-awow agent command: run it once
# after cloning, then open an agent session and invoke /setup-awow.
#
# The core tools/ are stdlib-only, but some skills (e.g. mlflow-export) add
# third-party deps to the project. `uv sync` creates the .venv and installs
# whatever pyproject.toml declares — adopters add new deps with `uv add <pkg>`.
#
# Usage (from the repo root):
#   ./setup/install.sh
#
# Prerequisites: uv (https://docs.astral.sh/uv/). If uv is missing, this
# script tells you how to install it and exits — it does not run a curl|sh
# bootstrap on your behalf.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_VERSION="3.12"

if ! command -v uv >/dev/null 2>&1; then
  cat <<'EOF'
uv is not installed.

awow uses uv to manage a local Python interpreter and a .venv inside the
repo so you do not need a system-wide Python. Install uv first, then re-run
./setup/install.sh:

  macOS / Linux:  curl -LsSf https://astral.sh/uv/install.sh | sh
  Windows:        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  Homebrew:       brew install uv
  pipx:           pipx install uv

See https://docs.astral.sh/uv/getting-started/installation/ for alternatives.
EOF
  exit 1
fi

echo "[1/3] Syncing project (installs Python $PYTHON_VERSION, creates .venv, installs deps)..."
uv sync --python "$PYTHON_VERSION" --quiet

echo "[2/3] Running initial pointer-stub gather..."
uv run python tools/gather.py

echo "[3/3] Recording the awow version baseline (tools/awow.lock.json)..."
uv run python tools/awow_lock.py backfill

cat <<'EOF'

awow installed.

Next steps:
  1. Open an agent session at the repo root:
       Claude Code:    `claude` in this directory
       GitHub Copilot: open VS Code in this directory
  2. Run /setup-awow and answer the wizard's questions. It will walk you
     through wiring the board MCP (Linear / Jira / Azure DevOps / GitHub
     Issues) and the rest of the configuration.

If you re-edit .agents/ later, run `uv run python tools/gather.py` to
re-mirror the pointer stubs into .claude/ and .github/.

To add a Python dependency a skill needs:
  uv add <package>            # records it in pyproject.toml + uv.lock
  uv sync                     # rehydrates the .venv on another machine
EOF
