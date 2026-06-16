"""`unanswered` is populated, never silently dropped, when a mode grounds nothing (§6 r4).

The forced-decision cases pass an explicit :class:`RoutingDecision` — the same hook a future
agent would drive — to fan out to modes that cannot ground the question, and assert no mode
back-fills another's gap.
"""

from wdb_router import Route, RoutingDecision, answer


def test_mode_a_states_unanswered_when_no_entity_matches(backends):
    ans = answer("List the projects in Atlantis?", backends=backends)
    assert not ans.claims                # 'Atlantis' matches no committed node
    assert ans.unanswered                # stated, not hidden


def _forced(*modes):
    return RoutingDecision(routes=tuple(Route(m, "forced") for m in modes))


def test_a_mode_that_grounds_nothing_surfaces_in_unanswered(backends):
    # Force a fan-out to all three on an enumeration-only question: A grounds, B (no recorded
    # passage) and C (no recorded resolution) cannot — and say so rather than letting A's
    # answer paper over them.
    ans = answer("What projects operate in Kenya?", backends=backends,
                 decision=_forced("A", "B", "C"))
    assert "A" in ans.modes_grounded
    assert "B" not in ans.modes_grounded
    assert "C" not in ans.modes_grounded
    assert len(ans.unanswered) >= 2      # B's and C's parts both stated


def test_unanswered_parts_are_not_back_filled_by_another_mode(backends):
    # the answered part stays answered; the unanswerable parts stay unanswered — no mode
    # invents to cover another's gap (§5).
    ans = answer("What projects operate in Kenya?", backends=backends,
                 decision=_forced("A", "C"))
    assert ans.claims                                  # A grounded
    assert all(c.mode == "A" for c in ans.claims)      # C did not back-fill
    assert ans.unanswered                              # C's part is stated
