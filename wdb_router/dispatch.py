"""The dispatcher — the one-pass tie-point between routing and composition.

:func:`answer` is the single entry point the CLI and tests call: it **routes** the question
to a :class:`~wdb_router.contract.RoutingDecision` and **composes** the answer by dispatching
those modes — once. That is the whole of today's behaviour: a dispatcher, not an agent. No
LangGraph, no orchestration framework, no loop, no state machine.

This function is also the deliberate **seam** where a future agentic router would live. The
boundary is real, not cosmetic: routing (``route``) is a pure ``question -> decision``, and
composition (``compose``) consumes a decision it did not make and merges additively into the
contract. So an agent that decides the *next* mode from a previous mode's answer would
replace the body of *this* function with a loop — calling ``route``/``compose`` repeatedly
and accumulating into one :class:`~wdb_router.contract.RouterAnswer` — and would need to
change neither the modes nor the contract. We build none of that here; we only keep the
boundary clean so it remains possible.
"""

from __future__ import annotations

from .backends import Backends, replay_backends
from .composition import compose
from .contract import RouterAnswer, RoutingDecision
from .routing import route


def answer(question: str, backends: Backends | None = None,
           decision: RoutingDecision | None = None) -> RouterAnswer:
    """Route, dispatch, and compose — one pass.

    ``decision`` is normally derived from the question; tests/callers may pass an explicit
    one to force a mode set (the same hook a future agent would drive). ``backends`` defaults
    to the deterministic Replay backends.
    """
    backends = backends or replay_backends()
    decision = decision if decision is not None else route(question)
    return compose(question, decision, backends)
