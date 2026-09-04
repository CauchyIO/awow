#!/usr/bin/env bash
# git-init the fixture repo, then require a markitdown runner: without uv or
# markitdown on PATH the scenario cannot measure the prompt, so exit 1 and let
# the runner compose indeterminate (stage: setup) instead of a graded fail.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
if ! command -v uv >/dev/null 2>&1 && ! command -v markitdown >/dev/null 2>&1; then
  echo "setup: neither uv nor markitdown on PATH — cannot run office-ingest scenarios" >&2
  exit 1
fi
