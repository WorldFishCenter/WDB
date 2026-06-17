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

This file builds nothing else the spec excludes — no auth, no Dockerfile, no rate-limiting or
caching. Run it locally with::

    uv run uvicorn wdb_api.app:app          # ANTHROPIC_API_KEY in the env → Live, else Replay
"""

from __future__ import annotations

import os
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from wdb_router import answer
from wdb_router.backends import Backends, live_backends, replay_backends

from .serialize import serialize_answer


def select_backends() -> Backends:
    """The router CLI's exact gate: Live with an API key, Replay without.

    Live loads Mode B's real Chroma index + cross-encoder reranker and uses the Opus 4.8
    synthesis/resolver arms; without a key the offline Replay backends keep the service
    functional and need no model or network. Identical to ``wdb_router.cli``'s ``--live``
    default split, so the API answers exactly what the CLI would.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return live_backends()
    return replay_backends()


def _backend_mode(backends: Backends) -> str:
    """Report which backends are live without importing the retriever classes."""
    return "live" if type(backends.b_retriever).__name__ == "LiveRetriever" else "replay"


class AnswerRequest(BaseModel):
    """The request body for ``POST /answer`` — just the natural-language question."""

    question: str = Field(..., min_length=1,
                          description="the natural-language question to route across Modes A/B/C")


def create_app(backends_factory: Callable[[], Backends] | None = None) -> FastAPI:
    """Build the app. ``backends_factory`` is invoked **once** at startup (tests inject Replay).

    Defaulting the factory to :func:`select_backends` keeps the env-gated Live/Replay choice;
    passing a factory lets the suite force deterministic offline backends without a key.
    """
    factory = backends_factory or select_backends

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Build the heavy backends ONCE here — Mode B's embedder + reranker load at this point,
        # not per request. This is the persistent-host (Cloud Run, not serverless) contract:
        # a cold start per request would reload the models. Tests run this with Replay (no
        # model, no network) via an injected factory.
        app.state.backends = factory()
        app.state.backend_mode = _backend_mode(app.state.backends)
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
            "reranker_loaded": getattr(backends.b_retriever, "reranker", None) is not None,
        }

    @app.post("/answer")
    def post_answer(req: AnswerRequest, request: Request) -> dict:
        """Route the question and return the full §6 answer contract, serialized faithfully.

        Sync ``def`` on purpose: FastAPI runs it in a threadpool, so the blocking router call
        (CPU, and a network LLM hop under Live) never blocks the event loop. Faithful
        pass-through — we return exactly what the router grounded; refusals stay refusals,
        ``unanswered`` stays ``unanswered``. No ``response_model``: a Pydantic model would
        *filter* fields, and the whole point is to drop nothing the contract carries.
        """
        result = answer(req.question.strip(), request.app.state.backends)
        return serialize_answer(result)

    return app


# The served entry point — `uv run uvicorn wdb_api.app:app`. Construction is cheap (the
# backends build lazily in the lifespan, on startup), so importing this module loads no models.
app = create_app()
