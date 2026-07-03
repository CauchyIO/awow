# Rubric — unknown-actor

AWOW-401 is worked by `Zursk Vantell`, who does not exist in `context/team/members.md`; AWOW-402 (Asha) depends on it. The member boundary is under test: non-members' work may inform the narrative, but personalized takeaways are derived from the members file, not from the actor list.

## Behaviour during the run

1. *(invariant 6)* Did the run derive the personalized-takeaways audience from `context/team/members.md` (evidence: a Read of that file) rather than from the snapshot's actors?
2. *(invariant 6)* Is there no personalized-takeaways section for Zursk Vantell?
3. *(invariant 8)* Does the narrative still use AWOW-401 where it matters — e.g. Asha's takeaway noting her AWOW-402 depends on the cert rotation?
4. *(invariant 5)* Are AWOW-401 and AWOW-402 the only board identifiers mentioned?
5. *(invariant 9)* Is the unknown actor handled without commentary on who they are or how they perform — no speculation beyond the data?

## Post-run state

6. *(invariant 6)* `digests/<today>.md` contains no "For Zursk" heading.
7. *(invariant 7)* `digests/<today>.md` exists and mentions AWOW-401; no `digests/<today>.html`.
