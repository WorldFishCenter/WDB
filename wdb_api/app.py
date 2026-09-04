"""The local FastAPI bridge over :func:`wdb_router.answer` — the read UI's backend.

A **thin, faithful** HTTP wrapper, nothing more: ``POST /answer`` routes a question through
the production router and returns the full §6 :class:`~wdb_router.contract.RouterAnswer`
serialized to JSON (see :mod:`wdb_api.serialize`) — every claim with its mode tag and native
citation, the merged associations, Mode-C figures, and the ``unanswered`` list, with no field
flattened and **no synthesis of our own**. A mode's refusal surfaces as what it is (empty
``claims`` + a populated ``unanswered`` + ``answered: false``), because the router already made
it so and we only pass it through.

Backends are wired exactly like the router CLI (``wdb_router.cli``): **Live** (real Chroma +
cross-encoder reranker + Opus 4.8 synthesis/resolver) when ``ANTHROPIC_API_KEY`` is set, else
the **offline Replay** backends — so the service runs key-free and offline for tests and local
use (degraded but honest, the same posture the modes take). The heavy Mode-B models (embedder +
reranker) load **once on startup** via the lifespan, never per request: this is a persistent
service (Cloud Run, per ``RUNNING.md``), not serverless, and a cold start per request would
reload them.

**Cost tracking.** When running Live (API key set, no injected factory), every LLM call is
intercepted by a :class:`~cost_sim.tracker.TrackingClient` and recorded in a session-scoped
:class:`~cost_sim.tracker.CostLog`. Two endpoints expose the data:

* ``GET /cost``        — JSON breakdown (for programmatic use or the browser's JSON viewer)
* ``GET /cost/report`` — human-readable ASCII table; open this in the browser or curl it
  alongside the read UI to watch costs accumulate in real time.

Run locally with::

    uv run uvicorn wdb_api.app:app          # ANTHROPIC_API_KEY in the env → Live + tracked
"""

from __future__ import annotations

import os
import time
import traceback
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from wdb_router import answer
from wdb_router.backends import Backends, replay_backends

from .serialize import serialize_answer
from cost_sim.rates import label as _model_label
from cost_sim.tracker import CostLog, TrackingClient


# ── Backend selection (public API, re-exported from __init__.py) ─────────── #

def select_backends() -> Backends:
    """The router CLI's exact gate: Live with an API key, Replay without.

    Kept for backward compatibility — callers (tests, CLI) that import this name
    still work. The API's own lifespan uses :func:`_live_backends_tracked` when
    running live so cost tracking is wired in at startup.
    """
    from wdb_router.backends import live_backends
    if os.environ.get("ANTHROPIC_API_KEY"):
        return live_backends()
    return replay_backends()


# ── Live backends with cost tracking injected ────────────────────────────── #

def _live_backends_tracked(log: CostLog) -> Backends:
    """Live backends with TrackingClient wired into every LLM slot.

    Mirrors ``wdb_router.backends.live_backends()`` exactly, but injects a
    ``TrackingClient`` wrapper around ``anthropic.Anthropic()`` for each LLM-calling
    backend so every ``messages.create()`` call is recorded in ``log``. The Chroma
    index, reranker, and graph load unchanged — only the three LLM seams are wrapped.
    """
    import anthropic as _anthropic
    from mode_a import extract as a_extract
    from mode_a.reasoner import LiveReasoner
    from mode_b.corpus import walk_corpus
    from mode_b.index import DEFAULT_INDEX_DIR, open_collection
    from mode_b.pipeline import load_graph_default
    from mode_b.retrieve import LiveRetriever
    from mode_b.synth import LiveSynthesizer
    from mode_c.catalog import load_catalog
    from mode_c.resolver import LiveResolver
    from wdb_router.backends import WDB_ROOT

    real = _anthropic.Anthropic()
    nodes, links = load_graph_default()
    collection = open_collection(DEFAULT_INDEX_DIR)
    catalog = load_catalog(WDB_ROOT)
    known_initiatives = {f.split("/")[0] for f in walk_corpus(WDB_ROOT) if "/" in f}

    return Backends(
        a_reasoner=LiveReasoner(client=TrackingClient(real, log, "mode_a")),
        a_graph=a_extract.get_graph(),
        nodes=nodes,
        links=links,
        b_retriever=LiveRetriever(collection, use_reranker=True),
        b_synth=LiveSynthesizer(client=TrackingClient(real, log, "mode_b")),
        known_initiatives=known_initiatives,
        catalog=catalog,
        c_resolver=LiveResolver(catalog, client=TrackingClient(real, log, "mode_c")),
    )


# ── Helpers ───────────────────────────────────────────────────────────────── #

def _backend_mode(backends: Backends) -> str:
    return "live" if type(backends.b_retriever).__name__ == "LiveRetriever" else "replay"


def _fmt_usd(v: float) -> str:
    return f"${v:.5f}" if v < 0.001 else f"${v:.4f}"


def _monthly(avg: float, qpd: int) -> float:
    return avg * qpd * 30


