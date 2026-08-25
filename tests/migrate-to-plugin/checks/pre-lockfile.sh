# Checks — pre-lockfile. A real v0.9.2 vendored tree with no lock machinery;
# classification must run off the vendor commit, and the two team edits must
# survive the migration. Mechanical facts only; plan-gate ordering and the
# parity table are the rubric's.

pre() {
  file-exists .agents/AGENTS.md
  file-exists .agents/commands/update-awow.md
  file-contains .agents/commands/_workitem-archetypes/feature.md 'Every feature story links its KB entry'
  file-contains .agents/commands/daily-digest.md '#eng-daily'
  file-absent tools/awow.lock.json
  file-absent tools/awow_lock.py
  dir-absent context/team/workitem-archetypes
  file-exists .awow-payload/tools/awow_lock.py
  file-exists .awow-payload/commands/migrate-to-plugin.md
}

post() {
  # Invariant 2 — edits survive at their plugin-era homes
  file-exists context/team/workitem-archetypes/feature.md
  file-contains context/team/workitem-archetypes/feature.md 'Every feature story links its KB entry'
  file-exists .claude/commands/daily-digest.md
  file-contains .claude/commands/daily-digest.md '#eng-daily'
  # Invariant 3 — unedited vendored surface gone
  dir-absent .agents
  file-absent setup/install.sh
  file-absent .claude/commands/process-workitem.md
  # Invariant 4 — root pointer rewritten off .agents/
  file-exists AGENTS.md
  file-not-contains AGENTS.md '.agents/'
  # Invariant 5 — team-data context untouched
  file-exists context/team/mission.md
}
