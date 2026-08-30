#!/usr/bin/env python3
"""Build-stamp determinism over the payload plans (CAU-1338 AC3).

The stamp at <payload root>/.claude-plugin/build.json distinguishes rebuilds:
same source tree -> same stamp; any planned content change -> a new digest.
It must be a pure function of the plan (no clock, no commit), or
`gather.py --check` would flap on every CI run.

Pure stdlib; no pytest, no network. Exercises the plan, never the disk.

Run:  python3 tests/payload-manifests/test_build_stamp.py
"""
import importlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

gather = importlib.import_module("gather")

FAILURES = []


def check(label, cond):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        FAILURES.append(label)


def stamp_of(plans, root):
    target = root / ".claude-plugin" / "build.json"
    found = [p for p in plans if p.target == target]
    check(f"{root.name}: plan carries exactly one build stamp", len(found) == 1)
    return json.loads(found[0].content) if found else {}


def main() -> int:
    version = json.loads(gather.PLUGIN_MANIFEST.read_text())["version"]
    plans = gather.dist_surface_plans()
    stamp = stamp_of(plans, gather.DIST_DIR)
    others = [p for p in plans
              if p.target != gather.DIST_DIR / ".claude-plugin" / "build.json"]

    check("stamp carries the canonical version", stamp.get("version") == version)
    check("digest is sha256:<12 hex>",
          re.fullmatch(r"sha256:[0-9a-f]{12}", stamp.get("content", "")) is not None)
    check("a second plan build produces an identical stamp",
          stamp == stamp_of(gather.dist_surface_plans(), gather.DIST_DIR))
    check("digest recomputes from the non-stamp stubs alone",
          json.loads(gather.payload_stamp(gather.DIST_DIR, others, version))["content"]
          == stamp.get("content"))
    check("stub order does not affect the digest",
          json.loads(gather.payload_stamp(
              gather.DIST_DIR, list(reversed(others)), version))["content"]
          == stamp.get("content"))
    mutated = [gather.Stub(others[0].target, others[0].content + "x",
                           others[0].mode)] + others[1:]
    check("a planned content change flips the digest",
          json.loads(gather.payload_stamp(gather.DIST_DIR, mutated, version))["content"]
          != stamp.get("content"))
    check("m365 never enters the dist digest input",
          all(gather.M365_ROOT not in p.target.parents for p in others))

    tstamp = stamp_of(gather.telemetry_surface_plans(), gather.DIST_TELEMETRY_DIR)
    check("telemetry stamp carries the canonical version",
          tstamp.get("version") == version)
    check("the two payloads carry different digests",
          tstamp.get("content") != stamp.get("content"))

    if FAILURES:
        print(f"\n{len(FAILURES)} failing")
        return 1
    print("\nall passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
