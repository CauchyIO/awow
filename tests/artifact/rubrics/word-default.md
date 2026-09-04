# Rubric — word-default

1. [target-first] Did the run ask which output the user wanted (HTML + PDF / Word / both) before drafting or generating anything?
2. [word-constraints] After "Word" was chosen, did the run state the Word constraints (diagrams as PNG or table; one H1 or title line; relative image paths; no slide layouts)?
3. [content-gate] Did the run stop at "content agreed — generate the Word?" and generate only after the user's yes?
4. [from-markdown] Was `out/brief.docx` produced by a pandoc call reading `brief.md` (or a copy of it) with `--from gfm --to docx`, with no HTML generated at any point?
5. [outline] Did the run execute `docx_outline.py` over the generated `.docx` and report its outline — headings `Q3 stakeholder one-pager` (1), `Intent` (2), `Acceptance criteria` (2) in that order, `tables: 1`, `images: 1`?
6. [round-trip] Did the run perform the pandoc round-trip check and report its result?
7. [style-report] Did the final report state that pandoc's stock styles were used (no reference doc)?
8. [board] Was AR-1 moved to In Review with a comment only after the docx existed?
