#!/usr/bin/env bash
# Regenerate the frozen .docx fixtures for tests/artifact-render. Needs pandoc.
# renamed.docx is sample.docx with Heading1's styleId renamed to "berschrift1"
# in both styles.xml and document.xml — the w:name stays "heading 1", which is
# exactly the case docx_outline.py must still classify as level 1.
# titled.docx is sample.md rendered with a title metadata as well as its H1 —
# pandoc then emits a Title paragraph *and* a Heading 1, the duplicate the
# /artifact "one H1 or a title: line, never both" rule prevents. It is the
# fixture that pins Title to level 0.
# imaged.docx is sample.md plus one referenced PNG, so the image count is
# exercised against a non-zero value rather than only against 0.
set -euo pipefail
cd "$(dirname "$0")"
pandoc sample.md --from gfm --to docx -o sample.docx
pandoc sample.md --from gfm --to docx --metadata title="Probe brief" -o titled.docx
# A 4x4 opaque PNG, written with stdlib so the fixture is deterministic (the
# same generator tests/artifact/fixtures/make-fixtures.sh uses).
python3 - <<'PY'
import struct, zlib
def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
raw = b"".join(b"\x00" + b"\x50\x6f\xa0" * 4 for _ in range(4))
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
open("probe.png", "wb").write(png)
open("imaged.md", "w").write(open("sample.md").read() + "\n![Probe diagram](probe.png)\n")
PY
pandoc imaged.md --from gfm --to docx --resource-path=. -o imaged.docx
rm -f imaged.md probe.png
python3 - <<'PY'
import zipfile
with zipfile.ZipFile("sample.docx") as zin, zipfile.ZipFile("renamed.docx", "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename in ("word/styles.xml", "word/document.xml"):
            data = data.replace(b'w:styleId="Heading1"', b'w:styleId="berschrift1"').replace(b'w:val="Heading1"', b'w:val="berschrift1"')
        zout.writestr(item, data)
PY
echo "fixtures regenerated: sample.docx renamed.docx titled.docx imaged.docx"
