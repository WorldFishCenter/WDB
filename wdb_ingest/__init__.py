"""WDB ingestion service — the write-side backend (workflow state machine + two-stage gate +
single-builder build handoff). Local, production-shaped; see wdb_ingest/app.py."""

from .app import create_app

__all__ = ["create_app"]
