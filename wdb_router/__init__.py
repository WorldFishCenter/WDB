"""WDB production router — the dispatcher over Modes A + B + C.

Given a question it (1) **routes** to the set of modes whose §5 signals fire, (2)
**dispatches** to those real modes in one pass (their library entry points —
``mode_a``/``mode_b``/``mode_c``, reimplementing none), and (3) **composes** their results
into one §6 :class:`RouterAnswer` — every claim carrying its mode tag and its mode's native
citation, merged graph associations, Mode-C figures, and an ``unanswered`` list for anything
no mode could ground (never back-filled).

It is a **dispatcher**, not an agent: a one-pass fan-out + merge today, built with a clean
routing ↔ composition seam (``routing.route`` decides modes; ``composition.compose`` calls
them; ``dispatch.answer`` ties them once) so a future agentic version can slot into that seam
without changing the modes or the contract. No orchestration framework, no loop, no state
machine is built here.

Public surface:

* :func:`route`   — §5 layer-1 intent routing (``question -> RoutingDecision``).
* :func:`compose` — dispatch a decision's modes + merge (the composition half).
* :func:`answer`  — the one-pass dispatcher: route + compose into a :class:`RouterAnswer`.
* :func:`replay_backends` / :func:`live_backends` — the offline / real backends.
"""

from .backends import Backends, live_backends, replay_backends
from .composition import compose
from .contract import Route, RouterAnswer, RoutingDecision, add_associations
from .dispatch import answer
from .routing import route

__all__ = [
    "route",
    "compose",
    "answer",
    "Backends",
    "replay_backends",
    "live_backends",
    "RouterAnswer",
    "RoutingDecision",
    "Route",
    "add_associations",
]
