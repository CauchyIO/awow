# Rubric — docx-notes

1. [sidecar-first] Before parsing, did the run route `notes/notes.docx` through the office-ingest skill rather than attempting to read the binary?
2. [provenance] Was `notes/notes.docx.md` written with exactly the four header keys (`source`, `source_sha256`, `converted`, `converter`) above markitdown's body?
3. [gate-read] Did GATE 1 attribute statements to Dana and Priya from the sidecar's content?
4. [reuse] On the second request, did the run compute the hash, find it matching, and proceed from the existing sidecar with no second markitdown invocation in the tool-call list?
5. [quiet] Did the run avoid a fidelity warning (the fixture has no checklists, code, or images to lose)?
