"""Small shared helpers used by both the service and the build orchestrator."""

from __future__ import annotations

from datetime import datetime, timezone

from .models import HistoryEntry, Submission, WorkflowState


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def advance(sub: Submission, to: WorkflowState, actor: str, note: str | None = None) -> Submission:
    """Return a copy of ``sub`` moved to ``to`` with an appended (append-only) history entry."""
    return sub.model_copy(
        update={
            "state": to,
            "history": [*sub.history, HistoryEntry(state=to, at=now_iso(), actor=actor, note=note)],
        }
    )
