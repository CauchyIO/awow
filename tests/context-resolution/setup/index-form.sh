#!/usr/bin/env bash
# The resolution walk needs a real repo boundary: init a git repo at the
# scratch root and commit the fixture so tracked-file probes see it.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
