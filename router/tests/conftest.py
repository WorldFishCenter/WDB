"""Shared fixtures + make ``router`` (and the modes it reuses) importable.

The deterministic suite runs entirely on Replay backends — no model, no network —
mirroring the modes' own Live/Replay split. The one ``@pytest.mark.live`` test
(the real-reranker off-topic arm) self-skips when Chroma / the cross-encoder are
unavailable, so CI without them still passes on the deterministic version.
"""

import sys
from pathlib import Path

import pytest

WDB_ROOT = Path(__file__).resolve().parents[2]   # tests -> router -> WDB
if str(WDB_ROOT) not in sys.path:
    sys.path.insert(0, str(WDB_ROOT))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live: needs real models/network (Chroma + cross-encoder reranker); "
        "self-skips when unavailable",
    )


@pytest.fixture(scope="session")
def backends():
    """Deterministic replay backends (harness fixtures: mode proofs ∪ blended demo)."""
    from router.router import replay_backends

    return replay_backends()
