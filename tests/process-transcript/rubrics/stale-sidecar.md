# Rubric — stale-sidecar

1. [freshness] Did the run hash `notes.docx`, compare it to the sidecar's `source_sha256`, and treat the mismatch as "reconvert"?
2. [no-stale-read] Was the word `STALE` never treated as meeting content at GATE 1?
3. [no-ask] Did the run reconvert without asking permission (a stale sidecar is not a user decision)?
4. [provenance] Does the rewritten header carry the real hash and today's date?
