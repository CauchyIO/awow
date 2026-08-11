#!/usr/bin/env python3
"""Report when the published payload has fallen behind this checkout.

`awow-dist` is the install source for Codex, Pi and opencode. Publishing it is a
manual `tools/sync-dist.sh` run, and between v0.6.0 and v0.8.0 nobody ran it:
every install on those three harnesses resolved two minor versions behind while
CI stayed green, because `gather.py --check` only compares dist/ against the
generator and knows nothing about the remote (AWO-156).

Compares the local built payload version against the published one and exits
non-zero when they differ.

No fallbacks. A network or parse failure raises rather than passing quietly:
a staleness check that goes green when it could not reach the remote is worse
than no check, because it reads as proof.

Usage:
  tools/check-dist-published.py            # fail if published != local
  tools/check-dist-published.py --warn     # report only, always exit 0
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_MANIFEST = REPO_ROOT / "dist" / "package.json"
PUBLISHED_URL = "https://raw.githubusercontent.com/CauchyIO/awow-dist/main/package.json"
TIMEOUT_SECONDS = 20


def published_version(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "awow-release-check"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode())
    version = payload.get("version")
    if not version:
        raise RuntimeError(f"{url} carries no version field")
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn", action="store_true",
        help="report the mismatch but exit 0 (for a non-blocking CI signal)",
    )
    parser.add_argument("--url", default=PUBLISHED_URL)
    args = parser.parse_args()

    local = json.loads(LOCAL_MANIFEST.read_text())["version"]
    remote = published_version(args.url)

    if local == remote:
        print(f"ok — awow-dist published {remote}, matching this checkout")
        return 0

    print(
        f"awow-dist is at {remote}; this checkout builds {local}.\n"
        "Codex, Pi and opencode installs resolve the published version, so they "
        f"are serving {remote}. Publish with: tools/sync-dist.sh --apply",
        file=sys.stderr,
    )
    return 0 if args.warn else 1


if __name__ == "__main__":
    raise SystemExit(main())
