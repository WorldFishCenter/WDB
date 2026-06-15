"""Throwaway router harness over WDB Modes A + B + C.

⚠️  A disposable **test harness**, not the product router and not a UI. It exists
to let one question be routed to one or more modes and watched compose into a
single §6 answer — validating the composition logic and the answer contract before
any frontend exists. It reuses the modes as libraries (``mode_b``, ``mode_c``) and
a harness-grade Mode-A enumeration stand-in (``router.mode_a`` — NOT the real Mode
A, which is Claude over the graph; see that module's docstring).

Public surface:

* :func:`classify` — §5 layer-1 intent routing (keyword/signal → list of modes).
* :func:`answer`   — route + dispatch + compose into a :class:`RouterAnswer`.
* :func:`replay_backends` / :func:`live_backends` — the offline / real backends.
"""

from .contract import Route, RouterAnswer
from .intent import classify
from .router import Backends, answer, live_backends, replay_backends

__all__ = [
    "classify",
    "answer",
    "Backends",
    "replay_backends",
    "live_backends",
    "RouterAnswer",
    "Route",
]
