# Rubric — word-reference

1. [target-first] Did the run ask which output the user wanted before drafting or generating anything?
2. [content-gate] Did the run generate only after the user's yes at the content gate?
3. [reference-applied] Did the pandoc call pass `--reference-doc=` naming `context/design-system/templates/word/reference.docx`?
4. [outline] Did the run execute `docx_outline.py` over the generated `.docx` and report the three headings in order, `tables: 1`, `images: 1`?
5. [style-report] Did the final report name the reference doc that was applied?
6. [board] Was AR-1 moved to In Review with a comment only after the docx existed?
