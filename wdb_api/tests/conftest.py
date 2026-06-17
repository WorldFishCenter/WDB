"""Shared fixtures for the read-API suite — deterministic, offline, model-free.

The whole suite runs on **Replay** backends (no model, no network), the same posture the
router's and the modes' own suites take. Backends are injected into the app via
``create_app(backends_factory=…)`` so the suite never depends on whether the developer's shell
happens to export ``ANTHROPIC_API_KEY`` — it always forces Replay.

``make_client`` is a factory fixture: tests that need an isolated case (an off-topic refusal,
a fabricated edge, a single recorded resolution) build a client over their own Replay backends;
``client`` is the convenience default over the merged proof ∪ blended fixtures. Both enter the
``TestClient`` as a context manager, so the lifespan runs and the backends build **once** on
startup — exercising the real startup-load path (model-free under Replay).
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

WDB_ROOT = Path(__file__).resolve().parents[2]   # tests -> wdb_api -> WDB
if str(WDB_ROOT) not in sys.path:
    sys.path.insert(0, str(WDB_ROOT))

from wdb_api.app import create_app                  # noqa: E402
from wdb_router.backends import replay_backends     # noqa: E402


@pytest.fixture
def make_client():
    """Factory → a ``TestClient`` whose app loads the GIVEN backends once on startup.

    Tracks every client it opens and closes them at teardown, so each test's lifespan
    (startup + shutdown) runs deterministically.
    """
    opened: list[TestClient] = []

    def _make(backends) -> TestClient:
        client = TestClient(create_app(backends_factory=lambda: backends))
        client.__enter__()        # run lifespan startup → build the backends once
        opened.append(client)
        return client

    yield _make
    for client in opened:
        client.__exit__(None, None, None)


@pytest.fixture
def client(make_client):
    """Default offline client — Replay backends (mode proofs ∪ the blended/grouped demo)."""
    return make_client(replay_backends())
