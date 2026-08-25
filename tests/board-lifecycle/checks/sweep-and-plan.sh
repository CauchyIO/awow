# Checks — sweep-and-plan. A declined gate must leave the fixture byte-level
# intact: same board.md contract, same snapshot, no plan/ledger artifacts.
# Which project got which verdict is transcript evidence — the rubric's job.

pre() {
  file-exists context/tooling/board.md
  file-contains context/tooling/board.md 'shape:engagement'
  file-contains context/tooling/board.md 'Needs decision'
  file-exists board-snapshots/2026-08-20-projects.json
  file-contains board-snapshots/2026-08-20-projects.json 'harbor-rollout'
  file-contains board-snapshots/2026-08-20-projects.json 'north-star-portal'
  dir-absent proposals
}

post() {
  # invariant 1 — nothing written on a declined gate
  file-exists context/tooling/board.md
  file-contains context/tooling/board.md 'Tripwire: 2 unresolved cycles'
  file-exists board-snapshots/2026-08-20-projects.json
  file-contains board-snapshots/2026-08-20-projects.json '"snapshot_date": "2026-08-20"'
  dir-absent proposals
}
