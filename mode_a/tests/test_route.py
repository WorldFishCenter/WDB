"""Shape routing — direct questions go to enumeration, multi-hop/explanatory to reasoning.

Routing is the augmentation's whole point: cheap enumeration stays for direct questions,
the gated reasoning path handles relational ones (proof_a/FINDINGS.md). These pin that the
5 proof questions land on the right path + extraction primitive, plus the direct-vs-multi-hop
distinction the brief calls out.
"""

from mode_a.route import route


def test_direct_question_routes_to_enumeration(graph):
    r = route("What is Peskas connected to?", graph)
    assert r.path == "enumeration"
    assert r.extraction == "neighborhood"
    assert r.entities == ["peskas_hub"]


def test_how_why_two_entities_routes_to_reasoning_relate(graph):
    r = route("How does Peskas relate to the WIO data harmonization work, and why?", graph)
    assert r.path == "reasoning"
    assert r.extraction == "relate"
    assert r.entities == ["peskas_hub", "data_harmonization_hub"]


def test_which_initiatives_share_routes_to_reasoning_bridges(graph):
    r = route("Which initiatives share methods or data with Peskas, and how?", graph)
    assert r.path == "reasoning"
    assert r.extraction == "bridges"
    assert r.entities == ["peskas_hub"]


def test_is_x_related_to_y_routes_to_reasoning_relate(graph):
    r = route("Is the WIO data harmonization initiative related to the Digital Transformation Accelerator?", graph)
    assert r.path == "reasoning"
    assert r.extraction == "relate"
    assert set(r.entities) == {"data_harmonization_hub", "dta_hub"}


def test_unknown_entity_routes_unresolved(graph):
    r = route("How does Atlantis relate to Narnia?", graph)
    assert r.path == "unresolved"
    assert r.entities == []


def test_direct_vs_multihop_split(graph):
    # the brief's explicit check: a direct question → enumeration, a multi-hop → reasoning
    assert route("What is Peskas connected to?", graph).path == "enumeration"
    assert route("How does FASA's feed formulation work relate to the WIO data harmonization initiative?",
                 graph).path == "reasoning"
