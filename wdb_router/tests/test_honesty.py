"""Honesty pass-through: the router respects each mode's native refusal/guard.

Mode B's off-topic refusal is in ``test_mode_b_refusal.py``. Here:

* **Mode C — vetted-band gate.** A resolution pinned on a generic, shared value ("Gill Net",
  shared by all three trip tables) is *outside* the vetted band; Mode C refuses by
  construction. The router must surface that refusal as ``unanswered`` — never a number.
* **Mode A — cite-check downgrade.** A reasoner that fabricates an edge must never have its
  fabrication surface: Mode A's mechanical cite-check fails and downgrades to enumeration.
  The router must surface the downgraded answer, never the fabricated edge — it calls Mode A's
  entry point and respects the gate, it does not route around it.
"""

from mode_a.extract import get_graph
from mode_c.fixtures.resolutions import OUT_OF_BAND_GILLNET

from wdb_router import answer
from wdb_router.backends import replay_backends
from wdb_contract import UnansweredCode


# --- Mode C: vetted-band gate ------------------------------------------------- #

def test_mode_c_out_of_band_is_refused_not_computed():
    q = "Average trip duration for Gill Net trips?"          # routes to C ("average")
    backends = replay_backends(recorded_resolutions={q: OUT_OF_BAND_GILLNET})
    ans = answer(q, backends=backends)
    assert not ans.answered                                  # no fabricated number
    assert not ans.claims and not ans.figures
    assert ans.unanswered                                    # stated (§6 r4)
    assert any(u.code is UnansweredCode.OUT_OF_BAND for u in ans.unanswered)


# --- Mode A: cite-check downgrade --------------------------------------------- #

class _Fabricator:
    """A reasoner that fabricates an edge — Mode A's cite-check must reject + downgrade it."""

    def reason(self, serialized):
        return {
            "answer": "Peskas is directly wired to a made-up node.",
            "connected": True,
            "cited_edges": [{"source": "peskas_hub", "relation": "totally_made_up",
                             "target": "fake_node_xyz", "confidence": "EXTRACTED"}],
            "inferred_flags": [],
        }


def test_mode_a_failed_cite_check_never_surfaces_fabrication():
    # this question routes to A only, and inside Mode A to the bridges→reasoning path
    q = "Which initiatives share methods or data with Peskas, and how?"
    backends = replay_backends()
    backends.a_reasoner = _Fabricator()
    ans = answer(q, backends=backends)

    assert ans.modes_grounded in (["A"], [])      # downgraded enumeration (or clean refusal)
    blob = " ".join(
        [c.text for c in ans.claims]
        + [cit.locator for c in ans.claims for cit in c.citations]
        + [u.text for u in ans.unanswered]
    )
    assert "fake_node_xyz" not in blob            # the fabricated edge never surfaces
    assert "totally_made_up" not in blob


def test_mode_a_cite_check_downgrade_still_grounds_real_edges():
    # the downgrade is not a silent drop: it enumerates Peskas's real neighborhood
    q = "Which initiatives share methods or data with Peskas, and how?"
    backends = replay_backends()
    backends.a_reasoner = _Fabricator()
    ans = answer(q, backends=backends)
    assert ans.claims                             # real enumeration claims surfaced
    g = get_graph()
    for c in ans.claims:
        for cit in c.citations:
            assert cit.confidence in {"EXTRACTED", "INFERRED"}   # a real graph edge
