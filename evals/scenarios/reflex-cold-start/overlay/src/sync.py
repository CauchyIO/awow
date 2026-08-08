"""Manifest push worker: sends carrier manifests, retrying on timeout."""
from __future__ import annotations

import time

TIMEOUT_S = 10
MAX_ATTEMPTS = 3


def send(manifest: dict, transport) -> str:
    """One send attempt; returns the carrier receipt id or raises TimeoutError."""
    return transport.post("/manifests", manifest, timeout=TIMEOUT_S)


def was_received(manifest: dict, transport) -> bool:
    """Ask the carrier whether this manifest already landed."""
    return transport.get(f"/manifests/{manifest['id']}/status") == "received"


def push_manifest(manifest: dict, transport) -> str:
    """Push with retries on timeout."""
    last_error = None
    for _attempt in range(MAX_ATTEMPTS):
        try:
            return send(manifest, transport)
        except TimeoutError as error:
            last_error = error
            time.sleep(1)
    raise last_error
