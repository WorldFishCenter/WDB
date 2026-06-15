"""`unanswered` is populated, never silently dropped, when a mode grounds nothing (§6 r4)."""

from router import Route, answer


def test_mode_a_states_unanswered_when_no_entity_matches(backends):
    ans = answer("List the projects in Atlantis?", backends=backends)
    assert not ans.claims                # 'Atlantis' matches no committed node
    assert ans.unanswered                # stated, not hidden


def test_a_mode_that_grounds_nothing_surfaces_in_unanswered(backends):
    # Force a fan-out to all three on an enumeration-only question: A grounds,
    # B (no recorded passage) and C (no recorded resolution) cannot — and say so
    # rather than letting A's answer paper over them.
    routes = [Route("A", "forced"), Route("B", "forced"), Route("C", "forced")]
    ans = answer("What projects operate in Kenya?", backends=backends, routes=routes)
    assert "A" in ans.modes_grounded
    assert "B" not in ans.modes_grounded
    assert "C" not in ans.modes_grounded
    assert len(ans.unanswered) >= 2      # B's and C's parts both stated


def test_unanswered_parts_are_not_back_filled_by_another_mode(backends):
    # the answered part stays answered; the unanswerable parts stay unanswered —
    # no mode invents to cover another's gap (§5).
    routes = [Route("A", "forced"), Route("C", "forced")]
    ans = answer("What projects operate in Kenya?", backends=backends, routes=routes)
    assert ans.claims                                  # A grounded
    assert all(c.mode == "A" for c in ans.claims)      # C did not back-fill
    assert ans.unanswered                              # C's part is stated
