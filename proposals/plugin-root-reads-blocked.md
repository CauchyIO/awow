# Plugin-root reads can be permission-blocked — shipped machinery silently degrades

**Status:** STUB — follow-up surfaced by CAU-1335; needs a board item.

## Finding

In both CAU-1335 reproduction runs (headless `claude -p --plugin-dir dist`),
the session reported the payload's lens registry
(`dist/handlers/_meeting-archetypes/`) as *outside this session's allowed
directories* and fell back to "minimal ad-hoc extraction". The plugin root is
not automatically a readable directory in every harness configuration, so
`{AWOW_ROOT}`-resolved machinery — handlers, contracts, board references — can
be unreachable exactly when it matters, and the commands degrade silently.

## Direction (to be refined)

Decide the guarantee: either commands must treat an unreadable `{AWOW_ROOT}`
as a loud, named degradation (one line at the next gate, minimum), or the
plugin needs a mechanism that makes the payload readable (e.g. additional
working directories in plugin config, or hook-injected content). Audit which
commands read `{AWOW_ROOT}` mid-flow and what each does when the read fails.
