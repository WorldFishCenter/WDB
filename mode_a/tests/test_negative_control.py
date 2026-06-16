"""Negative control (carried from the proof) — the cite-check MUST reject these.

A guard that passes everything proves nothing. This injects the exact Mode-A failure modes
over the freshly-extracted subgraphs and asserts the cite-check catches each — the regression
proof that the gate has teeth, independent of how rarely the cold model trips it
(MODEL.md: 0/10).

  N1  fabricated edge on the not-connected case (Q4): claims FASA shares_data_with the WIO
      harmonization hub — an edge that does NOT exist.        -> C1 FAIL + C4 FAIL
  N2  an INFERRED edge stated as fact (Q5): real INFERRED edge tagged EXTRACTED, unflagged.
                                                              -> C2 FAIL + C3 FAIL
  N3  an invented 2-hop path on the 0-edge Q4 subgraph (via WorldFish).  -> C1 FAIL + C4 FAIL
"""

from mode_a import extract
from mode_a.citecheck import cite_check
from mode_a.route import route


def _subgraph(question, g):
    r = route(question, g)
    if r.extraction == "neighborhood":
        return extract.neighborhood(g, r.entities[0])
    if r.extraction == "bridges":
        return extract.bridges(g, r.entities[0])
    return extract.relate(g, r.entities[0], r.entities[1])


def E(s, rel, t, c):
    return {"source": s, "relation": rel, "target": t, "confidence": c}


Q4 = "How does FASA's feed formulation work relate to the WIO data harmonization initiative?"
Q5 = "Is the WIO data harmonization initiative related to the Digital Transformation Accelerator?"


def test_n1_fabricated_edge_on_not_connected_case(graph):
    sub = _subgraph(Q4, graph)
    assert sub.disconnected
    bad = {"answer": "FASA shares data with the WIO harmonization initiative.",
           "connected": True,
           "cited_edges": [E("fasa_repo", "shares_data_with", "data_harmonization_hub", "EXTRACTED")],
           "inferred_flags": []}
    v = cite_check(sub.edges, sub.disconnected, bad)
    assert not v.honest
    assert v.checks["C1"] is False and v.checks["C4"] is False
    assert v.fabricated  # the fabricated triple was detected by id


def test_n2_inferred_edge_stated_as_fact(graph):
    sub = _subgraph(Q5, graph)
    inferred = [e for e in sub.edges if e["confidence"] == "INFERRED"]
    assert inferred, "Q5 subgraph should contain at least one INFERRED edge"
    e = inferred[0]
    bad = {"answer": "They are related.", "connected": True,
           "cited_edges": [E(e["source"], e["relation"], e["target"], "EXTRACTED")],  # mistagged
           "inferred_flags": []}                                                       # and unflagged
    v = cite_check(sub.edges, sub.disconnected, bad)
    assert not v.honest
    assert v.checks["C2"] is False and v.checks["C3"] is False


def test_n3_invented_path_via_worldfish(graph):
    sub = _subgraph(Q4, graph)
    bad = {"answer": "FASA connects to harmonization through WorldFish.",
           "connected": True,
           "cited_edges": [E("fasa_repo", "references", "shared_worldfish", "EXTRACTED"),
                           E("data_harmonization_hub", "references", "shared_worldfish", "EXTRACTED")],
           "inferred_flags": []}
    v = cite_check(sub.edges, sub.disconnected, bad)
    assert not v.honest
    assert v.checks["C1"] is False and v.checks["C4"] is False
