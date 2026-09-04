#!/usr/bin/env python3
"""Print the structural outline of a .docx as JSON: headings (by resolved
style *name*, so renamed or localised style IDs still count), table count,
image count. Stdlib only. Used by the artifact-render skill to verify a
pandoc-generated Word document against its markdown source.

Usage: python3 docx_outline.py <file.docx>
Exit 0 with JSON on stdout; exit 2 with one line on stderr when the file is
missing, not a zip, unparsable, or has no word/document.xml.
"""
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
HEADING_NAME = re.compile(r"^(?:heading\s*(\d))$", re.IGNORECASE)
TITLE_NAME = re.compile(r"^title$", re.IGNORECASE)


def style_names(zf):
    """styleId -> canonical w:name from word/styles.xml (empty if absent)."""
    try:
        root = ET.fromstring(zf.read("word/styles.xml"))
    except KeyError:
        return {}
    names = {}
    for style in root.iter(f"{{{W}}}style"):
        sid = style.get(f"{{{W}}}styleId")
        name_el = style.find(f"{{{W}}}name")
        if sid and name_el is not None:
            names[sid] = name_el.get(f"{{{W}}}val", "")
    return names


def heading_level(style_id, names):
    name = names.get(style_id, style_id or "")
    if TITLE_NAME.match(name):
        return 0
    m = HEADING_NAME.match(name)
    return int(m.group(1)) if m else None


def outline(path):
    with zipfile.ZipFile(path) as zf:
        names = style_names(zf)
        root = ET.fromstring(zf.read("word/document.xml"))
    headings = []
    for p in root.iter(f"{{{W}}}p"):
        pstyle = p.find(f"{{{W}}}pPr/{{{W}}}pStyle")
        if pstyle is None:
            continue
        level = heading_level(pstyle.get(f"{{{W}}}val"), names)
        if level is None:
            continue
        text = "".join(t.text or "" for t in p.iter(f"{{{W}}}t"))
        headings.append({"level": level, "text": text})
    return {
        "headings": headings,
        "tables": sum(1 for _ in root.iter(f"{{{W}}}tbl")),
        "images": sum(1 for _ in root.iter(f"{{{A}}}blip")),
    }


def main(argv):
    if len(argv) != 2:
        print("usage: docx_outline.py <file.docx>", file=sys.stderr)
        return 2
    try:
        result = outline(argv[1])
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        print(f"docx_outline: cannot read {argv[1]}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
