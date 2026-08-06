# `.agents/commands/_meeting-archetypes/`

Generic meeting-analysis lenses loaded by `/process-transcript`. They are
awow-owned handlers, not commands: several may apply to one transcript segment,
and none appears in a command picker.

Teams do not copy or edit these defaults. Put only meaningful local differences
under `context/team/meetings/`; `/process-transcript` composes those notes with
the matching handlers here. A team may also describe a recurring meeting with
no generic counterpart there.

Each handler answers four questions: when the lens applies, what to extract,
which missing topics are worth noting, and which interpretation mistakes to
avoid. Pipeline gates, attribution, evidence, specialist dispatch, and board
writes remain owned by `/process-transcript`.
