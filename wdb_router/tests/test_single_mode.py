"""Each mode answers its own proven case, end-to-end through the router.

Mode A is the **real** Mode A (graph enumeration over the committed graph — no model, no
fixture); B and C run on their recorded Replay fixtures.
"""

from mode_b.fixtures.recorded import Q_COVERED
from mode_c.fixtures.resolutions import Q4

from wdb_router import answer
from wdb_router.fixtures import GROUPED


def test_enumeration_grounds_in_mode_A(backends):
    ans = answer("What projects operate in Kenya?", backends=backends)
    assert ans.modes_grounded == ["A"]
    assert ans.claims and all(c.mode == "A" for c in ans.claims)
    texts = " | ".join(c.text for c in ans.claims)
    assert "Peskas" in texts and "FASA" in texts      # real Kenya-touching projects
    assert ans.associations                            # the typed-edge payload (§6)
    # Mode A's native citation artifact: a graph edge triple with its confidence tag
    cit = ans.claims[0].citations[0]
    assert cit.locator and cit.confidence in {"EXTRACTED", "INFERRED"}


def test_quantitative_grounds_in_mode_C(backends):
    ans = answer(Q4, backends=backends)                # "Average total catch per trip in Kwale?"
    assert ans.modes_grounded == ["C"]
    claim = ans.claims[0]
    assert claim.mode == "C"
    assert "31.88" in claim.text                       # the proof's trip-grain answer
    cit = claim.citations[0]
    assert cit.sql.strip().upper().startswith("WITH")  # the citation IS the SQL (§6 r3)
    assert cit.result == [{"n": 50422, "avg_total_catch_kg_per_trip": 31.88}]


def test_synthesis_grounds_in_mode_B(backends):
    ans = answer(Q_COVERED, backends=backends)
    assert ans.modes_grounded == ["B"]
    claim = ans.claims[0]
    assert claim.mode == "B"
    cit = claim.citations[0]
    assert cit.quote                                   # verbatim passage span
    assert cit.nodes                                   # joined graph node(s) at doc grain
    assert ans.associations


def test_grouped_quantitative_produces_a_figure(backends):
    ans = answer(GROUPED, backends=backends)
    assert ans.figures                                 # the contract's figures payload
    fig = ans.figures[0]
    assert fig.spec["kind"] == "bar"
    assert fig.query and fig.result                    # figure ships with its SQL (§8)
    assert fig.result[0]["gaul_1_name"] == "Lamu"      # top of the by-county ranking
