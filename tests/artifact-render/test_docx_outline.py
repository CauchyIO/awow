#!/usr/bin/env python3
"""Black-box test for the artifact-render skill's docx_outline.py.

Stdlib only, no pytest. Runs the script as a subprocess over frozen fixtures
(regenerate with fixtures/make-fixtures.sh — needs pandoc; CI does not).
    python3 tests/artifact-render/test_docx_outline.py
Exits 0 if all pass, 1 otherwise.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(ROOT, ".agents", "skills", "artifact-render", "scripts", "docx_outline.py")
FIX = os.path.join(os.path.dirname(__file__), "fixtures")

EXPECTED_HEADINGS = [
    {"level": 1, "text": "Probe brief"},
    {"level": 2, "text": "Intent"},
    {"level": 2, "text": "Acceptance criteria"},
]
# titled.docx carries a title: metadata line as well as the H1, so pandoc emits
# a Title paragraph in front of the same three headings. Title is level 0.
EXPECTED_TITLED = [{"level": 0, "text": "Probe brief"}] + EXPECTED_HEADINGS

failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)


def run(path):
    return subprocess.run([sys.executable, SCRIPT, path], capture_output=True, text=True)


r = run(os.path.join(FIX, "sample.docx"))
check("sample: exit 0", r.returncode == 0)
out = json.loads(r.stdout) if r.returncode == 0 else {}
check("sample: headings in order", out.get("headings") == EXPECTED_HEADINGS)
check("sample: one table", out.get("tables") == 1)
check("sample: no images", out.get("images") == 0)

r = run(os.path.join(FIX, "renamed.docx"))
out = json.loads(r.stdout) if r.returncode == 0 else {}
check("renamed styleId still resolves by name", out.get("headings") == EXPECTED_HEADINGS)

r = run(os.path.join(FIX, "titled.docx"))
out = json.loads(r.stdout) if r.returncode == 0 else {}
check("titled: Title style is level 0", out.get("headings") == EXPECTED_TITLED)

r = run(os.path.join(FIX, "sample.md"))
check("non-zip: exit 2", r.returncode == 2)
check("non-zip: one stderr line", r.stderr.count("\n") == 1)

r = run(os.path.join(FIX, "does-not-exist.docx"))
check("missing: exit 2", r.returncode == 2)

sys.exit(1 if failures else 0)
