"""Fixtures for the ingestion suite — hermetic: every test runs against a temp WDB_ROOT + temp
SQLite store, so file/note writes and the build handoff never touch the real repo."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

WDB_ROOT = Path(__file__).resolve().parents[2]  # tests -> wdb_ingest -> WDB
if str(WDB_ROOT) not in sys.path:
    sys.path.insert(0, str(WDB_ROOT))

from wdb_ingest import config, service  # noqa: E402
from wdb_ingest.app import create_app  # noqa: E402
from wdb_ingest.models import Role, SubmissionInput  # noqa: E402
from wdb_ingest.store import SqliteWorkflowStore  # noqa: E402


@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "WDB_ROOT", tmp_path)
    monkeypatch.setattr(config, "STATE_DIR", tmp_path / "_state")
    monkeypatch.setattr(config, "STAGING_DIR", tmp_path / "_staging")
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "_state" / "workflow.db")
    out = tmp_path / "graphify-out"
    out.mkdir()
    monkeypatch.setattr(config, "GRAPHIFY_OUT", out)
    monkeypatch.setattr(config, "GRAPH_JSON", out / "graph.json")
    monkeypatch.setattr(config, "BUILD_INFO", out / "BUILD_INFO.md")
    return tmp_path


@pytest.fixture
def store(tmp_env):
    return SqliteWorkflowStore(config.DB_PATH)


@pytest.fixture
def client(store):
    c = TestClient(create_app(lambda: store))
    c.__enter__()
    yield c
    c.__exit__(None, None, None)


@pytest.fixture
def to_pending(store):
    """Drive a fresh doc submission to PENDING (deterministic — doc format, no subprocess)."""

    def _go(initiative: str = "ssf_research", filename: str = "ssf_notes.md"):
        inp = SubmissionInput(filename=filename, format="doc", sizeLabel="2 KB", initiative=initiative)
        sub = service.submit(store, inp, b"# notes\n", contributor="amina", background=False)
        sub = service.act(store, sub.id, "open_for_review", Role.CONTRIBUTOR)
        return service.act(store, sub.id, "approve", Role.CONTRIBUTOR)

    return _go
