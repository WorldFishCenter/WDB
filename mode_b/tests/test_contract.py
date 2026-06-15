"""The §6 answer contract — Claim = passage quote + span + matching node(s).

Deterministic: feeds a recorded passage + synthesis through `assemble` against
the real graph.json, and checks the dual payload (citation nodes + associations)
and the refusal shape.
"""

from mode_b.contract import assemble, refusal
from mode_b.retrieve import Passage

PESKAS_SOFTWAREX = "peskas/peskas_automated_analytics_softwarex_2025.pdf"


def _passage():
    return Passage(
        text="Validation: outlier detection and error identification with an email alert system.",
        source_file=PESKAS_SOFTWAREX, location="page 2 [part 1/2]",
        initiative="peskas", cos_score=68.2,
    )


def test_claim_carries_quote_span_and_matching_nodes(graph, wdb_root):
    nodes, links = graph
    answer = assemble("How does Peskas validate data?", [_passage()],
                      "Peskas validates via outlier detection and email alerts [1].",
                      nodes, links, wdb_root)

    assert answer.answered
    claim = answer.claims[0]
    assert claim.mode == "B"
    cit = claim.citations[0]

    assert cit.source_file == PESKAS_SOFTWAREX               # the join key (#4)
    assert cit.location == "page 2 [part 1/2]"               # the span
    assert "outlier detection" in cit.quote                  # the verbatim quote
    assert "peskas_validation_engine" in cit.nodes           # the matching graph node(s)
    assert cit.note.endswith("_context.md")                  # companion-note pointer (§6)

    # the dual payload: associations for the cited nodes
    assert answer.associations
    assert any(e.get("target") == "peskas_hub" for e in answer.associations)


def test_uncited_synthesis_falls_back_to_all_passages(graph, wdb_root):
    nodes, links = graph
    # synthesis with no [k] markers -> every passage is cited (still grounded)
    answer = assemble("q", [_passage()], "An answer with no bracket citations.",
                      nodes, links, wdb_root)
    assert answer.answered
    assert len(answer.claims[0].citations) == 1


def test_refusal_shape_states_the_question():
    answer = refusal("Impossible question?", "not available: no passage retrieved")
    assert not answer.answered
    assert answer.claims == []
    assert answer.unanswered and "Impossible question?" in answer.unanswered[0]
