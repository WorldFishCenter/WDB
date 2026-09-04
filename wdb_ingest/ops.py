"""One shared helper: the timestamp format the whole workflow records history in.

``advance`` used to live here — the function that actually moved a contribution between states
and appended its history entry. It accepted any ``(from, to)`` pair and had six callers, five of
which never consulted the gate, which is how ``BUILT`` and ``LIVE`` were reachable without a
declared transition. It is now :func:`wdb_ingest.gate.apply`, private to the gate that checks it.
"""

from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
