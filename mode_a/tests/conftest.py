"""Shared fixtures + make ``mode_a`` importable however pytest is invoked.

The deterministic suite runs entirely on the offline ReplayReasoner + real graph
extraction — no model, no network — mirroring the modes' own Live/Replay split. The live
cold-fabrication-rate run is separate (``mode_a/cold_rate.py``).
"""

import sys
from pathlib import Path

import pytest

WDB_ROOT = Path(__file__).resolve().parents[2]   # tests -> mode_a -> WDB
if str(WDB_ROOT) not in sys.path:
    sys.path.insert(0, str(WDB_ROOT))


@pytest.fixture(scope="session")
def graph():
    from mode_a.extract import get_graph

    return get_graph()


@pytest.fixture(scope="session")
def recorded():
    from mode_a.fixtures import RECORDED

    return RECORDED
