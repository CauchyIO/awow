---
name: office-ingest
description: "Use when you are handed or encounter a .docx, .pptx, .xlsx or .xls — a quarterly deck, a stakeholder brief, Word meeting notes — before any command reads it; converts it once into a provenance-stamped markdown sidecar and reuses that sidecar until the source changes."
---

# office-ingest — read Office files through a markdown sidecar

You read Office files through their markdown sidecar, never directly. The sidecar is `<file>.<ext>.md` beside the source, written by markitdown, headed by four provenance keys. PDF is not yours: the harness reads it natively.

## 1. Check for a current sidecar

Hash the source with `python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <source>` (`python` where `python3` is absent). If `<file>.<ext>.md` exists and its `source_sha256` equals the hash, read it and stop here. A file at that path with no `source_sha256` header is not a sidecar — ask before overwriting it. Otherwise convert.

## 2. Convert

Use the first rung that applies, and no other:

1. `uv` on PATH: `uvx --from "markitdown[docx,pptx,xlsx,xls]" markitdown <source> -o <sidecar>`
2. `markitdown` on PATH: `markitdown <source> -o <sidecar>`
3. Neither: offer once — `uv tool install "markitdown[docx,pptx,xlsx,xls]"` (or `pipx install …`, or `python3 -m pip install --user …`) — and run it only on an explicit yes. On no or on failure, ask for a PDF export or pasted text and proceed on that. Do not claim the file was read.

`markitdown -o` writes the body only. Convert first, then rewrite the sidecar with this header on top of the body it just wrote — exactly these four keys:

    ---
    source: <source filename, relative to the sidecar's directory>
    source_sha256: <hash from step 1>
    converted: <today, ISO date>
    converter: markitdown <version from --version>
    ---

Leave the body as markitdown wrote it. Never edit a sidecar by hand; fix the source or note the correction in your own working notes.

## 3. Match the source's tracking

Run `git check-ignore -q <source>` and branch on its exit code. 128 — no git repo: do nothing here. 0 — the source is ignored: if the sidecar is not also ignored, propose one line in the repo-root `.gitignore` and write it on confirmation. 1 — the source is tracked, or untracked and not ignored: leave the sidecar for the same commit. Never stage or commit.

A sidecar carries its source's sensitivity: a converted copy of anything the user called sensitive never lands in a tracked path. When such a source is itself tracked, write the sidecar to the session scratch directory instead, read it from there, and say so; that source is reconverted every session, by design.

## 4. Say what may have been lost, when it matters

Checkboxes flatten to bullets and lose their checked state, fenced code becomes plain text, images are referenced not extracted, tracked changes and comments are not guaranteed. State the fact that bears on the task in one line; otherwise say nothing. A body that is whitespace only, or implausibly short for the source's size, means the file is likely image-only, encrypted or empty — ask for a different export instead of proceeding on nothing.

## Boundaries

- Convert `.docx`, `.pptx`, `.xlsx`, `.xls` only. Hand PDF to the harness's native reader.
- One conversion per source version. A matching hash means no markitdown call.
- The sidecar's name keeps the source extension: `deck.pptx.md`, never `deck.md`.
- No MCP server, no LLM captioning, no cloud extraction. Local CLI only.
