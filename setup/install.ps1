# awow installer (Windows / PowerShell)
#
# Sets up Python via uv, creates a .venv, and runs the initial pointer-stub
# gather so .claude/ and .github/ are populated. Mirror of install.sh for
# Unix systems.
#
# This is the prerequisite for the /setup-awow agent command: run it once
# after cloning, then open an agent session and invoke /setup-awow.
#
# All awow tools are stdlib-only — there is no requirements file to install.
# This script exists so a first-time user without a Python toolchain can get
# from `git clone` to a working repo with a single command.
#
# Usage (from the repo root, in PowerShell):
#   .\setup\install.ps1
#
# If PowerShell refuses to run the script because of execution policy, you
# can scope a bypass to this one invocation:
#   powershell -ExecutionPolicy Bypass -File .\setup\install.ps1
#
# Prerequisites: uv (https://docs.astral.sh/uv/). If uv is missing, this
# script prints the install command and exits — it does not run a remote
# bootstrap on your behalf.

$ErrorActionPreference = 'Stop'

$PythonVersion = '3.12'
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RepoRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host @'
uv is not installed.

awow uses uv to manage a local Python interpreter and a .venv inside the
repo so you do not need a system-wide Python. Install uv first, then re-run
.\setup\install.ps1:

  Windows:        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  winget:         winget install --id=astral-sh.uv -e
  Scoop:          scoop install uv

See https://docs.astral.sh/uv/getting-started/installation/ for alternatives.
'@
    exit 1
}

Write-Host "[1/3] Ensuring Python $PythonVersion is available via uv..."
uv python install $PythonVersion --quiet

Write-Host "[2/3] Creating .venv ..."
uv venv --python $PythonVersion --quiet

Write-Host "[3/3] Running initial pointer-stub gather..."
uv run --no-project python tools/gather.py

Write-Host @'

awow installed.

Next steps:
  1. Open an agent session at the repo root:
       Claude Code:    `claude` in this directory
       GitHub Copilot: open VS Code in this directory
  2. Run /setup-awow and answer the wizard's questions. It will walk you
     through wiring the board MCP (Linear / Jira / Azure DevOps / GitHub
     Issues) and the rest of the configuration.

If you re-edit .agents/ later, run `uv run python tools\gather.py` to
re-mirror the pointer stubs into .claude/ and .github/.
'@
