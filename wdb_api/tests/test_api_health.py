"""Health endpoint + request validation — the small surface around the router pass-through."""

from fastapi.testclient import TestClient

from wdb_api.app import create_app
from wdb_router.backends import replay_backends


def test_backends_build_once_on_startup_not_per_request():
    # the persistent-service contract: the heavy backends (Mode B's models, under Live) build
    # ONCE in the lifespan, never per request. We count factory calls across several requests.
    calls = {"n": 0}

    def counting_factory():
        calls["n"] += 1
        return replay_backends()

    with TestClient(create_app(backends_factory=counting_factory)) as client:
        for _ in range(3):
            client.post("/answer", json={"question": "What projects operate in Kenya?"})
        client.get("/health")
    assert calls["n"] == 1                         # built once on startup, reused every request


def test_health_reports_offline_replay_backend(client):
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["backend"] == "replay"             # no API key in the suite → offline Replay
    assert data["reranker_loaded"] is False        # Replay loads no cross-encoder


def test_answer_requires_a_nonempty_question(client):
    assert client.post("/answer", json={}).status_code == 422            # missing field
    assert client.post("/answer", json={"question": ""}).status_code == 422  # empty string
