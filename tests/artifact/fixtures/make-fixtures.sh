#!/usr/bin/env bash
# Build the three scenario fixtures from _base/. Needs pandoc (for the
# word-reference reference doc). Re-run after editing anything in _base/.
set -euo pipefail
cd "$(dirname "$0")"
for s in word-default word-reference pandoc-absent; do
  rm -rf "$s"; mkdir -p "$s"; cp -R _base/. "$s/"
done
# A 4x4 opaque PNG, written with stdlib so the fixture is deterministic.
python3 - <<'PY'
import struct, zlib
def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
raw = b"".join(b"\x00" + b"\x50\x6f\xa0" * 4 for _ in range(4))
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
for s in ("word-default", "word-reference", "pandoc-absent"):
    open(f"{s}/diagram.png", "wb").write(png)
PY
# word-reference: in-repo pointer + a reference doc whose Heading 1 colour is a sentinel.
# The pointer's `path:` must resolve, or Phase 0 sends the run looking for a
# file that is not there; a minimal style guide is enough to keep it coherent.
mkdir -p word-reference/context/design-system/templates/word
cat > word-reference/context/design-system/style-guide.html <<'HTML'
<!doctype html>
<title>Sample house style</title>
<style>
  :root { --accent: #ff00aa; --ink: #1a1a1a; --surface: #faf9f7; --page: 46rem; }
  body { background: var(--surface); color: var(--ink); font: 16px/1.6 Georgia, serif; max-width: var(--page); margin: 3rem auto; }
  h1, h2 { font-weight: 600; letter-spacing: -0.01em; }
  table { border-collapse: collapse; } td, th { border: 1px solid #ddd; padding: .4rem .6rem; }
</style>
<h1>Sample house style</h1>
<p>Frozen test fixture. One accent (<code>--accent</code>), reserved for the
wordmark; hierarchy by weight, not colour; borders over shadows. The Word
reference doc at <code>templates/word/reference.docx</code> carries the same
accent as its Heading 1 colour.</p>
HTML
pandoc -o word-reference/context/design-system/templates/word/reference.docx --print-default-data-file reference.docx
python3 - <<'PY'
import re, zipfile
p = "word-reference/context/design-system/templates/word/reference.docx"
tmp = p + ".tmp"
with zipfile.ZipFile(p) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/styles.xml":
            s = data.decode("utf-8")
            blk = re.search(r'(<w:style[^>]*w:styleId="Heading1".*?</w:style>)', s, re.S).group(1)
            new = re.sub(r'<w:color w:val="[0-9A-Fa-f]+"', '<w:color w:val="FF00AA"', blk) if "<w:color" in blk else blk.replace("<w:rPr>", '<w:rPr><w:color w:val="FF00AA"/>', 1)
            data = s.replace(blk, new).encode("utf-8")
        zout.writestr(item, data)
import os; os.replace(tmp, p)
PY
python3 - <<'PY'
p = "word-reference/context/tooling/design-system.md"
s = open(p).read()
s = s.replace("mode: absent ", "mode: in-repo", 1)
s = s.replace('path: ""  ', 'path: "context/design-system/style-guide.html"', 1)
s = s.replace('templates_dir: ""  ', 'templates_dir: "context/design-system/templates/"', 1)
s = s.replace('word_reference: ""  ', 'word_reference: "context/design-system/templates/word/reference.docx"', 1)
s = s.replace("_(none — `mode: absent`)_", "_(word_reference registered — see frontmatter)_", 1)
open(p, "w").write(s)
PY
echo "fixtures built"