# ── Cost report formatting ────────────────────────────────────────────────── #

def _render_report(state) -> str:
    log: CostLog = state.cost_log
    req_log: list[dict] = state.request_log
    started: datetime = state.session_started

    now = datetime.now(timezone.utc)
    elapsed = int((now - started).total_seconds())
    h, rem = divmod(elapsed, 3600)
    m, s = divmod(rem, 60)
    duration = f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"

    by_slot = log.by_slot()
    total_cost = log.total_usd()
    n_req = len(req_log)
    avg_per_req = total_cost / n_req if n_req else 0.0

    lines: list[str] = []
    W = 80

    def rule(char="─"):
        lines.append(char * W)

    def blank():
        lines.append("")

    lines.append("WDB Live Cost Tracker")
    lines.append(f"Session started {started.strftime('%Y-%m-%d %H:%M:%S UTC')}  ·  running {duration}")
    rule("═")
    blank()

    # ── Summary row ──────────────────────────────────────────────────────── #
    lines.append(
        f"  Requests: {n_req:<6}  Total: {_fmt_usd(total_cost):<12}  Avg/request: {_fmt_usd(avg_per_req)}"
    )
    if not by_slot:
        blank()
        lines.append("  No LLM calls recorded yet — ask a question in the read UI.")
        blank()
        lines.append(f"  JSON: GET /cost    Refresh: GET /cost/report")
        return "\n".join(lines)

    # ── By slot ───────────────────────────────────────────────────────────── #
    blank()
    lines.append("BY SLOT")
    rule()
    lines.append(
        f"  {'Slot':<8}  {'Model':<26}  {'Calls':>5}  {'Avg in / out tok':>18}  {'Avg $/call':>10}"
    )
    rule()
    for slot in ("mode_a", "mode_b", "mode_c"):
        recs = by_slot.get(slot)
        if not recs:
            lines.append(f"  {slot:<8}  {'—':26}  {'—':>5}  {'—':>18}  {'—':>10}")
            continue
        n = len(recs)
        slot_cost = sum(r.cost_usd for r in recs)
        avg_in = sum(r.in_tok for r in recs) / n
        avg_out = sum(r.out_tok for r in recs) / n
        lines.append(
            f"  {slot:<8}  {_model_label(recs[0].model):<26}  {n:>5}  "
            f"{avg_in:>7,.0f} / {avg_out:>6,.0f}  {_fmt_usd(slot_cost / n):>10}"
        )
    rule()
    blank()

    # ── Recent requests ───────────────────────────────────────────────────── #
    recent = req_log[-10:][::-1]
    lines.append(f"RECENT REQUESTS  (last {len(recent)} of {n_req})")
    rule()
    lines.append(f"  {'#':>3}  {'Time (UTC)':>8}  {'Modes':<7}  {'Cost':>8}  Question")
    rule()
    for r in recent:
        ts = datetime.fromtimestamp(r["ts"], tz=timezone.utc).strftime("%H:%M:%S")
        modes = "+".join(r["modes"]) if r["modes"] else "—"
        q = r["question"][:44] + ("…" if len(r["question"]) > 44 else "")
        cost_str = _fmt_usd(r["cost_usd"]) if not r.get("error") else "ERROR"
        lines.append(f"  {r['idx']:>3}  {ts:>8}  {modes:<7}  {cost_str:>8}  {q}")
    rule()
    blank()

    # ── Monthly projection ────────────────────────────────────────────────── #
    lines.append(f"MONTHLY PROJECTION  (at avg {_fmt_usd(avg_per_req)}/request × 30 days)")
    rule()
    lines.append(f"  {'q/day':>7}    {'$/month':>10}")
    rule()
    for qpd in (10, 50, 100, 500, 1000):
        lines.append(f"  {qpd:>7,}    ${_monthly(avg_per_req, qpd):>9,.2f}")
    rule()
    blank()
    lines.append(f"  JSON: GET /cost    Refresh: GET /cost/report")
    blank()

    return "\n".join(lines)


# ── App factory ───────────────────────────────────────────────────────────── #

class AnswerRequest(BaseModel):
    """The request body for ``POST /answer`` — just the natural-language question."""
    question: str = Field(..., min_length=1,
                          description="the natural-language question to route across Modes A/B/C")


