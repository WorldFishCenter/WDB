"""The composition half of the router's seam — dispatch a decision, merge into one §6 answer.

:func:`compose` is given a :class:`~wdb_router.contract.RoutingDecision` (it does **not**
decide routing) and a :class:`~wdb_router.backends.Backends`, dispatches **exactly** the
modes the decision names by calling their real library entry points
(``mode_a.answer_question`` / ``mode_b.answer_question`` / ``mode_c.answer_question``), and
merges their §6 fragments into one :class:`~wdb_router.contract.RouterAnswer`. It
reimplements no mode.

Honesty carries over from the modes; the router must not weaken it:

* Every claim a mode returns already carries its citation (§6 r1) — the router only
  concatenates, it never synthesizes a claim of its own.
* A mode that returns nothing / "not available" contributes its part to ``unanswered``; the
  router **never** back-fills that gap with another mode's content (§5, §6 r4).
* Each mode's own refusal (Mode B's reranker-gated thin refusal, Mode C's vetted-band gate,
  Mode A's cite-check downgrade) happens *inside* its entry point — the router calls the
  entry point and surfaces whatever it returns, refusal included. It never routes around a
  refusal.

The seam: because :func:`compose` consumes a decision rather than deriving one, an agentic
router could call ``route`` again from a returned :class:`RouterAnswer` and call
:func:`compose` once more — accumulating into the contract — without any change here, to the
modes, or to the contract. Today the dispatcher (``dispatch.py``) calls this exactly once.
"""

from __future__ import annotations

from .backends import Backends
from .contract import RouterAnswer, RoutingDecision, add_associations


def _run_mode_a(question: str, b: Backends):
    from mode_a import answer_question

    return answer_question(question, b.a_reasoner, b.a_graph)


def _run_mode_b(question: str, b: Backends):
    from mode_b.pipeline import answer_question

    return answer_question(question, b.b_retriever, b.b_synth, b.nodes, b.links,
                           known_initiatives=b.known_initiatives)


def _run_mode_c(question: str, b: Backends):
    from mode_c.pipeline import answer_question

    return answer_question(question, b.c_resolver, b.catalog)


def compose(question: str, decision: RoutingDecision, backends: Backends) -> RouterAnswer:
    """Dispatch the decision's modes and assemble their fragments into one §6 answer.

    Modes are dispatched in a fixed A→B→C order for deterministic output, regardless of the
    order signals fired in. Each mode already returns the §6 shape and enforces "no claim
    without a citation"; merging is concatenate + de-dup (associations by edge triple).
    """
    ra = RouterAnswer(question=question, routes=list(decision.routes))
    fired = set(decision.modes)

    if "A" in fired:
        a = _run_mode_a(question, backends)
        ra.claims.extend(a.claims)
        add_associations(ra, a.associations)
        ra.unanswered.extend(a.unanswered)

    if "B" in fired:
        b = _run_mode_b(question, backends)
        ra.claims.extend(b.claims)
        add_associations(ra, b.associations)
        ra.unanswered.extend(b.unanswered)

    if "C" in fired:
        c = _run_mode_c(question, backends)
        ra.claims.extend(c.claims)
        ra.figures.extend(c.figures)
        ra.unanswered.extend(c.unanswered)

    return ra
