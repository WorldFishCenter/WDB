"""WDB read API — a thin, faithful FastAPI bridge over :func:`wdb_router.answer`.

The read UI's backend: it exposes the production router's single entry point over HTTP and
serializes the full §6 :class:`~wdb_router.contract.RouterAnswer` to JSON, dropping nothing the
contract carries (every mode's claims + native citations, the merged associations, Mode-C
figures, the ``unanswered`` list) and adding no synthesis of its own. It reimplements no mode
and no routing — it calls :func:`wdb_router.answer` and serializes the result.

Backends mirror the router CLI's Live/Replay split (Live with ``ANTHROPIC_API_KEY``, offline
Replay without); Mode B's models load once on startup, never per request. Runs **locally** —
nothing here is deployed.

Public surface:

* :func:`create_app`      — build the FastAPI app (tests inject offline backends).
* :func:`select_backends` — the env-gated Live/Replay chooser (the router CLI's gate).
* :func:`serialize_answer` — ``RouterAnswer`` → JSON-native dict (the UI's contract).
* :data:`app`             — the served ASGI app (``uvicorn wdb_api.app:app``).
"""

from .app import app, create_app, select_backends
from .serialize import serialize_answer

__all__ = ["app", "create_app", "select_backends", "serialize_answer"]
