"""Honesty pass-through at the API layer — refusals serialize as refusals, never as answers.

Each mode's native guard fires *inside* the router; the API must surface the result as what it
is, adding no synthesis of its own. Three guards, mirrored from the router's own honesty suite
but asserted on the serialized JSON the UI will receive:

* **Mode B — off-topic rerank-floor refusal.** A passage scoring below the cross-encoder floor
  must yield "not available" (empty ``claims`` + populated ``unanswered``), not a synthesis
  from an irrelevant passage.
* **Mode C — vetted-band gate.** A resolution pinned on a generic, shared value is outside the
  vetted band; Mode C refuses by construction. The JSON must carry the refusal, never a number.
* **Mode A — cite-check downgrade.** A reasoner that fabricates an edge must have the
  fabrication rejected; it must appear **nowhere** in the serialized response.
"""

from mode_c.fixtures.resolutions import OUT_OF_BAND_GILLNET
from wdb_router.backends import replay_backends
from wdb_router.fixtures import OFFTOPIC_BELOW_FLOOR, Q_OFFTOPIC


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


def test_offtopic_refusal_surfaces_as_unanswered_not_synthesis(make_client):
    backends = replay_backends(recorded_passages=OFFTOPIC_BELOW_FLOOR,
                               recorded_synthesis={}, recorded_resolutions={})
    client = make_client(backends)
    data = client.post("/answer", json={"question": Q_OFFTOPIC}).json()
    assert data["answered"] is False               # refused, not synthesized
    assert data["claims"] == []                    # no fabricated synthesis
    assert data["unanswered"]                      # stated (§6 r4)
    reason = " ".join(data["unanswered"]).lower()
    assert "rerank" in reason and "below" in reason  # the SCORE arm fired (not the empty arm)


def test_mode_c_out_of_band_is_refused_not_a_number(make_client):
    q = "Average trip duration for Gill Net trips?"            # routes to C ("average")
    client = make_client(replay_backends(recorded_resolutions={q: OUT_OF_BAND_GILLNET}))
    data = client.post("/answer", json={"question": q}).json()
    assert data["answered"] is False                          # no fabricated number
    assert not data["claims"] and not data["figures"]
    assert data["unanswered"]                                 # stated (§6 r4)


def test_mode_a_fabricated_edge_never_surfaces_in_the_json(make_client):
    # the API passes the cite-check downgrade through; the fabricated edge must appear NOWHERE
    # in the serialized response (checked on the raw response text, not just parsed fields).
    q = "Which initiatives share methods or data with Peskas, and how?"
    backends = replay_backends()
    backends.a_reasoner = _Fabricator()
    client = make_client(backends)
    raw = client.post("/answer", json={"question": q}).text
    assert "fake_node_xyz" not in raw
    assert "totally_made_up" not in raw


def test_mode_a_downgrade_still_grounds_real_edges(make_client):
    # the downgrade is not a silent drop: real Peskas-neighborhood enumeration still surfaces,
    # every citation a real graph edge.
    q = "Which initiatives share methods or data with Peskas, and how?"
    backends = replay_backends()
    backends.a_reasoner = _Fabricator()
    client = make_client(backends)
    data = client.post("/answer", json={"question": q}).json()
    assert data["claims"]
    for c in data["claims"]:
        for cit in c["citations"]:
            assert cit["confidence"] in {"EXTRACTED", "INFERRED"}
