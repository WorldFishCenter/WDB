"""The routing ↔ composition seam is real, not just claimed.

The phase brief requires a unit test confirming routing decisions are made *separately* from
composition — the boundary a future agentic router would slot into. Three checks:

1. **Routing is backend-free by construction** — ``route`` takes only the question, so it
   *cannot* dispatch a mode; the decision is computed without any backend.
2. **Composition dispatches exactly the decision** — a decision naming only A leaves the B/C
   backends untouched (they would raise if dispatched).
3. **Composition obeys the decision, never re-routes** — given a decision that disagrees with
   what ``route`` would pick, ``compose`` honors the decision, not the question's natural
   route.
"""

import inspect

from wdb_router import Route, RoutingDecision, answer, compose, route
from wdb_router.backends import replay_backends


class _BoomRetriever:
    def retrieve(self, *a, **k):
        raise AssertionError("Mode B was dispatched but the decision did not include B")


class _BoomResolver:
    def resolve(self, *a, **k):
        raise AssertionError("Mode C was dispatched but the decision did not include C")


def test_routing_is_backend_free_by_construction():
    # routing takes only the question — it has no backend to call a mode with
    assert list(inspect.signature(route).parameters) == ["question"]
    decision = route("Average total catch per trip by county in Kenya?")
    assert isinstance(decision, RoutingDecision)
    assert decision.modes == ["C"]
    # pure: same question -> same decision
    assert route("Average total catch per trip by county in Kenya?").modes == ["C"]


def test_composition_dispatches_exactly_the_decision(backends):
    # a decision naming only A must not touch the B/C backends
    b = replay_backends()
    b.b_retriever = _BoomRetriever()       # raise if Mode B is dispatched
    b.c_resolver = _BoomResolver()         # raise if Mode C is dispatched
    decision = RoutingDecision(routes=(Route("A", "forced"),))
    ans = compose("What projects operate in Kenya?", decision, b)   # must not raise
    assert ans.modes_grounded == ["A"]
    assert ans.modes_fired == ["A"]


def test_composition_obeys_the_decision_not_the_natural_route():
    # the question would naturally route to A, but compose is handed a C-only decision and
    # must honor it — dispatching C, never A (so no Mode-A claims appear).
    q = "What projects operate in Kenya?"
    assert route(q).modes == ["A"]                      # the natural route
    b = replay_backends()
    b.b_retriever = _BoomRetriever()                    # B must not be dispatched either
    decision = RoutingDecision(routes=(Route("C", "forced"),))
    ans = compose(q, decision, b)
    assert ans.modes_fired == ["C"]                     # routes come from the decision
    assert not any(c.mode == "A" for c in ans.claims)   # A was not dispatched
    assert ans.unanswered                               # C cannot ground it -> stated


def test_answer_is_route_then_compose_one_pass(backends):
    # the dispatcher's one-pass behaviour == compose over the routed decision
    q = "Average total catch per trip in Kwale?"
    via_answer = answer(q, backends=backends)
    via_seam = compose(q, route(q), backends)
    assert via_answer.modes_grounded == via_seam.modes_grounded == ["C"]
