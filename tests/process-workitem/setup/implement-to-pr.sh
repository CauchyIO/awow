#!/usr/bin/env bash
# implement-to-pr: the scratch is a git repository on main with one commit and no remote, so a
# branch and a commit are possible and a PR is not.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git init -q -b main
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