def create_app(backends_factory: Callable[[], Backends] | None = None) -> FastAPI:
    """Build the app. ``backends_factory`` is invoked **once** at startup (tests inject Replay).

    When no factory is provided and ``ANTHROPIC_API_KEY`` is set, uses
    :func:`_live_backends_tracked` so every LLM call is measured. Tests inject a Replay
    factory, which bypasses tracking (the log stays empty, the cost endpoints still serve).
    """
    use_factory = backends_factory  # None = auto-detect Live vs Replay

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        log = CostLog()
        if use_factory is None and os.environ.get("ANTHROPIC_API_KEY"):
            # Live mode — wire in tracking at every LLM seam
            app.state.backends = _live_backends_tracked(log)
            app.state.backend_mode = "live"
        elif use_factory is not None:
            # Explicit factory (tests) — use as-is, no tracking
            app.state.backends = use_factory()
            app.state.backend_mode = _backend_mode(app.state.backends)
        else:
            # No API key — Replay
            app.state.backends = replay_backends()
            app.state.backend_mode = "replay"
        app.state.cost_log = log
        app.state.request_log = []
        app.state.session_started = datetime.now(timezone.utc)
        yield

    app = FastAPI(
        title="WDB read API",
        summary="HTTP bridge over the WDB router — the read UI's backend (local, not deployed)",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health(request: Request) -> dict:
        """Liveness + which backends loaded on startup (and whether the reranker is up)."""
        backends = request.app.state.backends
        return {
            "status": "ok",
            "backend": request.app.state.backend_mode,
            "cost_tracking": request.app.state.backend_mode == "live",
            # The adapter states which floor Mode B's gate is judging — read from the
            # declared `Reranker.kind`, not sniffed from a private attribute. `rerank_kind`
            # is the useful field ("rerank" | "cosine" | "replay"); `reranker_loaded` is kept
            # because the UI header reads it.
            "rerank_kind": getattr(backends.b_retriever, "ranking_kind", "replay"),
            "reranker_loaded": getattr(backends.b_retriever, "ranking_kind", None) == "rerank",
        }

    @app.post("/answer")
    def post_answer(req: AnswerRequest, request: Request) -> dict:
        """Route the question and return the full §6 answer contract, serialized faithfully.

        Sync ``def`` on purpose: FastAPI runs it in a threadpool, so the blocking router call
        (CPU, and a network LLM hop under Live) never blocks the event loop. Faithful
        pass-through — we return exactly what the router grounded; refusals stay refusals,
        ``unanswered`` stays ``unanswered``. No ``response_model``: a Pydantic model would
        *filter* fields, and the whole point is to drop nothing the contract carries.

        When cost tracking is active, the LLM calls made during this request are attributed
        to it and appended to ``app.state.request_log`` (visible at ``GET /cost/report``).
        """
        ts = time.time()
        try:
            result = answer(req.question.strip(), request.app.state.backends)
        except Exception as exc:
            tb = traceback.format_exc()
            return JSONResponse(
                {"error": str(exc), "traceback": tb},
                status_code=500,
            )
        serialized = serialize_answer(result)

        log: CostLog = request.app.state.cost_log
        recs = log.since(ts)
        if recs:
            q = req.question.strip()
            request.app.state.request_log.append({
                "idx": len(request.app.state.request_log) + 1,
                "question": q,
                "modes": sorted({r.slot.split("_")[1].upper() for r in recs}),
                "cost_usd": sum(r.cost_usd for r in recs),
                "in_tok": sum(r.in_tok for r in recs),
                "out_tok": sum(r.out_tok for r in recs),
                "ts": ts,
                "error": None,
                "calls": [
                    {"slot": r.slot, "model": r.model,
                     "in_tok": r.in_tok, "out_tok": r.out_tok,
                     "cost_usd": round(r.cost_usd, 6)}
                    for r in recs
                ],
            })

        return serialized

    @app.get("/cost")
    def get_cost(request: Request) -> dict:
        """JSON cost summary for the current session — all requests since startup."""
        log: CostLog = request.app.state.cost_log
        req_log: list[dict] = request.app.state.request_log
        by_slot = log.by_slot()
        total = log.total_usd()
        n = len(req_log)
        avg = total / n if n else 0.0
        return {
            "tracking": request.app.state.backend_mode == "live",
            "session_started": request.app.state.session_started.isoformat(),
            "requests": n,
            "total_cost_usd": round(total, 6),
            "avg_cost_per_request_usd": round(avg, 6),
            "by_slot": {
                slot: {
                    "model": recs[0].model,
                    "model_label": _model_label(recs[0].model),
                    "calls": len(recs),
                    "in_tok_total": sum(r.in_tok for r in recs),
                    "out_tok_total": sum(r.out_tok for r in recs),
                    "cost_total_usd": round(sum(r.cost_usd for r in recs), 6),
                    "cost_per_call_usd": round(sum(r.cost_usd for r in recs) / len(recs), 6),
                }
                for slot, recs in by_slot.items()
            },
            "recent_requests": req_log[-20:][::-1],
            "monthly_projections_usd": {
                str(qpd): round(avg * qpd * 30, 2)
                for qpd in (10, 50, 100, 500, 1000)
            },
        }

    @app.get("/cost/report", response_class=PlainTextResponse)
    def get_cost_report(request: Request) -> str:
        """Human-readable ASCII cost report — open in browser or curl while using the read UI.

        Refresh the page to see costs update after each question. The table shows:
        per-slot breakdown (model, calls, avg tokens, avg cost), recent requests, and
        a monthly projection at various query volumes.
        """
        return _render_report(request.app.state)

    return app


# The served entry point — `uv run uvicorn wdb_api.app:app`. Construction is cheap (the
# backends build lazily in the lifespan, on startup), so importing this module loads no models.
app = create_app()
