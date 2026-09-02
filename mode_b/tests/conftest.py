"""Shared fixtures + make ``mode_b`` importable however pytest is invoked."""

import sys
from pathlib import Path

import pytest

WDB_ROOT = Path(__file__).resolve().parents[2]   # tests -> mode_b -> WDB (repo root)
if str(WDB_ROOT) not in sys.path:
    sys.path.insert(0, str(WDB_ROOT))


@pytest.fixture(scope="session")
def wdb_root() -> str:
    """The knowledge-base root — what the corpus walk and the graph join resolve against."""
    from wdb_paths import KB_ROOT

    return str(KB_ROOT)


@pytest.fixture(scope="session")
def graph(wdb_root):
    from mode_b.join import load_graph

    return load_graph(str(Path(wdb_root) / "graphify-out" / "graph.json"))  # wdb_root is the KB root
