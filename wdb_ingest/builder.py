"""The single-builder build orchestrator — TRACKED HANDOFF to the pinned ``/graphify`` build.

Finding (see graphify-out/BUILD_INFO.md + CLAUDE.md): the two extraction guards and the
canonical-entity remap are **injected by the maintainer's pinned ``claude-opus-4-8`` session**, not by
the ``graphify`` CLI — so there is no *faithful* headless build. This orchestrator therefore does NOT
run a headless build and call it faithful. Instead it:

  1. ``start_build`` — snapshots ``graphify-out/graph.json`` as a baseline, records which QUEUED
     contributions are handed off, and surfaces the **exact pinned command** for the maintainer to run
     (``/graphify . --update`` in a pinned session — the only place the guards + remap apply).
  2. ``poll`` / ``confirm`` — when the real build has run (graph.json changed vs. baseline, or the
     operator confirms), advances the handed-off contributions QUEUED → BUILT → LIVE.

A module lock enforces the single-builder rule (one handoff outstanding at a time). Nothing is
auto-committed — the maintainer reviews the git diff and opens a PR (single-builder + PR review).
"""

from __future__ import annotations

import json
import threading

from . import config
from .models import WorkflowState
from .ops import advance, now_iso
from .store import WorkflowStore

_BUILD_KEY = "build"
_lock = threading.Lock()


def _snapshot() -> dict | None:
    """Counts + mtime of the current built graph, or None if it doesn't exist yet."""
    if not config.GRAPH_JSON.exists():
        return None
    try:
        data = json.loads(config.GRAPH_JSON.read_text())
        return {
            "nodes": len(data.get("nodes", [])),
            "edges": len(data.get("edges", [])),
            "mtime": config.GRAPH_JSON.stat().st_mtime,
        }
    except (json.JSONDecodeError, OSError):
        return None


def _read(store: WorkflowStore) -> dict:
    raw = store.meta_get(_BUILD_KEY)
    return json.loads(raw) if raw else {"status": "IDLE"}


def _write(store: WorkflowStore, state: dict) -> None:
    store.meta_set(_BUILD_KEY, json.dumps(state))


def _baseline_changed(baseline: dict | None, current: dict | None) -> bool:
    """Did a real build run since handoff? True if the graph was rewritten (mtime advanced) or its
    node/edge counts changed."""
    if current is None:
        return False
    if baseline is None:
        return True
    return (
        current["mtime"] > baseline["mtime"]
        or current["nodes"] != baseline["nodes"]
        or current["edges"] != baseline["edges"]
    )


def _finish(store: WorkflowStore, state: dict) -> dict:
    """Advance every handed-off contribution QUEUED → BUILT → LIVE and mark the build done."""
    current = _snapshot()
    for sub_id in state.get("handed_off_ids", []):
        sub = store.get(sub_id)
        if sub and sub.state == WorkflowState.QUEUED:
            sub = advance(sub, WorkflowState.BUILT, "Single-builder build")
            sub = advance(sub, WorkflowState.LIVE, "Single-builder build")
            store.upsert(sub)
    state.update(
        status="DONE",
        completed_at=now_iso(),
        result=current,
        message=f"Build complete — {len(state.get('handed_off_ids', []))} contribution(s) are now live.",
    )
    _write(store, state)
    return state


def start_build(store: WorkflowStore) -> dict:
    """Hand the queue off to the pinned build. Idempotent while a handoff is outstanding."""
    with _lock:
        state = _read(store)
        if state.get("status") == "AWAITING_BUILD":
            return state  # one build at a time — single-builder
        queued = store.list_submissions(states=[WorkflowState.QUEUED])
        if not queued:
            idle = {"status": "IDLE", "message": "Nothing queued to build."}
            _write(store, idle)
            return idle
        baseline = _snapshot()
        ids = [s.id for s in queued]
        for s in queued:  # annotate the audit trail; state stays QUEUED until the build completes
            store.upsert(advance(s, WorkflowState.QUEUED, "Build orchestrator", "Handed off to single-builder build"))
        state = {
            "status": "AWAITING_BUILD",
            "command": config.PINNED_BUILD_COMMAND,
            "model": config.PINNED_MODEL,
            "baseline": baseline,
            "handed_off_ids": ids,
            "started_at": now_iso(),
            "message": (
                f"Handed off {len(ids)} contribution(s). Run the pinned build to publish: "
                f"`{config.PINNED_BUILD_COMMAND}` (pinned {config.PINNED_MODEL}). "
                "They go live once the build completes."
            ),
        }
        _write(store, state)
        return state


def poll(store: WorkflowStore) -> dict:
    """Return the build status, auto-detecting completion (the real build rewrote the graph)."""
    with _lock:
        state = _read(store)
        if state.get("status") != "AWAITING_BUILD":
            return state
        if _baseline_changed(state.get("baseline"), _snapshot()):
            return _finish(store, state)
        return state


def confirm(store: WorkflowStore) -> dict:
    """Manual fallback: the operator asserts the pinned build ran — advance handed-off → LIVE."""
    with _lock:
        state = _read(store)
        if state.get("status") != "AWAITING_BUILD":
            return state
        return _finish(store, state)
