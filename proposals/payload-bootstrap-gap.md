# Payload bootstrap gap — /setup-awow Step 5 cannot run as written on the plugin channel

**Status:** STUB — follow-up surfaced by CAU-1335; needs a board item.

## Finding

`/setup-awow` Step 5 says "Run `tools/bootstrap-claude-md.py` (or the inline
equivalent). It reads the stub at `.agents/AGENTS.md`…" — but the plugin
payload ships neither that script (`dist/tools/` holds only `awow_lock.py` and
`hooks/`) nor any `AGENTS.md` stub. A plugin adopter completing setup gets an
improvised, unspecified CLAUDE.md, and before CAU-1335 could never receive the
context-resolution rules at all.

## Direction (to be refined)

Either ship `bootstrap-claude-md.py` plus a channel-appropriate stub in the
payload, or rewrite Step 5 for the plugin channel to author the team file from
the wizard's outputs alone — and say which channel each instruction serves.
CAU-1335 removed the sharpest consequence (the resolution contract now ships
as machinery independent of setup), but Step 5 as written still names files a
plugin adopter does not have.
