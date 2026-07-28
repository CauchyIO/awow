#!/usr/bin/env bash
# Re-date the frozen snapshot to the run day so /daily-digest's "today" finds it.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
TODAY=$(date +%F)
mv "$SCRATCH/activity/2026-07-01.json" "$SCRATCH/activity/$TODAY.json"
sed -i.bak "s/2026-07-01/$TODAY/g" "$SCRATCH/activity/$TODAY.json"
rm -f "$SCRATCH/activity/$TODAY.json.bak"
