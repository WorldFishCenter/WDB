"""Workflow persistence — the ``WorkflowStore`` protocol + a SQLite implementation.

The protocol is the **Atlas swap seam** (design §8: ingestion workflow state lives in a database).
SQLite is the working local default; a ``MongoWorkflowStore`` implementing the same protocol would
point the service at Atlas with no other change. Approved *notes* never live here — they go to git on
sign-off (design §5); this store holds workflow state only.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Protocol

from .models import Submission, WorkflowState


class WorkflowStore(Protocol):
    def get(self, sub_id: str) -> Submission | None: ...
    def list_submissions(
        self, *, contributor: str | None = None, states: list[WorkflowState] | None = None
    ) -> list[Submission]: ...
    def upsert(self, submission: Submission) -> None: ...
    def meta_get(self, key: str) -> str | None: ...
    def meta_set(self, key: str, value: str) -> None: ...
    def reset(self) -> None: ...


class SqliteWorkflowStore:
    """File-backed store. Opens a fresh connection per call (threadpool-safe — FastAPI runs the
    sync endpoints across threads). The full Submission is kept as JSON; ``state``/``contributor``
    are mirrored into columns for role-scoped queries and ordering by submission time."""

    def __init__(self, db_path: Path | str) -> None:
        # No disk touch here — importing the app (which constructs the default store) must not create
        # files. The DB is created lazily on first use via _ensure().
        self.db_path = str(db_path)
        self._initialized = False

    def _connect(self) -> sqlite3.Connection:
        self._ensure()
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure(self) -> None:
        if self._initialized:
            return
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialized = True
        self._init()

    def _init(self) -> None:
        with self._connect() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS submissions (
                       id TEXT PRIMARY KEY,
                       contributor TEXT NOT NULL,
                       state TEXT NOT NULL,
                       created_at TEXT NOT NULL,
                       data TEXT NOT NULL
                   )"""
            )
            c.execute("""CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)""")

    def get(self, sub_id: str) -> Submission | None:
        with self._connect() as c:
            row = c.execute("SELECT data FROM submissions WHERE id = ?", (sub_id,)).fetchone()
        return Submission.model_validate_json(row["data"]) if row else None

    def list_submissions(
        self, *, contributor: str | None = None, states: list[WorkflowState] | None = None
    ) -> list[Submission]:
        sql = "SELECT data FROM submissions"
        clauses: list[str] = []
        params: list[str] = []
        if contributor is not None:
            clauses.append("contributor = ?")
            params.append(contributor)
        if states:
            clauses.append(f"state IN ({','.join('?' for _ in states)})")
            params.extend(s.value for s in states)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC"
        with self._connect() as c:
            rows = c.execute(sql, params).fetchall()
        return [Submission.model_validate_json(r["data"]) for r in rows]

    def upsert(self, submission: Submission) -> None:
        # created_at = the SUBMITTED timestamp (first history entry) so ordering is stable.
        created_at = submission.history[0].at if submission.history else submission.provenance.captured_at
        data = submission.model_dump_json(by_alias=True)
        with self._connect() as c:
            c.execute(
                """INSERT INTO submissions (id, contributor, state, created_at, data)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET state=excluded.state, data=excluded.data""",
                (submission.id, submission.provenance.contributor, submission.state.value, created_at, data),
            )

    def meta_get(self, key: str) -> str | None:
        with self._connect() as c:
            row = c.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def meta_set(self, key: str, value: str) -> None:
        with self._connect() as c:
            c.execute(
                "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def reset(self) -> None:
        with self._connect() as c:
            c.execute("DELETE FROM submissions")
            c.execute("DELETE FROM meta")
