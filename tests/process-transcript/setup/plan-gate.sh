#!/usr/bin/env bash
# Board writes in this suite edit the fixture board file; a real repo boundary
# keeps the resolution walk honest.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
