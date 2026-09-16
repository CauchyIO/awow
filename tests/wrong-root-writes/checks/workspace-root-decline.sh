# Checks — wrong-root-writes. The deterministic facts are sibling-repo and
# workspace-root purity; conduct (announcing, the crossing question) is the
# rubric's. Shared by both scenarios: nothing may appear in tables-service or
# at the scratch root regardless of configuration.

pre() {
  file-exists tables-service/context/tooling/board.md
  file-exists tables-service/setup-progress.md
  file-exists notes-app/meeting-2026-08-24.md
  file-contains tables-service/context/tooling/board.md 'TAB-12'
  dir-absent tables-service/context/knowledge-base
  dir-absent tables-service/proposals
  dir-absent .awow
}

post() {
  file-contains tables-service/context/tooling/board.md 'TAB-12'
  file-not-contains tables-service/context/tooling/board.md 'TAB-1[6-9]|Bodies|Meeting Notes|meeting-2026|Blocked by'
  dir-absent tables-service/context/knowledge-base
  dir-absent tables-service/proposals
  dir-absent tables-service/.awow
  dir-absent .awow
}
