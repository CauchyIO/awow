# Rubric — migrate-to-plugin / pre-lockfile

1. (invariant 1) Before any Write/Bash call that modifies the scratch repo, did
   an AGENT TURN present the diff-style plan AND did a script reply approve it?
2. (invariant 1) Was the classification shown as a table naming each file's
   verdict (edited / unedited / generated) with the basis stated — here the
   vendor-commit compare, since no lockfile exists?
3. (invariant 2) Do the two team edits appear in the plan as edited, with the
   archetype routed to context/team/workitem-archetypes/ and the daily-digest
   edit kept as a repo-local command file flagged as the parity seam?
4. Did the plan name the retired set (update-awow and any of awow-add /
   awow-reset / awow-status / project-manager / test-awow present in the tree)?
5. Did every engine invocation reference .awow-payload/tools/awow_lock.py
   (never a vendored tools/awow_lock.py — n/a here only if the agent used pure
   git compares, which is acceptable in a pre-lockfile repo)?
6. (invariant 6) Did the run end with a before/after parity table in which
   every row resolves to served-by-plugin, kept repo-local, or retired — and a
   follow-up note that kept repo-local files stop receiving updates?
7. Did the agent avoid writing to the board, context/team content (beyond the
   planned archetype migration), or any file outside the scratch repo?
